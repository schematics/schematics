import uuid
import re
import datetime
import decimal
import itertools
import functools
import random
import string

import six
from six import iteritems

from ..exceptions import (
    StopValidation, ValidationError, ConversionError, MockCreationError
)

try:
    from string import ascii_letters # PY3
except ImportError:
    from string import letters as ascii_letters #PY2

try:
    basestring #PY2
except NameError:
    basestring = str #PY3

try:
    unicode #PY2
except:
    import codecs
    unicode = str #PY3

def utf8_decode(s):

    if six.PY3:
        s = str(s) #todo: right thing to do?
    else:
        s = unicode(s, 'utf-8')

    return s

def fill_template(template, min_length, max_length):
    return template % random_string(
        get_value_in(
            min_length,
            max_length,
            padding=len(template) - 2,
            required_length=1))


def force_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            #obj = unicode(obj, encoding)
            obj = utf8_decode(obj)
    elif not obj is None:
        #obj = unicode(obj)
        obj = utf8_decode(obj)

    return obj


def get_range_endpoints(min_length, max_length, padding=0, required_length=0):
    if min_length is None and max_length is None:
        min_length = 0
        max_length = 16
    elif min_length is None:
        min_length = 0
    elif max_length is None:
        max_length = max(min_length * 2, 16)

    if padding:
        max_length = max_length - padding
        min_length = max(min_length - padding, 0)

    if max_length < required_length:
        raise MockCreationError(
            'This field is too short to hold the mock data')

    min_length = max(min_length, required_length)

    return min_length, max_length


def get_value_in(min_length, max_length, padding=0, required_length=0):
    return random.randint(
        *get_range_endpoints(min_length, max_length, padding, required_length))


def random_string(length, chars=ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))


_last_position_hint = -1
_next_position_hint = itertools.count()


class TypeMeta(type):

    """
    Meta class for BaseType. Merges `MESSAGES` dict and accumulates
    validator methods.
    """

    def __new__(mcs, name, bases, attrs):
        messages = {}
        validators = []

        for base in reversed(bases):
            if hasattr(base, 'MESSAGES'):
                messages.update(base.MESSAGES)

            if hasattr(base, "_validators"):
                validators.extend(base._validators)

        if 'MESSAGES' in attrs:
            messages.update(attrs['MESSAGES'])

        attrs['MESSAGES'] = messages

        for attr_name, attr in iteritems(attrs):
            if attr_name.startswith("validate_"):
                validators.append(attr)

        attrs["_validators"] = validators

        return type.__new__(mcs, name, bases, attrs)


