# -*- coding: utf-8 -*-

from __future__ import print_function

from encodings import idna
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

from ..common import *
from ..exceptions import ConversionError, ValidationError, StopValidationError
from ..util import listify
from .base import StringType

try:
    basestring #PY2
    bytes = str
except NameError:
    basestring = str #PY3
    unicode = str


### Character ranges

hex      = '0-9A-F'
alpha    = 'A-Z'
alphanum = 'A-Z0-9'
ucs      = (u'\u00A0-\uD7FF'
            u'\uF900-\uFDCF'
            u'\uFDF0-\uFFEF')
private  =  u'\uE000-\uF8FF'

if len(u'\U0002000B') == 1: # Indicates that code points beyond the BMP are supported.
    ucs     += u'\U00010000-\U000EFFFF'
    private += u'\U000F0000-\U0010FFFD'


### IP address patterns

ipv4_octet = '( 25[0-5] | 2[0-4][0-9] | [0-1]?[0-9]{1,2} )'
ipv4 = '( ((%(oct)s\.){3} %(oct)s) )' % {'oct': ipv4_octet}

ipv6_h16 = '[%s]{1,4}' % hex
ipv6_l32 = '(%(h16)s:%(h16)s|%(ipv4)s)' % {'h16': ipv6_h16, 'ipv4': ipv4}
ipv6 = u"""(
                                    (%(h16)s:){6}%(l32)s  |
                                ::  (%(h16)s:){5}%(l32)s  |
    (               %(h16)s )?  ::  (%(h16)s:){4}%(l32)s  |
    ( (%(h16)s:){,1}%(h16)s )?  ::  (%(h16)s:){3}%(l32)s  |
    ( (%(h16)s:){,2}%(h16)s )?  ::  (%(h16)s:){2}%(l32)s  |
    ( (%(h16)s:){,3}%(h16)s )?  ::  (%(h16)s:){1}%(l32)s  |
    ( (%(h16)s:){,4}%(h16)s )?  ::               %(l32)s  |
    ( (%(h16)s:){,5}%(h16)s )?  ::               %(h16)s  |
    ( (%(h16)s:){,6}%(h16)s )?  :: )""" % {'h16': ipv6_h16,
                                           'l32': ipv6_l32}


class IPAddressType(StringType):

    VERSION = None
    REGEX = re.compile('^%s|%s$' % (ipv4, ipv6), re.I + re.X)

    @classmethod
    def valid_ip(cls, value):
        return bool(cls.REGEX.match(value))

    def validate_(self, value, context=None):
        if not self.valid_ip(value):
            raise ValidationError('Invalid IP%s address' % (self.VERSION or ''))


class IPv4Type(IPAddressType):
    """A field that stores a valid IPv4 address."""

    VERSION = 'v4'
    REGEX = re.compile('^%s$' % ipv4, re.I + re.X)

    def _mock(self, context=None):
        return '.'.join(str(random.randrange(256)) for _ in range(4))


class IPv6Type(IPAddressType):
    """A field that stores a valid IPv6 address."""

    VERSION = 'v6'
    REGEX = re.compile('^%s$' % ipv6, re.I + re.X)

    def _mock(self, context=None):
        return '.'.join(str(random.randrange(256)) for _ in range(4))


### URI patterns

sub_delims = '!$&\'()*+,;='
unreserved  = '-_.~' + alphanum + ucs
pchar = unreserved + sub_delims + '%%:@'
query_extras = '\[\]' # nonstandard

uri_patterns = {
    'scheme' : '[%s]+' % ('-.+' + alphanum),
    'user'   : '[%s]+' % (unreserved + sub_delims + '%%:'),
    'port'   : '\d{2,5}',
    'host'   : '[%s]+' % (unreserved + sub_delims + '%%:\[\]'),
    'host6'  : '[%s]+' % (hex + ':'),
    'host4'  :  ipv4,
    'hostn'  : '[%s]+' % (alphanum + ucs + '.-'),
    'path'   : '(/[%s]*)*' % pchar,
    'query'  : '[%s]*' % (pchar + '/?' + private + query_extras),
    'frag'   : '[%s]*' % (pchar + '/?'),
}


class URLType(StringType):

    """A field that validates the input as a URL.

    If ``verify_exists=True``, the validation function will make sure
    the URL is accessible (server responds with HTTP 2xx).
    """

    MESSAGES = {
        'invalid_url': u"Not a well-formed URL.",
        'not_found': u"URL could not be retrieved.",
    }

    URL_REGEX = re.compile(r"""^(
            (?P<scheme> %(scheme)s ) ://
        (   (?P<user>   %(user)s   ) @   )?
        (   (?P<host6>\[%(host6)s] ) 
          | (?P<host4>  %(host4)s  )
          | (?P<hostn>  %(hostn)s  )     )
        ( : (?P<port>   %(port)s   )     )?
            (?P<path>   %(path)s   )
        (\? (?P<query>  %(query)s  )     )?
        (\# (?P<frag>   %(frag)s   )     )?)$
        """ % uri_patterns, re.I + re.X)

    TLD_REGEX = re.compile('^( ([a-z]{2,}) | (xn--[a-z0-9]{4,}) )$', re.I + re.X)

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
            if IPv6Type.valid_ip(url['host6'][1:-1]):
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
                ).encode('utf-8'), safe='%~:/?#[]@'+sub_delims)
            try:
                urlopen(url_string)
            except URLError:
                raise StopValidationError(self.messages['not_found'])


### Email patterns

atext = 'A-Z0-9!#$%&\'*+-/=?^_`{|}~'
qtext = '!#-\[\]-~\s'


class EmailType(StringType):

    """A field that validates input as an E-Mail-Address.
    """

    MESSAGES = {
        'email': u"Not a well-formed email address."
    }

    EMAIL_REGEX = re.compile(r"""^(
        (
          (      [%(a)s]+ (\.[%(a)s]+)*      )  |  # dot-atom
          ( "(   [%(q)s] | \\[!-~\s]     )*" )     # quoted-string
        )
        @((?!-)[A-Z0-9-]{1,63}(?<!-)\.)+[A-Z]{2,63})$""" % {'a': atext, 'q': qtext}, re.I + re.X)

    def _mock(self, context=None):
        return fill_template('%s@example.com', self.min_length,
                             self.max_length)

    def validate_email(self, value, context=None):
        if not EmailType.EMAIL_REGEX.match(value):
            raise StopValidationError(self.messages['email'])

