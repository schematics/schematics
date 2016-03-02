# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import copy
import datetime
import decimal
import itertools
import numbers
import random
import re
import string
import uuid

from ..common import *  # pylint: disable=redefined-builtin
from ..exceptions import ConversionError, ValidationError, StopValidationError
from ..undefined import Undefined
from ..util import listify
from ..validate import prepare_validator, get_validation_context

MIMIMUM_TZ_HOUR_OFFSET = -12
MAXIMUM_TZ_HOUR_OFFSET = 12


def fill_template(template, min_length, max_length):
    return template % random_string(
        get_value_in(
            min_length,
            max_length,
            padding=len(template) - 2,
            required_length=1))


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


_alphanumeric = string.ascii_letters + string.digits

def random_string(length, chars=_alphanumeric):
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
        validators = set()

        for base in reversed(bases):
            if hasattr(base, 'MESSAGES'):
                messages.update(base.MESSAGES)

            if hasattr(base, "_validators"):
                validators.update(base._validators)

        if 'MESSAGES' in attrs:
            messages.update(attrs['MESSAGES'])

        attrs['MESSAGES'] = messages

        for attr_name, attr in attrs.items():
            if attr_name.startswith("validate_"):
                validators.add(attr_name)
                attrs[attr_name] = prepare_validator(attr, 3)

        attrs["_validators"] = validators

        return type.__new__(mcs, name, bases, attrs)


@metaclass(TypeMeta)
class BaseType(object):

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
        'required': "This field is required.",
        'choices': "Value must be one of {0}.",
    }

    EXPORT_METHODS = {
        NATIVE: 'to_native',
        PRIMITIVE: 'to_primitive',
    }

    def __init__(self, required=False, default=Undefined, serialized_name=None,
                 choices=None, validators=None, deserialize_from=None,
                 export_level=None, serialize_when_none=None,
                 messages=None, **kwargs):
        super(BaseType, self).__init__()

        self.required = required
        self._default = default
        self.serialized_name = serialized_name
        if choices and not isinstance(choices, (list, tuple)):
            raise TypeError('"choices" must be a list or tuple')
        self.choices = choices
        self.deserialize_from = listify(deserialize_from)

        self.validators = [getattr(self, validator_name) for validator_name in self._validators]
        if validators:
            self.validators += (prepare_validator(func, 2) for func in validators)

        self._set_export_level(export_level, serialize_when_none)

        self.messages = dict(self.MESSAGES, **(messages or {}))
        self._position_hint = next(_next_position_hint)  # For ordering of fields

        self.name = None
        self.owner_model = None
        self.parent_field = None
        self.typeclass = self.__class__
        self.is_compound = False

        self.export_mapping = dict(
            (format, getattr(self, fname)) for format, fname in self.EXPORT_METHODS.items())

    def __repr__(self):
        type_ = "%s(%s) instance" % (self.__class__.__name__, self._repr_info() or '')
        model = " on %s" % self.owner_model.__name__ if self.owner_model else ''
        field = " as '%s'" % self.name if self.name else ''
        return "<%s>" % (type_ + model + field)

    def _repr_info(self):
        return None

    def __call__(self, value, context=None):
        return self.convert(value, context)

    def __deepcopy__(self, memo):
        return copy.copy(self)

    def _mock(self, context=None):
        return None

    def _setup(self, field_name, owner_model):
        """Perform late-stage setup tasks that are run after the containing model
        has been created.
        """
        self.name = field_name
        self.owner_model = owner_model
        self._input_keys = self._get_input_keys()

    def _set_export_level(self, export_level, serialize_when_none):
        if export_level is not None:
            self.export_level = export_level
        elif serialize_when_none is True:
            self.export_level = DEFAULT
        elif serialize_when_none is False:
            self.export_level = NONEMPTY
        else:
            self.export_level = None

    def get_export_level(self, context):
        if self.owner_model:
            level = self.owner_model._options.export_level
        else:
            level = DEFAULT
        if self.export_level is not None:
            level = self.export_level
        if context.export_level is not None:
            level = context.export_level
        return level

    def get_input_keys(self, mapping=None):
        if mapping:
            return self._get_input_keys(mapping)
        else:
            return self._input_keys

    def _get_input_keys(self, mapping=None):
        input_keys = [self.name]
        if self.serialized_name:
            input_keys.append(self.serialized_name)
        if mapping and self.name in mapping:
            input_keys.extend(listify(mapping[self.name]))
        if self.deserialize_from:
            input_keys.extend(self.deserialize_from)
        return input_keys

    @property
    def default(self):
        default = self._default
        if callable(default):
            default = default()
        return default

    def pre_setattr(self, value):
        return value

    def convert(self, value, context=None):
        return self.to_native(value, context)

    def export(self, value, format, context=None):
        return self.export_mapping[format](value, context)

    def to_primitive(self, value, context=None):
        """Convert internal data to a value safe to serialize.
        """
        return value

    def to_native(self, value, context=None):
        """
        Convert untrusted data to a richer Python construct.
        """
        return value

    def validate(self, value, context=None):
        """
        Validate the field and return a converted value or raise a
        ``ValidationError`` with a list of errors raised by the validation
        chain. Stop the validation process from continuing through the
        validators by raising ``StopValidationError`` instead of ``ValidationError``.

        """
        context = context or get_validation_context()

        if context.convert:
            value = self.convert(value, context)
        elif self.is_compound:
            self.convert(value, context)

        errors = []
        for validator in self.validators:
            try:
                validator(value, context)
            except ValidationError as exc:
                errors.append(exc)
                if isinstance(exc, StopValidationError):
                    break
        if errors:
            raise ValidationError(errors)

        return value

    def check_required(self, value, context):
        if self.required and value in (None, Undefined):
            if self.name is None or context and not context.partial:
                raise ConversionError(self.messages['required'])

    def validate_choices(self, value, context):
        if self.choices is not None:
            if value not in self.choices:
                raise ValidationError(self.messages['choices']
                                      .format(str(self.choices)))

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
            except (TypeError, ValueError):
                raise ConversionError(self.messages['convert'].format(value))
        return value

    def to_primitive(self, value, context=None):
        return str(value)


