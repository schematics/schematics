# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import encodings.idna
import random
import re

try: # PY3
    from urllib.request import urlopen
    from urllib.parse import urlunsplit, quote as urlquote
    from urllib.error import URLError
except ImportError: # PY2
    from urllib2 import urlopen, URLError
    from urlparse import urlunsplit
    from urllib import quote as urlquote

from ..common import * # pylint: disable=redefined-builtin
from ..exceptions import ValidationError, StopValidationError

from .base import StringType, fill_template


### Character ranges

HEX      = '0-9A-F'
ALPHA    = 'A-Z'
ALPHANUM = 'A-Z0-9'


### IP address patterns

IPV4_OCTET = '( 25[0-5] | 2[0-4][0-9] | [0-1]?[0-9]{1,2} )'
IPV4 = r'( ((%(oct)s\.){3} %(oct)s) )' % {'oct': IPV4_OCTET}

IPV6_H16 = '[%s]{1,4}' % HEX
IPV6_L32 = '(%(h16)s:%(h16)s|%(ipv4)s)' % {'h16': IPV6_H16, 'ipv4': IPV4}
IPV6 = r"""(
                                    (%(h16)s:){6}%(l32)s  |
                                ::  (%(h16)s:){5}%(l32)s  |
    (               %(h16)s )?  ::  (%(h16)s:){4}%(l32)s  |
    ( (%(h16)s:){,1}%(h16)s )?  ::  (%(h16)s:){3}%(l32)s  |
    ( (%(h16)s:){,2}%(h16)s )?  ::  (%(h16)s:){2}%(l32)s  |
    ( (%(h16)s:){,3}%(h16)s )?  ::  (%(h16)s:){1}%(l32)s  |
    ( (%(h16)s:){,4}%(h16)s )?  ::               %(l32)s  |
    ( (%(h16)s:){,5}%(h16)s )?  ::               %(h16)s  |
    ( (%(h16)s:){,6}%(h16)s )?  :: )""" % {'h16': IPV6_H16,
                                           'l32': IPV6_L32}


class IPAddressType(StringType):

    VERSION = None
    REGEX = re.compile('^%s|%s$' % (IPV4, IPV6), re.I + re.X)

    @classmethod
    def valid_ip(cls, value):
        return bool(cls.REGEX.match(value))

    def validate_(self, value, context=None):
        if not self.valid_ip(value):
            raise ValidationError('Invalid IP%s address' % (self.VERSION or ''))


class IPv4Type(IPAddressType):
    """A field that stores a valid IPv4 address."""

    VERSION = 'v4'
    REGEX = re.compile('^%s$' % IPV4, re.I + re.X)

    def _mock(self, context=None):
        return '.'.join(str(random.randrange(256)) for _ in range(4))


class IPv6Type(IPAddressType):
    """A field that stores a valid IPv6 address."""

    VERSION = 'v6'
    REGEX = re.compile('^%s$' % IPV6, re.I + re.X)

    def _mock(self, context=None):
        return '.'.join(str(random.randrange(256)) for _ in range(4))


### URI patterns

GEN_DELIMS = set(':/?#[]@')
SUB_DELIMS = set('!$&\'()*+,;=')
UNRESERVED = set('-_.~')
PCHAR = SUB_DELIMS | UNRESERVED | set('%:@')
QUERY_EXTRAS = set('[]') # nonstandard

VALID_CHARS = GEN_DELIMS | SUB_DELIMS | UNRESERVED | set('%')
VALID_CHAR_STRING = py_native_string(str.join('', VALID_CHARS))
UNSAFE_CHAR_STRING = '\x00-\x20<>{}|"`\\^\x7F-\x9F'

def _chrcls(allowed_chars):
    """
    Given a subset of the URL-compatible special characters ``!#$%&'()*+,-./:;=?@[]_~``,
    returns a regex character class matching any URL-compatible character apart from the
    special characters not present in the provided set.
    """
    return ('^'
            + UNSAFE_CHAR_STRING
            + str.join('', VALID_CHARS - allowed_chars).replace('%', '%%')
                                                       .replace(']', r'\]')
                                                       .replace('-', r'\-'))