class BaseType(TypeMeta('BaseTypeBase', (object, ), {})):

    """A base class for Types in a Schematics model. Instances of this
    class may be added to subclasses of ``Model`` to define a model schema.

    Validators that need to access variables on the instance
    can be defined be implementing methods whose names start with ``validate_``
    and accept one parameter (in addition to ``self``)

    :param required:
        Invalidate field when value is None or is not supplied. Default:
        False.
    :param default:
        When no data is provided default to this value. May be a callable.
        Default: None.
    :param serialized_name:
        The name of this field defaults to the class attribute used in the
        model. However if the field has another name in foreign data set this
        argument. Serialized data will use this value for the key name too.
    :param deserialize_from:
        A name or list of named fields for which foreign data sets are
        searched to provide a value for the given field.  This only effects
        inbound data.
    :param choices:
        A list of valid choices. This is the last step of the validator
        chain.
    :param validators:
        A list of callables. Each callable receives the value after it has been
        converted into a rich python type. Default: []
    :param serialize_when_none:
        Dictates if the field should appear in the serialized data even if the
        value is None. Default: True
    :param messages:
        Override the error messages with a dict. You can also do this by
        subclassing the Type and defining a `MESSAGES` dict attribute on the
        class. A metaclass will merge all the `MESSAGES` and override the
        resulting dict with instance level `messages` and assign to
        `self.messages`.

    """

    MESSAGES = {
        'required': u"This field is required.",
        'choices': u"Value must be one of {0}.",
    }

    def __init__(self, required=False, default=None, serialized_name=None,
                 choices=None, validators=None, deserialize_from=None,
                 serialize_when_none=None, messages=None):
        super(BaseType, self).__init__()
        self.required = required
        self._default = default
        self.serialized_name = serialized_name
        if choices and not isinstance(choices, (list, tuple)):
            raise TypeError('"choices" must be a list or tuple')
        self.choices = choices
        self.deserialize_from = deserialize_from

        self.validators = [functools.partial(v, self) for v in self._validators]
        if validators:
            self.validators += validators

        self.serialize_when_none = serialize_when_none
        self.messages = dict(self.MESSAGES, **(messages or {}))
        self._position_hint = next(_next_position_hint)  # For ordering of fields

    def __call__(self, value):
        return self.to_native(value)

    def _mock(self, context=None):
        return None

    @property
    def default(self):
        default = self._default
        if callable(self._default):
            default = self._default()
        return default

    def to_primitive(self, value, context=None):
        """Convert internal data to a value safe to serialize.
        """
        return value

    def to_native(self, value, context=None):
        """
        Convert untrusted data to a richer Python construct.
        """
        return value

    def allow_none(self):
        if hasattr(self, 'owner_model'):
            return self.owner_model.allow_none(self)
        else:
            return self.serialize_when_none

    def validate(self, value):
        """
        Validate the field and return a clean value or raise a
        ``ValidationError`` with a list of errors raised by the validation
        chain. Stop the validation process from continuing through the
        validators by raising ``StopValidation`` instead of ``ValidationError``.

        """

        errors = []

        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as exc:
                errors.extend(exc.messages)

                if isinstance(exc, StopValidation):
                    break

        if errors:
            raise ValidationError(errors)

    def validate_required(self, value):
        if self.required and value is None:
            raise ValidationError(self.messages['required'])

    def validate_choices(self, value):
        if self.choices is not None:
            if value not in self.choices:
                raise ValidationError(self.messages['choices']
                                      .format(unicode(self.choices)))

    def mock(self, context=None):
        if not self.required and not random.choice([True, False]):
            return self.default
        if self.choices is not None:
            return random.choice(self.choices)
        return self._mock(context)


class UUIDType(BaseType):

    """A field that stores a valid UUID value.
    """
    MESSAGES = {
        'convert': u"Couldn't interpret '{0}' value as UUID.",
    }

    def _mock(self, context=None):
        return uuid.uuid4()

    def to_native(self, value, context=None):
        if not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)
            except (AttributeError, TypeError, ValueError):
                raise ConversionError(self.messages['convert'].format(value))
        return value

    def to_primitive(self, value, context=None):
        return str(value)


class IPv4Type(BaseType):

    """ A field that stores a valid IPv4 address """

    def _mock(self, context=None):
        return '.'.join(str(random.randrange(256)) for _ in range(4))

    @classmethod
    def valid_ip(cls, addr):
        try:
            addr = addr.strip().split(".")
        except AttributeError:
            return False
        try:
            return len(addr) == 4 and all(0 <= int(octet) < 256 for octet in addr)
        except ValueError:
            return False

    def validate(self, value):
        """
          Make sure the value is a IPv4 address:
          http://stackoverflow.com/questions/9948833/validate-ip-address-from-list
        """
        if not IPv4Type.valid_ip(value):
            error_msg = 'Invalid IPv4 address'
            raise ValidationError(error_msg)
        return True