class StringType(BaseType):

    """A Unicode string field."""

    allow_casts = (int, bytes)

    MESSAGES = {
        'convert': u"Couldn't interpret '{0}' as string.",
        'decode': u"Invalid UTF-8 data.",
        'max_length': u"String value is too long.",
        'min_length': u"String value is too short.",
        'regex': u"String value did not match validation regex.",
    }

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length

        super(StringType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return random_string(get_value_in(self.min_length, self.max_length))

    def to_native(self, value, context=None):
        if isinstance(value, str):
            return value
        if isinstance(value, self.allow_casts):
            if isinstance(value, bytes):
                try:
                    return str(value, 'utf-8')
                except UnicodeError:
                    raise ConversionError(self.messages['decode'].format(value))
            else:
                return str(value)
        raise ConversionError(self.messages['convert'].format(value))

    def validate_length(self, value, context=None):
        length = len(value)
        if self.max_length is not None and length > self.max_length:
            raise ValidationError(self.messages['max_length'])

        if self.min_length is not None and length < self.min_length:
            raise ValidationError(self.messages['min_length'])

    def validate_regex(self, value, context=None):
        if self.regex is not None and self.regex.match(value) is None:
            raise ValidationError(self.messages['regex'])


class NumberType(BaseType):

    """A number field.
    """

    MESSAGES = {
        'number_coerce': u"Value '{0}' is not {1}.",
        'number_min': u"{0} value should be greater than or equal to {1}.",
        'number_max': u"{0} value should be less than or equal to {1}.",
    }

    def __init__(self, number_class, number_type,
                 min_value=None, max_value=None, strict=False, **kwargs):
        self.number_class = number_class
        self.number_type = number_type
        self.min_value = min_value
        self.max_value = max_value
        self.strict = strict

        super(NumberType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return get_value_in(self.min_value, self.max_value)

    def to_native(self, value, context=None):
        if isinstance(value, self.number_class):
            return value
        try:
            native_value = self.number_class(value)
        except (TypeError, ValueError):
            pass
        else:
            if self.number_class is float: # Float conversion is strict enough.
                return native_value
            if not self.strict and native_value == value:  # Match numeric types.
                return native_value
            if isinstance(value, (string_type, numbers.Integral)):
                return native_value

        raise ConversionError(self.messages['number_coerce']
                              .format(value, self.number_type.lower()))

    def validate_range(self, value, context=None):
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
            number_class = long  # PY2
        except NameError:
            number_class = int  # PY3

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
        'number_min': u"Value should be greater than or equal to {0}.",
        'number_max': u"Value should be less than or equal to {0}.",
    }

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value

        super(DecimalType, self).__init__(**kwargs)

    def _mock(self, context=None):
        return get_value_in(self.min_value, self.max_value)

    def to_primitive(self, value, context=None):
        return str(value)

    def to_native(self, value, context=None):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, string_type):
                value = str(value)
            try:
                value = decimal.Decimal(value)
            except (TypeError, decimal.InvalidOperation):
                raise ConversionError(self.messages['number_coerce'].format(value))

        return value

    def validate_range(self, value, context=None):
        if self.min_value is not None and value < self.min_value:
            error_msg = self.messages['number_min'].format(self.min_value)
            raise ValidationError(error_msg)

        if self.max_value is not None and value > self.max_value:
            error_msg = self.messages['number_max'].format(self.max_value)
            raise ValidationError(error_msg)

        return value