URI_PATTERNS = {
    'scheme' : r'[%s]+' % ('A-Z0-9.+-'),
    'user'   : r'[%s]+' % _chrcls(UNRESERVED | SUB_DELIMS | set('%:')),
    'port'   : r'[0-9]{2,5}',
    'host4'  : IPV4,
    'host6'  : r'[%s]+' % (HEX + ':'),
    'hostn'  : r'[%s]+' % _chrcls(set('.-')),
    'path'   : r'[%s]*' % _chrcls(PCHAR | set('/')),
    'query'  : r'[%s]*' % _chrcls(PCHAR | set('/?') | QUERY_EXTRAS),
    'frag'   : r'[%s]*' % _chrcls(PCHAR | set('/?')),
}


class URLType(StringType):

    """A field that validates the input as a URL.

    If ``verify_exists=True``, the validation function will make sure
    the URL is accessible (server responds with HTTP 2xx).
    """

    MESSAGES = {
        'invalid_url': "Not a well-formed URL.",
        'not_found': "URL could not be retrieved.",
    }

    URL_REGEX = re.compile(r"""^(
            (?P<scheme> %(scheme)s ) ://
        (   (?P<user>   %(user)s   ) @   )?
        (\[ (?P<host6>  %(host6)s  ) ]
          | (?P<host4>  %(host4)s  )
          | (?P<hostn>  %(hostn)s  )     )
        ( : (?P<port>   %(port)s   )     )?
            (?P<path> / %(path)s   )?
        (\? (?P<query>  %(query)s  )     )?
        (\# (?P<frag>   %(frag)s   )     )?)$
        """ % URI_PATTERNS, re.I + re.X)

    TLD_REGEX = re.compile(r'^( ([a-z]{2,}) | (xn--[a-z0-9]{4,}) )$', re.I + re.X)

    def __init__(self, fqdn=True, verify_exists=False, **kwargs):
        self.schemes = ['http', 'https']
        self.fqdn = fqdn
        self.verify_exists = verify_exists
        super(URLType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return fill_template('http://a%s.ZZ', self.min_length, self.max_length)

    def valid_url(self, value):
        match = self.URL_REGEX.match(value)
        if not match:
            return False
        url = match.groupdict()

        if url['scheme'].lower() not in self.schemes:
            return False
        if url['host6']:
            if IPv6Type.valid_ip(url['host6']):
                return url
            else:
                return False
        if url['host4']:
            return url

        try:
            hostname = url['hostn'].encode('ascii').decode('ascii')
        except UnicodeError:
            try:
                hostname = url['hostn'].encode('idna').decode('ascii')
            except UnicodeError:
                return False

        if hostname[-1] == '.':
            hostname = hostname[:-1]
        if len(hostname) > 253:
            return False

        labels = hostname.split('.')
        for label in labels:
            if not 0 < len(label) < 64:
                return False
            if '-' in (label[0], label[-1]):
                return False
        if self.fqdn:
            if len(labels) == 1 \
              or not self.TLD_REGEX.match(labels[-1]):
                return False

        url['hostn_enc'] = hostname

        return url

    def validate_(self, value, context=None):
        url = self.valid_url(value)
        if not url:
            raise StopValidationError(self.messages['invalid_url'])
        if self.verify_exists:
            url_string = urlquote(urlunsplit((
                url['scheme'],
                (url['host6'] or url['host4'] or url['hostn_enc']) + ':' + (url['port'] or ''),
                url['path'],
                url['query'],
                url['frag'])
                ).encode('utf-8'), safe=VALID_CHAR_STRING)
            try:
                urlopen(url_string)
            except URLError:
                raise StopValidationError(self.messages['not_found'])


class EmailType(StringType):

    """A field that validates input as an E-Mail-Address.
    """

    MESSAGES = {
        'email': "Not a well-formed email address."
    }

    EMAIL_REGEX = re.compile(r"""^(
        ( ( [%(atext)s]+ (\.[%(atext)s]+)* ) | ("( [%(qtext)s\s] | \\[%(vchar)s\s] )*") )
        @((?!-)[A-Z0-9-]{1,63}(?<!-)\.)+[A-Z]{2,63})$"""
        % {
            'atext': '-A-Z0-9!#$%&\'*+/=?^_`{|}~',
            'qtext': '\x21\x23-\x5B\\\x5D-\x7E',
            'vchar': '\x21-\x7E'
        },
        re.I + re.X)

    def _mock(self, context=None):
        return fill_template('%s@example.com', self.min_length,
                             self.max_length)

    def validate_email(self, value, context=None):
        if not EmailType.EMAIL_REGEX.match(value):
            raise StopValidationError(self.messages['email'])


__all__ = module_exports(__name__)