class StringType(BaseType):

    """A unicode string field. Default minimum length is one. If you want to
    accept empty strings, init with ``min_length`` 0.
    """

    allow_casts = (int, str)

    MESSAGES = {
        'convert': u"Couldn't interpret '{0}' as string.",
        'max_length': u"String value is too long.",
        'min_length': u"String value is too short.",
        'regex': u"String value did not match validation regex.",
    }

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = regex
        self.max_length = max_length
        self.min_length = min_length

        super(StringType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return random_string(get_value_in(self.min_length, self.max_length))

    def to_native(self, value, context=None):
        if value is None:
            return None

        if not isinstance(value, unicode):
            if isinstance(value, self.allow_casts):
                if not isinstance(value, str):
                    value = str(value)
                value = utf8_decode(value) #unicode(value, 'utf-8')
            else:
                raise ConversionError(self.messages['convert'].format(value))

        return value

    def validate_length(self, value):
        len_of_value = len(value) if value else 0

        if self.max_length is not None and len_of_value > self.max_length:
            raise ValidationError(self.messages['max_length'])

        if self.min_length is not None and len_of_value < self.min_length:
            raise ValidationError(self.messages['min_length'])

    def validate_regex(self, value):
        if self.regex is not None and re.match(self.regex, value) is None:
            raise ValidationError(self.messages['regex'])


class URLType(StringType):

    """A field that validates input as an URL.

    If verify_exists=True is passed the validate function will make sure
    the URL makes a valid connection.
    """

    MESSAGES = {
        'invalid_url': u"Not a well formed URL.",
        'not_found': u"URL does not exist.",
    }

    URL_REGEX = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,2000}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    def __init__(self, verify_exists=False, **kwargs):
        self.verify_exists = verify_exists
        super(URLType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return fill_template('http://a%s.ZZ', self.min_length,
                             self.max_length)

    def validate_url(self, value):
        if not URLType.URL_REGEX.match(value):
            raise StopValidation(self.messages['invalid_url'])
        if self.verify_exists:
            from six.moves import urllib
            try:
                request = urllib.Request(value)
                urllib.urlopen(request)
            except Exception:
                raise StopValidation(self.messages['not_found'])


class EmailType(StringType):

    """A field that validates input as an E-Mail-Address.
    """

    MESSAGES = {
        'email': u"Not a well formed email address."
    }

    EMAIL_REGEX = re.compile(
        # dot-atom
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016'
        r'-\177])*"'
        # domain
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,2000}[A-Z0-9])?\.)+[A-Z]{2,63}\.?$',
        re.IGNORECASE
    )

    def _mock(self, context=None):
        return fill_template('%s@example.com', self.min_length,
                             self.max_length)

    def validate_email(self, value):
        if not EmailType.EMAIL_REGEX.match(value):
            raise StopValidation(self.messages['email'])