class HashType(StringType):

    MESSAGES = {
        'hash_length': u"Hash value is wrong length.",
        'hash_hex': u"Hash value is not hexadecimal.",
    }

    def _mock(self, context=None):
        return random_string(self.LENGTH, string.hexdigits)

    def to_native(self, value, context=None):
        value = super(HashType, self).to_native(value, context)

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
        if isinstance(value, string_type):
            if value in self.TRUE_VALUES:
                value = True
            elif value in self.FALSE_VALUES:
                value = False

        elif isinstance(value, int) and value in [0, 1]:
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

    """A field that holds a combined date and time value.

    The built-in parser accepts input values conforming to the ISO 8601 format
    ``<YYYY>-<MM>-<DD>T<hh>:<mm>[:<ss.ssssss>][<z>]``. A space may be substituted
    for the delimiter ``T``. The time zone designator ``<z>`` may be either ``Z``
    or ``±<hh>[:][<mm>]``.

    Values are stored as standard ``datetime.datetime`` instances with the time zone
    offset in the ``tzinfo`` component if available. Raw values that do not specify a time
    zone will be converted to naive ``datetime`` objects unless ``tzd='utc'`` is in effect.

    Unix timestamps are also valid input values and will be converted to UTC datetimes.

    :param formats:
        (Optional) A value or iterable of values suitable as ``datetime.datetime.strptime`` format
        strings, for example ``('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f')``. If the parameter is
        present, ``strptime()`` will be used for parsing instead of the built-in parser.
    :param serialized_format:
        The output format suitable for Python ``strftime``. Default: ``'%Y-%m-%dT%H:%M:%S.%f%z'``
    :param parser:
        (Optional) An external function to use for parsing instead of the built-in parser. It should
        return a ``datetime.datetime`` instance.
    :param tzd:
        Sets the time zone policy.
        Default: ``'allow'``
            ============== ======================================================================
            ``'require'``  Values must specify a time zone.
            ``'allow'``    Values both with and without a time zone designator are allowed.
            ``'utc'``      Like ``allow``, but values with no time zone information are assumed
                           to be in UTC.
            ``'reject'``   Values must not specify a time zone. This also prohibits timestamps.
            ============== ======================================================================
    :param convert_tz:
        Indicates whether values with a time zone designator should be automatically converted to UTC.
        Default: ``False``
            * ``True``:  Convert the datetime to UTC based on its time zone offset.
            * ``False``: Don't convert. Keep the original time and offset intact.
    :param drop_tzinfo:
        Can be set to automatically remove the ``tzinfo`` objects. This option should generally
        be used in conjunction with the ``convert_tz`` option unless you only care about local
        wall clock times. Default: ``False``
            * ``True``:  Discard the ``tzinfo`` components and make naive ``datetime`` objects instead.
            * ``False``: Preserve the ``tzinfo`` components if present.
    """

    SERIALIZED_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'

    MESSAGES = {
        'parse': u'Could not parse {0}. Should be ISO 8601 or timestamp.',
        'parse_formats': u'Could not parse {0}. Valid formats: {1}',
        'parse_external': u'Could not parse {0}.',
        'parse_tzd_require': u'Could not parse {0}. Time zone offset required.',
        'parse_tzd_reject': u'Could not parse {0}. Time zone offset not allowed.',
        'tzd_require': u'Could not convert {0}. Time zone required but not found.',
        'tzd_reject': u'Could not convert {0}. Time zone offsets not allowed.',
        'validate_tzd_require': u'Time zone information required but not found.',
        'validate_tzd_reject': u'Time zone information not allowed.',
        'validate_utc_none': u'Time zone must be UTC but was None.',
        'validate_utc_wrong': u'Time zone must be UTC.',
    }

    REGEX = re.compile(r"""
                (?P<year>\d{4})-(?P<month>\d\d)-(?P<day>\d\d)(?:T|\ )
                (?P<hour>\d\d):(?P<minute>\d\d)
                (?::(?P<second>\d\d)(?:(?:\.|,)(?P<sec_frac>\d{1,6}))?)?
                (?:(?P<tzd_offset>(?P<tzd_sign>[+−-])(?P<tzd_hour>\d\d):?(?P<tzd_minute>\d\d)?)
                |(?P<tzd_utc>Z))?$""", re.X)

    TIMEDELTA_ZERO = datetime.timedelta(0)

    class fixed_timezone(datetime.tzinfo):
        def utcoffset(self, dt): return self.offset
        def fromutc(self, dt): return dt + self.offset
        def dst(self, dt): return None
        def tzname(self, dt): return self.str
        def __str__(self): return self.str
        def __repr__(self, info=''): return '{0}({1})'.format(type(self).__name__, info)

    class utc_timezone(fixed_timezone):
        offset = datetime.timedelta(0)
        name = str = 'UTC'

    class offset_timezone(fixed_timezone):
        def __init__(self, hours=0, minutes=0):
            self.offset = datetime.timedelta(hours=hours, minutes=minutes)
            total_seconds = self.offset.days * 86400 + self.offset.seconds
            self.str = '{0:s}{1:02d}:{2:02d}'.format(
                '+' if total_seconds >= 0 else '-',
                int(abs(total_seconds) / 3600),
                int(abs(total_seconds) % 3600 / 60))
        def __repr__(self):
            return DateTimeType.fixed_timezone.__repr__(self, self.str)

    UTC = utc_timezone()
    EPOCH = datetime.datetime(1970, 1, 1, tzinfo=UTC)

    def __init__(self, formats=None, serialized_format=None, parser=None,
                 tzd='allow', convert_tz=False, drop_tzinfo=False, **kwargs):

        if isinstance(formats, string_type):
            formats = [formats]
        self.formats = formats
        self.serialized_format = serialized_format or self.SERIALIZED_FORMAT
        self.parser = parser
        self.tzd = tzd
        self.convert_tz = convert_tz
        self.drop_tzinfo = drop_tzinfo

        super(DateTimeType, self).__init__(**kwargs)

    def _mock(self, context=None):
        mocked = datetime.datetime(
            year=random.randrange(600) + 1900,
            month=random.randrange(12) + 1,
            day=random.randrange(28) + 1,
            hour=random.randrange(24),
            minute=random.randrange(60),
            second=random.randrange(60),
            microsecond=random.randrange(1000000),
        )

        # Validated datetime is guaranteed to be naive
        if self.tzd == 'reject':
            return mocked

        # Validated datetime is guaranteed to be in utc
        if self.tzd == 'utc':
            return mocked.replace(tzinfo=self.UTC)

        # Validated datetime is guaranteed to be timezone-aware
        if self.tzd == 'require':
            if self.convert_tz:
                return mocked.replace(tzinfo=self.UTC)
            hours = random.randrange(MIMIMUM_TZ_HOUR_OFFSET,
                                     MAXIMUM_TZ_HOUR_OFFSET + 1)
            return mocked.replace(tzinfo=self.offset_timezone(hours=hours))

        # Validated datetime can be timezone-naive or -aware.
        if self.tzd == 'allow':
            if self.drop_tzinfo:
                return mocked

            # We always need to return a timezone-aware
            if self.convert_tz:
                return mocked.replace(tzinfo=self.UTC)

            # We return a timezone-naive datetime in half the cases.
            if random.randrange(2):
                return mocked

            hours = random.randrange(MIMIMUM_TZ_HOUR_OFFSET,
                                     MAXIMUM_TZ_HOUR_OFFSET + 1)
            return mocked.replace(tzinfo=self.offset_timezone(hours=hours))

        raise ValueError('Unknown tzd: %r' % self.tzd)

    def to_native(self, value, context=None):

        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                if not self.drop_tzinfo:
                    if self.tzd == 'require':
                        raise ConversionError(self.messages['tzd_require'].format(value))
                    if self.tzd == 'utc':
                        value = value.replace(tzinfo=self.UTC)
            else:
                if self.tzd == 'reject':
                    raise ConversionError(self.messages['tzd_reject'].format(value))
                if self.convert_tz:
                    value = value.astimezone(self.UTC)
                if self.drop_tzinfo:
                    value = value.replace(tzinfo=None)
            return value

        if self.formats:
            # Delegate to datetime.datetime.strptime() using provided format strings.
            for fmt in self.formats:
                try:
                    dt = datetime.datetime.strptime(value, fmt)
                    break
                except (ValueError, TypeError):
                    continue
            else:
                raise ConversionError(self.messages['parse_formats'].format(value, ", ".join(self.formats)))
        elif self.parser:
            # Delegate to external parser.
            try:
                dt = self.parser(value)
            except:
                raise ConversionError(self.messages['parse_external'].format(value))
        else:
            # Use built-in parser.
            try:
                value = float(value)
            except ValueError:
                dt = self.from_string(value)
            else:
                dt = self.from_timestamp(value)
            if not dt:
                raise ConversionError(self.messages['parse'].format(value))

        if dt.tzinfo is None:
            if self.tzd == 'require':
                raise ConversionError(self.messages['parse_tzd_require'].format(value))
            if self.tzd == 'utc' and not self.drop_tzinfo:
                dt = dt.replace(tzinfo=self.UTC)
        else:
            if self.tzd == 'reject':
                raise ConversionError(self.messages['parse_tzd_reject'].format(value))
            if self.convert_tz:
                dt = dt.astimezone(self.UTC)
            if self.drop_tzinfo:
                dt = dt.replace(tzinfo=None)

        return dt

    def from_string(self, value):
        match = self.REGEX.match(value)
        if not match:
            return None
        parts = dict(((k, v) for k, v in match.groupdict().items() if v is not None))
        p = lambda name: int(parts.get(name, 0))
        microsecond = p('sec_frac') and p('sec_frac') * 10 ** (6 - len(parts['sec_frac']))
        if 'tzd_utc' in parts:
            tz = self.UTC
        elif 'tzd_offset' in parts:
            tz_sign = 1 if parts['tzd_sign'] == '+' else -1
            tz_offset = (p('tzd_hour') * 60 + p('tzd_minute')) * tz_sign
            if tz_offset == 0:
                tz = self.UTC
            else:
                tz = self.offset_timezone(minutes=tz_offset)
        else:
            tz = None
        try:
            return datetime.datetime(p('year'), p('month'), p('day'),
                                     p('hour'), p('minute'), p('second'),
                                     microsecond, tz)
        except (ValueError, TypeError):
            return None

    def from_timestamp(self, value):
        try:
            return datetime.datetime(1970, 1, 1, tzinfo=self.UTC) + datetime.timedelta(seconds=value)
        except (ValueError, TypeError):
            return None

    def to_primitive(self, value, context=None):
        if callable(self.serialized_format):
            return self.serialized_format(value)
        return value.strftime(self.serialized_format)

    def validate_tz(self, value, context=None):
        if value.tzinfo is None:
            if not self.drop_tzinfo:
                if self.tzd == 'require':
                    raise ValidationError(self.messages['validate_tzd_require'])
                if self.tzd == 'utc':
                    raise ValidationError(self.messages['validate_utc_none'])
        else:
            if self.drop_tzinfo:
                raise ValidationError(self.messages['validate_tzd_reject'])
            if self.tzd == 'reject':
                raise ValidationError(self.messages['validate_tzd_reject'])
            if (self.tzd == 'utc' or self.convert_tz) \
              and value.tzinfo.utcoffset(value) != self.TIMEDELTA_ZERO:
                raise ValidationError(self.messages['validate_utc_wrong'])


