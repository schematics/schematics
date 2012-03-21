import uuid
import re
import datetime
import decimal

from dictshield.base import ShieldException, InvalidShield

from dictshield.fields import dictshield_fields


class BaseFieldMetaClass(type):
    def __init__(cls, name, bases, dct):
        if hasattr(cls, '_from_jsonschema_formats'):
            for fmt in cls._from_jsonschema_formats():
                for tipe in cls._from_jsonschema_types():
                    dictshield_fields[(tipe, fmt)] = cls
        super(BaseFieldMetaClass, cls).__init__(name, bases, dct)


###
### Fields
###

class BaseField(object):
    """A base class for fields in a DictShield document. Instances of this
    class may be added to subclasses of `Document` to define a document's
    schema.
    """

    __metaclass__ = BaseFieldMetaClass

    def __init__(self, uniq_field=None, field_name=None, required=False,
                 default=None, id_field=False, validation=None, choices=None,
                 description=None, minimized_field_name=None):

        self.uniq_field = '_id' if id_field else uniq_field or field_name
        self.field_name = field_name
        self.required = required
        self.default = default
        self.validation = validation
        self.choices = choices
        self.id_field = id_field
        self.description = description
        self.minimized_field_name = minimized_field_name

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a document. Do
        any necessary conversion between Python and `DictShield` types.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = instance._data.get(self.field_name)

        if value is None:
            value = self.default
            # Allow callable default values
            if callable(value):
                value = value()
        return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document.
        """
        instance._data[self.field_name] = value

    def for_python(self, value):
        """Convert a DictShield type into native Python value
        """
        return value

    def for_json(self, value):
        """Convert a DictShield type into a value safe for JSON encoding
        """
        return self.for_python(value)

    def validate(self, value):
        """Perform validation on a value.
        """
        pass

    def _validate(self, value):
        # check choices
        if self.choices is not None:
            if value not in self.choices:
                raise ShieldException("Value must be one of %s."
                    % unicode(self.choices))

        # check validation argument
        if self.validation is not None:
            if callable(self.validation):
                if not self.validation(value):
                    raise ShieldException('Value does not match custom' \
                                          'validation method.')
            else:
                raise ValueError('validation argument must be a callable.')

        return self.validate(value)

    def _jsonschema_default(self):
        if callable(self.default):
            # jsonschema doesn't support procedural defaults
            return None
        else:
            return self.default

    def _jsonschema_description(self):
        return self.description

    def _jsonschema_title(self):
        if self.field_name:
            return self.field_name
        else:
            return None

    def _jsonschema_type(self):
        return 'any'

    def _jsonschema_required(self):
        if self.required is True:
            return self.required
        else:
            return None

    def for_jsonschema(self):
        """Generate the jsonschema by mapping the value of all methods
        beginning `_jsonschema_' to a key that is the name of the method after
        `_jsonschema_'.

        For example, `_jsonschema_type' will populate the schema key 'type'.
        """

        schema = {}
        get_name = lambda x: x.startswith('_jsonschema')
        for func_name in filter(get_name, dir(self)):
            attr_name = func_name.split('_')[-1]
            attr_value = getattr(self, func_name)()
            if attr_value is not None:
                schema[attr_name] = attr_value
        return schema


class UUIDField(BaseField):
    """A field that stores a valid UUID value and optionally auto-populates
    empty values with new UUIDs.
    """

    def __init__(self, auto_fill=False, **kwargs):
        super(UUIDField, self).__init__(**kwargs)
        self.auto_fill = auto_fill

    def __set__(self, instance, value):
        """Convert any text values provided into Python UUID objects and
        auto-populate any empty values should auto_fill be set to True.
        """
        if not value and self.auto_fill is True:
            value = uuid.uuid4()

        if value and not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)

        instance._data[self.field_name] = value

    def _jsonschema_type(self):
        return 'string'

    def validate(self, value):
        """Make sure the value is a valid uuid representation.  See
        http://docs.python.org/library/uuid.html for accepted formats.
        """
        if not isinstance(value, (uuid.UUID,)):
            try:
                value = uuid.UUID(value)
            except ValueError:
                raise ShieldException('Not a valid UUID value',
                    self.field_name, value)
        return value

    def for_json(self, value):
        """Return a JSON safe version of the UUID object.
        """

        return str(value)


class StringField(BaseField):
    """A unicode string field.
    """

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super(StringField, self).__init__(**kwargs)

    def _jsonschema_type(self):
        return 'string'

    @classmethod
    def _from_jsonschema_types(self):
        return ['string']

    @classmethod
    def _from_jsonschema_formats(self):
        return [None, 'phone']

    def _jsonschema_maxLength(self):
        return self.max_length

    def _jsonschema_minLength(self):
        return self.min_length

    def _jsonschema_pattern(self):
        return self.regex

    def for_python(self, value):
        return unicode(value)

    def validate(self, value):
        assert isinstance(value, (str, unicode))

        if self.max_length is not None and len(value) > self.max_length:
            raise ShieldException('String value is too long',
                                  self.field_name, value)

        if self.min_length is not None and len(value) < self.min_length:
            raise ShieldException('String value is too short',
                                  self.uniq_field, value)

        if self.regex is not None and self.regex.match(value) is None:
            message = 'String value did not match validation regex',
            raise ShieldException(message, self.uniq_field, value)

        return value

    def lookup_member(self, member_name):
        return None


###
### Web fields
###

class URLField(StringField):
    """A field that validates input as an URL.

    If verify_exists=True is passed the validate function will make sure
    the URL makes a valid connection.
    """

    URL_REGEX = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    def __init__(self, verify_exists=False, **kwargs):
        self.verify_exists = verify_exists
        super(URLField, self).__init__(**kwargs)

    def _jsonschema_format(self):
        return 'url'

    @classmethod
    def _from_jsonschema_formats(self):
        return ['url']

    def validate(self, value):
        if not URLField.URL_REGEX.match(value):
            raise ShieldException('Invalid URL', self.field_name, value)

        if self.verify_exists:
            import urllib2
            try:
                request = urllib2.Request(value)
                urllib2.urlopen(request)
            except Exception:
                message = 'URL does not exist'
                raise ShieldException(message, self.field_name, value)

        return value


class EmailField(StringField):
    """A field that validates input as an E-Mail-Address.
    """

    EMAIL_REGEX = re.compile(
        # dot-atom
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016'
        r'-\177])*"'
        # domain
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$',
        re.IGNORECASE
    )

    def validate(self, value):
        if not EmailField.EMAIL_REGEX.match(value):
            raise ShieldException('Invalid email address', self.field_name,
                                  value)
        return value

    def _jsonschema_format(self):
        return 'email'

    @classmethod
    def _from_jsonschema_formats(self):
        return ['email']


###
### Numbers
###

class JsonNumberMixin(object):
    """A mixin to support json schema validation for max, min, and type for all
    number fields, including DecimalField, which does not inherit from
    NumberField.
    """

    def _jsonschema_type(self):
        return 'number'

    def _jsonschema_maximum(self):
        return self.max_value

    def _jsonschema_minimum(self):
        return self.min_value


class NumberField(JsonNumberMixin, BaseField):
    """A number field.
    """

    def __init__(self, number_class, number_type,
                 min_value=None, max_value=None, **kwargs):
        self.number_class = number_class
        self.number_type = number_type
        self.min_value = min_value
        self.max_value = max_value
        super(NumberField, self).__init__(**kwargs)

    def for_python(self, value):
        return self.number_class(value)

    def validate(self, value):
        try:
            value = self.number_class(value)
        except:
            raise ShieldException('Not %s' % self.number_type, self.field_name,
                                  value)

        if self.min_value is not None and value < self.min_value:
            raise ShieldException('%s value below min_value: %s'
                                  % (self.number_type, self.min_value),
                                  self.field_name, value)

        if self.max_value is not None and value > self.max_value:
            raise ShieldException('%s value above max_value: %s'
                                  % (self.number_type, self.max_value),
                                  self.field_name, value)

        return value


class IntField(NumberField):
    """A field that validates input as an Integer
    """

    def __init__(self, *args, **kwargs):
        super(IntField, self).__init__(number_class=int,
                                       number_type='Int',
                                       *args, **kwargs)

    def _jsonschema_type(self):
        return 'number'

    @classmethod
    def _from_jsonschema_types(self):
        return ['number', 'integer']

    @classmethod
    def _from_jsonschema_formats(self):
        return [None]


class LongField(NumberField):
    """A field that validates input as a Long
    """
    def __init__(self, *args, **kwargs):
        super(LongField, self).__init__(number_class=long,
                                        number_type='Long',
                                        *args, **kwargs)


class FloatField(NumberField):
    """A field that validates input as a Float
    """
    def __init__(self, *args, **kwargs):
        super(FloatField, self).__init__(number_class=float,
                                         number_type='Float',
                                         *args, **kwargs)


class DecimalField(BaseField, JsonNumberMixin):
    """A fixed-point decimal number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(DecimalField, self).__init__(**kwargs)

    def for_python(self, value):
        if not isinstance(value, basestring):
            value = unicode(value)
        return decimal.Decimal(value)

    def for_json(self, value):
        return unicode(value)

    def validate(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, basestring):
                value = str(value)
            try:
                value = decimal.Decimal(value)
            except Exception:
                raise ShieldException('Could not convert to decimal',
                                      self.field_name, value)

        if self.min_value is not None and value < self.min_value:
            raise ShieldException('Decimal value below min_value: %s'
                                  % self.min_value, self.field_name, value)

        if self.max_value is not None and value > self.max_value:
            raise ShieldException('Decimal value above max_value: %s'
                                  % self.max_value, self.field_name, value)

        return value


###
### Hashing fields
###

class JsonHashMixin:
    """A mixin to support jsonschema validation for hashes
    """

    def _jsonschema_type(self):
        return 'string'

    def _jsonschema_maxLength(self):
        return self.hash_length

    def _jsonschema_minLength(self):
        return self.hash_length


class MD5Field(BaseField, JsonHashMixin):
    """A field that validates input as resembling an MD5 hash.
    """
    hash_length = 32

    def validate(self, value):
        if len(value) != MD5Field.hash_length:
            raise ShieldException('MD5 value is wrong length', self.field_name,
                                  value)
        try:
            int(value, 16)
        except:
            raise ShieldException('MD5 value is not hex', self.field_name,
                                  value)
        return value


class SHA1Field(BaseField, JsonHashMixin):
    """A field that validates input as resembling an SHA1 hash.
    """
    hash_length = 40

    def validate(self, value):
        if len(value) != SHA1Field.hash_length:
            raise ShieldException('SHA1 value is wrong length',
                                  self.field_name, value)
        try:
            int(value, 16)
        except:
            raise ShieldException('SHA1 value is not hex', self.field_name,
                                  value)
        return value


###
### Native type'ish fields
###

class BooleanField(BaseField):
    """A boolean field type.
    """

    def _jsonschema_type(self):
        return 'boolean'

    @classmethod
    def _from_jsonschema_types(self):
        return ['boolean']

    @classmethod
    def _from_jsonschema_formats(self):
        return [None]

    def for_python(self, value):
        return bool(value)

    def validate(self, value):
        if not isinstance(value, bool):
            raise ShieldException('Not a boolean', self.field_name, value)
        return value


class DateTimeField(BaseField):
    """A datetime field.
    """

    def _jsonschema_type(self):
        return 'string'

    def __init__(self, format=lambda dt: dt.isoformat(), **kwargs):
        self.format = format
        super(DateTimeField, self).__init__(**kwargs)

    def _jsonschema_format(self):
        return 'date-time'

    @classmethod
    def _from_jsonschema_types(self):
        return ['string']

    @classmethod
    def _from_jsonschema_formats(self):
        return ['date-time', 'date', 'time']

    def __set__(self, instance, value):
        """If `value` is a string, the string should match iso8601 format.
        `iso8601_to_date` is called for conversion.

        A datetime may be used (and is encouraged).
        """
        if not value:
            return

        if isinstance(value, (str, unicode)):
            value = DateTimeField.iso8601_to_date(value)

        instance._data[self.field_name] = value

    @classmethod
    def iso8601_to_date(cls, datestring):
        """Takes a string in ISO8601 format and converts it to a Python
        datetime.  This is not present in the standard library, as far as I can
        tell.

        Example: 'YYYY-MM-DDTHH:MM:SS.mmmmmm'

        ISO8601's elements come in the same order as the inputs to creating
        a datetime.datetime.  I pass the patterns directly into the datetime
        constructor.

        The ISO8601 spec is rather complex and allows for many variations in
        formatting values.  Currently the format expected is strict, with the
        only optional component being the six-digit microsecond field.

        http://www.w3.org/TR/NOTE-datetime
        """
        iso8601 = '(\d\d\d\d)-(\d\d)-(\d\d)' \
                  'T(\d\d):(\d\d):(\d\d)(?:\.(\d\d\d\d\d\d))?'
        elements = re.findall(iso8601, datestring)
        date_info = elements[0]
        date_digits = [int(d) for d in date_info if d]
        value = datetime.datetime(*date_digits)
        return value

    @classmethod
    def date_to_iso8601(cls, dt, format):
        """Classmethod that goes the opposite direction of iso8601_to_date.
           Defaults to using isoformat(), but can use the optional format
           argument either as a strftime format string or as a custom
           date formatting function or lambda.
        """
        if isinstance(format, str):
            iso_dt = dt.strftime(format)
        elif hasattr(format, '__call__'):
            iso_dt = format(dt)
        else:
            raise ShieldException('DateTimeField format must be a string or callable')
        return iso_dt

    def validate(self, value):
        if not isinstance(value, datetime.datetime):
            raise ShieldException('Not a datetime', self.field_name, value)
        return value

    def for_python(self, value):
        return value

    def for_json(self, value):
        v = DateTimeField.date_to_iso8601(value, self.format)
        return v


class DictField(BaseField):
    """A dictionary field that wraps a standard Python dictionary. This is
    similar to an embedded document, but the structure is not defined.
    """

    def _jsonschema_type(self):
        return 'object'

    def __init__(self, basecls=None, *args, **kwargs):
        self.basecls = basecls or BaseField
        if not issubclass(self.basecls, BaseField):
            raise InvalidShield('basecls is not subclass of BaseField')
        kwargs.setdefault('default', lambda: {})
        super(DictField, self).__init__(*args, **kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, dict):
            raise ShieldException('Only dictionaries may be used in a '
                                  'DictField', self.field_name, value)

        if any(('.' in k or '$' in k) for k in value):
            raise ShieldException('Invalid dictionary key name - keys may not '
                                  'contain "." or "$" characters',
                                  self.field_name, value)
        return value

    def lookup_member(self, member_name):
        return self.basecls(uniq_field=member_name)


class GeoPointField(BaseField):
    """A list storing a latitude and longitude.
    """

    def _jsonschema_type(self):
        return 'array'

    def _jsonschema_items(self):
        return NumberField().for_jsonschema()

    def _jsonschema_maxLength(self):
        return 2

    def _jsonschema_minLength(self):
        return 2

    def validate(self, value):
        """Make sure that a geo-value is of type (x, y)
        """
        if not len(value) == 2:
            raise ShieldException('Value must be a two-dimensional point',
                                  self.field_name, value)
        if isinstance(value, dict):
            for v in value.values():
                if not isinstance(v, (float, int)):
                    error_msg = 'Both values in point must be float or int'
                    raise ShieldException(error_msg, self.field_name, value)
        elif isinstance(value, (list, tuple)):
            if (not isinstance(value[0], (float, int)) and
                not isinstance(value[1], (float, int))):
                error_msg = 'Both values in point must be float or int'
                raise ShieldException(error_msg, self.field_name, value)
        else:
            raise ShieldException('GeoPointField can only accept tuples, '
                                  'lists of (x, y), or dicts of {k1: v1, '
                                  'k2: v2}',
                                  self.field_name, value)
        return value