class NumberType(BaseType):

    """A number field.
    """

    MESSAGES = {
        'number_coerce': u"Value '{0}' is not {1}.",
        'number_min': u"{0} value should be greater than {1}.",
        'number_max': u"{0} value should be less than {1}.",
    }

    def __init__(self, number_class, number_type,
                 min_value=None, max_value=None, **kwargs):
        self.number_class = number_class
        self.number_type = number_type
        self.min_value = min_value
        self.max_value = max_value

        super(NumberType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return get_value_in(self.min_value, self.max_value)

    def to_native(self, value, context=None):
        try:
            value = self.number_class(value)
        except (TypeError, ValueError):
            raise ConversionError(self.messages['number_coerce']
                                  .format(value, self.number_type.lower()))

        return value

    def validate_is_a_number(self, value):
        try:
            self.number_class(value)
        except (TypeError, ValueError):
            raise ConversionError(self.messages['number_coerce']
                                  .format(value, self.number_type.lower()))

    def validate_range(self, value):
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(self.messages['number_min']
                                  .format(self.number_type, self.min_value))

        if self.max_value is not None and value > self.max_value:
            raise ValidationError(self.messages['number_max']
                                  .format(self.number_type, self.max_value))

        return value


class IntType(NumberType):

    """A field that validates input as an Integer
    """

    def __init__(self, *args, **kwargs):
        super(IntType, self).__init__(number_class=int,
                                      number_type='Int',
                                      *args, **kwargs)


class LongType(NumberType):

    """A field that validates input as a Long
    """

    def __init__(self, *args, **kwargs):

        try:
            number_class = long #PY2
        except NameError:
            number_class = int #PY3


        super(LongType, self).__init__(number_class=number_class,
                                       number_type='Long',
                                       *args, **kwargs)


class FloatType(NumberType):

    """A field that validates input as a Float
    """

    def __init__(self, *args, **kwargs):
        super(FloatType, self).__init__(number_class=float,
                                        number_type='Float',
                                        *args, **kwargs)


class DecimalType(BaseType):

    """A fixed-point decimal number field.
    """

    MESSAGES = {
        'number_coerce': u"Number '{0}' failed to convert to a decimal.",
        'number_min': u"Value should be greater than {0}.",
        'number_max': u"Value should be less than {0}.",
    }

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value

        super(DecimalType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return get_value_in(self.min_value, self.max_value)

    def to_primitive(self, value, context=None):
        return unicode(value)

    def to_native(self, value, context=None):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, basestring):
                value = unicode(value)
            try:
                value = decimal.Decimal(value)
            except (TypeError, decimal.InvalidOperation):
                raise ConversionError(self.messages['number_coerce'].format(value))

        return value

    def validate_range(self, value):
        if self.min_value is not None and value < self.min_value:
            error_msg = self.messages['number_min'].format(self.min_value)
            raise ValidationError(error_msg)

        if self.max_value is not None and value > self.max_value:
            error_msg = self.messages['number_max'].format(self.max_value)
            raise ValidationError(error_msg)

        return value


class HashType(BaseType):

    MESSAGES = {
        'hash_length': u"Hash value is wrong length.",
        'hash_hex': u"Hash value is not hexadecimal.",
    }

    def _mock(self, context=None):
        return random_string(self.LENGTH, string.hexdigits)

    def to_native(self, value, context=None):
        if len(value) != self.LENGTH:
            raise ValidationError(self.messages['hash_length'])
        try:
            int(value, 16)
        except ValueError:
            raise ConversionError(self.messages['hash_hex'])
        return value


class MD5Type(HashType):

    """A field that validates input as resembling an MD5 hash.
    """

    LENGTH = 32


class SHA1Type(HashType):

    """A field that validates input as resembling an SHA1 hash.
    """

    LENGTH = 40


class BooleanType(BaseType):

    """A boolean field type. In addition to ``True`` and ``False``, coerces these
    values:

    + For ``True``: "True", "true", "1"
    + For ``False``: "False", "false", "0"

    """

    TRUE_VALUES = ('True', 'true', '1')
    FALSE_VALUES = ('False', 'false', '0')

    def _mock(self, context=None):
        return random.choice([True, False])

    def to_native(self, value, context=None):
        if isinstance(value, basestring):
            if value in self.TRUE_VALUES:
                value = True
            elif value in self.FALSE_VALUES:
                value = False

        if isinstance(value, int) and value in [0, 1]:
            value = bool(value)

        if not isinstance(value, bool):
            raise ConversionError(u"Must be either true or false.")

        return value


class DateType(BaseType):

    """Defaults to converting to and from ISO8601 date values.
    """

    SERIALIZED_FORMAT = '%Y-%m-%d'
    MESSAGES = {
        'parse': u"Could not parse {0}. Should be ISO8601 (YYYY-MM-DD).",
    }

    def __init__(self, **kwargs):
        self.serialized_format = self.SERIALIZED_FORMAT
        super(DateType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return datetime.datetime(
            year=random.randrange(600) + 1900,
            month=random.randrange(12) + 1,
            day=random.randrange(28) + 1,
        )

    def to_native(self, value, context=None):
        if isinstance(value, datetime.date):
            return value

        try:
            return datetime.datetime.strptime(value, self.serialized_format).date()
        except (ValueError, TypeError):
            raise ConversionError(self.messages['parse'].format(value))

    def to_primitive(self, value, context=None):
        return value.strftime(self.serialized_format)


class DateTimeType(BaseType):

    """Defaults to converting to and from ISO8601 datetime values.

    :param formats:
        A value or list of values suitable for ``datetime.datetime.strptime``
        parsing. Default: `('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ')`
    :param serialized_format:
        The output format suitable for Python ``strftime``. Default: ``'%Y-%m-%dT%H:%M:%S.%f'``

    """

    DEFAULT_FORMATS = (
        '%Y-%m-%dT%H:%M:%S.%f',  '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ',
    )
    SERIALIZED_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    MESSAGES = {
        'parse_formats': u'Could not parse {0}. Valid formats: {1}',
        'parse': u"Could not parse {0}. Should be ISO8601.",
    }

    def __init__(self, formats=None, serialized_format=None, **kwargs):
        """

        """
        if isinstance(formats, basestring):
            formats = [formats]
        if formats is None:
            formats = self.DEFAULT_FORMATS
        if serialized_format is None:
            serialized_format = self.SERIALIZED_FORMAT
        self.formats = formats
        self.serialized_format = serialized_format
        super(DateTimeType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return datetime.datetime(
            year=random.randrange(600) + 1900,
            month=random.randrange(12) + 1,
            day=random.randrange(28) + 1,
            hour=random.randrange(24),
            minute=random.randrange(60),
            second=random.randrange(60),
            microsecond=random.randrange(1000000),
        )

    def to_native(self, value, context=None):
        if isinstance(value, datetime.datetime):
            return value

        for fmt in self.formats:
            try:
                return datetime.datetime.strptime(value, fmt)
            except (ValueError, TypeError):
                continue
        if self.formats == self.DEFAULT_FORMATS:
            message = self.messages['parse'].format(value)
        else:
            message = self.messages['parse_formats'].format(
                value, ", ".join(self.formats)
            )
        raise ConversionError(message)

    def to_primitive(self, value, context=None):
        if callable(self.serialized_format):
            return self.serialized_format(value)
        return value.strftime(self.serialized_format)


class GeoPointType(BaseType):

    """A list storing a latitude and longitude.
    """

    def _mock(self, context=None):
        return (random.randrange(-90, 90), random.randrange(-90, 90))

    def to_native(self, value, context=None):
        """Make sure that a geo-value is of type (x, y)
        """
        if not len(value) == 2:
            raise ValueError('Value must be a two-dimensional point')
        if isinstance(value, dict):
            for val in value.values():
                if not isinstance(val, (float, int)):
                    raise ValueError('Both values in point must be float or int')
        elif isinstance(value, (list, tuple)):
            if (not isinstance(value[0], (float, int)) or
                    not isinstance(value[1], (float, int))):
                raise ValueError('Both values in point must be float or int')
        else:
            raise ValueError('GeoPointType can only accept tuples, lists, or dicts')

        return value


class MultilingualStringType(BaseType):

    """
    A multilanguage string field, stored as a dict with {'locale': 'localized_value'}.

    Minimum and maximum lengths apply to each of the localized values.

    At least one of ``default_locale`` or ``context['locale']`` must be defined
    when calling ``.to_primitive``.

    """

    allow_casts = (int, str)

    MESSAGES = {
        'convert': u"Couldn't interpret value as string.",
        'max_length': u"String value in locale {0} is too long.",
        'min_length': u"String value in locale {0} is too short.",
        'locale_not_found': u"No requested locale was available.",
        'no_locale': u"No default or explicit locales were given.",
        'regex_locale': u"Name of locale {0} did not match validation regex.",
        'regex_localized': u"String value in locale {0} did not match validation regex.",
    }

    LOCALE_REGEX = r'^[a-z]{2}(:?_[A-Z]{2})?$'

    def __init__(self, regex=None, max_length=None, min_length=None,
                 default_locale=None, locale_regex=LOCALE_REGEX, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        self.default_locale = default_locale
        self.locale_regex = re.compile(locale_regex) if locale_regex else None

        super(MultilingualStringType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return random_string(get_value_in(self.min_length, self.max_length))

    def to_native(self, value, context=None):
        """Make sure a MultilingualStringType value is a dict or None."""

        if not (value is None or isinstance(value, dict)):
            raise ValueError('Value must be a dict or None')

        return value

    def to_primitive(self, value, context=None):
        """
        Use a combination of ``default_locale`` and ``context['locale']`` to return
        the best localized string.

        """
        if value is None:
            return None

        context_locale = None
        if context is not None and 'locale' in context:
            context_locale = context['locale']

        # Build a list of all possible locales to try
        possible_locales = []
        for locale in (context_locale, self.default_locale):
            if not locale:
                continue

            if isinstance(locale, basestring):
                possible_locales.append(locale)
            else:
                possible_locales.extend(locale)

        if not possible_locales:
            raise ConversionError(self.messages['no_locale'])

        for locale in possible_locales:
            if locale in value:
                localized = value[locale]
                break
        else:
            raise ConversionError(self.messages['locale_not_found'])

        if not isinstance(localized, unicode):
            if isinstance(localized, self.allow_casts):
                if not isinstance(localized, str):
                    localized = str(localized)
                #localized = unicode(localized, 'utf-8')
                localized = utf8_decode(localized)
            else:
                raise ConversionError(self.messages['convert'])

        return localized

    def validate_length(self, value):
        for locale, localized in value.items():
            len_of_value = len(localized) if localized else 0

            if self.max_length is not None and len_of_value > self.max_length:
                raise ValidationError(self.messages['max_length'].format(locale))

            if self.min_length is not None and len_of_value < self.min_length:
                raise ValidationError(self.messages['min_length'].format(locale))

    def validate_regex(self, value):
        if self.regex is None and self.locale_regex is None:
            return

        for locale, localized in value.items():
            if self.regex is not None and self.regex.match(localized) is None:
                raise ValidationError(
                    self.messages['regex_localized'].format(locale))

            if self.locale_regex is not None and self.locale_regex.match(locale) is None:
                raise ValidationError(
                    self.messages['regex_locale'].format(locale))