class UTCDateTimeType(DateTimeType):

    """A variant of ``DateTimeType`` that normalizes everything to UTC and stores values
    as naive ``datetime`` instances. By default sets ``tzd='utc'``, ``convert_tz=True``,
    and ``drop_tzinfo=True``. The standard export format always includes the UTC time
    zone designator ``"Z"``.
    """

    SERIALIZED_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

    def __init__(self, formats=None, parser=None, tzd='utc', convert_tz=True, drop_tzinfo=True, **kwargs):
        super(UTCDateTimeType, self).__init__(formats=formats, parser=parser, tzd=tzd,
                                              convert_tz=convert_tz, drop_tzinfo=drop_tzinfo, **kwargs)


class TimestampType(DateTimeType):

    """A variant of ``DateTimeType`` that exports itself as a Unix timestamp
    instead of an ISO 8601 string. Always sets ``tzd='require'`` and
    ``convert_tz=True``.
    """

    def __init__(self, formats=None, parser=None, drop_tzinfo=False, **kwargs):
        super(TimestampType, self).__init__(formats=formats, parser=parser, tzd='require',
                                            convert_tz=True, drop_tzinfo=drop_tzinfo, **kwargs)

    def to_primitive(self, value):
        if value.tzinfo is None:
            value = value.replace(tzinfo=self.UTC)
        else:
            value = value.astimezone(self.UTC)
        delta = value - self.EPOCH
        ts = (delta.days * 24 * 3600) + delta.seconds + delta.microseconds / 1E6
        if delta.microseconds:
            return ts
        else:
            return int(ts)


class GeoPointType(BaseType):

    """A list storing a latitude and longitude.
    """

    MESSAGES = {
        'point_min': u"{0} value {1} should be greater than or equal to {2}.",
        'point_max': u"{0} value {1} should be less than or equal to {2}."
    }

    def _mock(self, context=None):
        return (random.randrange(-90, 90), random.randrange(-180, 180))

    @classmethod
    def _normalize(cls, value):
        if isinstance(value, dict):
            return value.values()
        else:
            return value

    def to_native(self, value, context=None):
        """Make sure that a geo-value is of type (x, y)
        """
        if not isinstance(value, (tuple, list, dict)):
            raise ConversionError('GeoPointType can only accept tuples, lists, or dicts')
        elements = self._normalize(value)
        if not len(elements) == 2:
            raise ConversionError('Value must be a two-dimensional point')
        if not all(isinstance(v, (float, int)) for v in elements):
            raise ConversionError('Both values in point must be float or int')
        return value

    def validate_range(self, value, context=None):
        latitude, longitude = self._normalize(value)
        if latitude < -90:
            raise ValidationError(
                self.messages['point_min'].format('Latitude', latitude, '-90')
            )
        if latitude > 90:
            raise ValidationError(
                self.messages['point_max'].format('Latitude', latitude, '90')
            )
        if longitude < -180:
            raise ValidationError(
                self.messages['point_min'].format('Longitude', longitude, -180)
            )
        if longitude > 180:
            raise ValidationError(
                self.messages['point_max'].format('Longitude', longitude, 180)
            )


class MultilingualStringType(BaseType):

    """
    A multilanguage string field, stored as a dict with {'locale': 'localized_value'}.

    Minimum and maximum lengths apply to each of the localized values.

    At least one of ``default_locale`` or ``context.app_data['locale']`` must be defined
    when calling ``.to_primitive``.

    """

    allow_casts = (int, bytes)

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
            raise ConversionError('Value must be a dict or None')

        return value

    def to_primitive(self, value, context=None):
        """
        Use a combination of ``default_locale`` and ``context.app_data['locale']`` to return
        the best localized string.

        """
        if value is None:
            return None

        context_locale = None
        if context and 'locale' in context.app_data:
            context_locale = context.app_data['locale']

        # Build a list of all possible locales to try
        possible_locales = []
        for locale in (context_locale, self.default_locale):
            if not locale:
                continue

            if isinstance(locale, string_type):
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

        if not isinstance(localized, str):
            if isinstance(localized, self.allow_casts):
                if isinstance(localized, bytes):
                    localized = str(localized, 'utf-8')
                else:
                    localized = str(localized)
            else:
                raise ConversionError(self.messages['convert'])

        return localized

    def validate_length(self, value, context=None):
        for locale, localized in value.items():
            len_of_value = len(localized) if localized else 0

            if self.max_length is not None and len_of_value > self.max_length:
                raise ValidationError(self.messages['max_length'].format(locale))

            if self.min_length is not None and len_of_value < self.min_length:
                raise ValidationError(self.messages['min_length'].format(locale))

    def validate_regex(self, value, context=None):
        if self.regex is None and self.locale_regex is None:
            return

        for locale, localized in value.items():
            if self.regex is not None and self.regex.match(localized) is None:
                raise ValidationError(
                    self.messages['regex_localized'].format(locale))

            if self.locale_regex is not None and self.locale_regex.match(locale) is None:
                raise ValidationError(
                    self.messages['regex_locale'].format(locale))


__all__ = module_exports(__name__)
