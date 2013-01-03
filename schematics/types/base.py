import uuid
import re
import datetime
import decimal


from schematics.validation import (TypeResult, FieldResult,
                                   OK, ERROR_TYPE_COERCION, ERROR_FIELD_CONFIG,
                                   ERROR_FIELD_BAD_CHOICE,
                                   ERROR_FIELD_TYPE_CHECK)
from schematics.types import schematic_types


class BaseTypeMetaClass(type):
    def __init__(cls, name, bases, dct):
        if hasattr(cls, '_from_jsonschema_formats'):
            for fmt in cls._from_jsonschema_formats():
                for tipe in cls._from_jsonschema_types():
                    schematic_types[(tipe, fmt)] = cls
        super(BaseTypeMetaClass, cls).__init__(name, bases, dct)


###
### Base Type
###

class BaseType(object):
    """A base class for Types in a Structures model. Instances of this
    class may be added to subclasses of `Model` to define a model schema.
    """

    __metaclass__ = BaseTypeMetaClass

    def __init__(self, required=False, default=None, field_name=None,
                 print_name=None, choices=None, validation=None, description=None,
                 minimized_field_name=None):

        self.required = required
        self.default = default
        self.field_name = field_name
        self.print_name = print_name
        self.choices = choices
        self.validation = validation
        self.description = description
        self.minimized_field_name = minimized_field_name

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a model. Do
        any necessary conversion between Python and `Structures` types.
        """
        if instance is None:
            # Model class being used rather than a model object
            return self

        value = instance._data.get(self.field_name)

        if value is None:
            value = self.default
            # Callable values are best for mutable defaults
            if callable(value):
                value = value()
        return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a model.
        """
        instance._data[self.field_name] = value

    def for_python(self, value):
        """Convert a Structures type into native Python value
        """
        return value

    def for_json(self, value):
        """Convert a Structures type into a value safe for JSON encoding
        """
        return self.for_python(value)

    def validate(self, value):
        """Function that is overridden by subclasses for their validation logic
        """
        pass

    def _validate(self, value):
        """This function runs before `validate()` and handles applying the
        global environment parameters.
        """
        # `choices`
        if self.choices is not None:
            if value not in self.choices:
                error_msg = 'Value must be one of %s.' % unicode(self.choices)
                return FieldResult(ERROR_FIELD_BAD_CHOICE, error_msg,
                                   self.field_name, value)

        # `validation` function
        if self.validation is not None:
            if callable(self.validation):
                if not self.validation(value):
                    error_msg = 'Value failed custom validation.'
                    return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                       self.field_name, value)
            else:
                error_msg = 'Validation argument must be a callable.'
                return FieldResult(ERROR_FIELD_CONFIG, error_msg,
                                   self.field_name, value)

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


###
### Standard Types
###

class UUIDType(BaseType):
    """A field that stores a valid UUID value and optionally auto-populates
    empty values with new UUIDs.
    """

    def __init__(self, auto_fill=False, **kwargs):
        super(UUIDType, self).__init__(**kwargs)
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
        new_value = value
        
        if not isinstance(value, (uuid.UUID,)):
            try:
                new_value = uuid.UUID(value)
            except ValueError:
                error_msg = 'Not a valid UUID value'
                return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                   self.field_name, value)

        return FieldResult(OK, 'success', self.field_name, new_value)

    def for_json(self, value):
        """Return a JSON safe version of the UUID object.
        """

        return str(value)


class StringType(BaseType):
    """A unicode string field.
    """

    def __init__(self, regex=None, max_length=None, min_length=None, empty=False, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super(StringType, self).__init__(**kwargs)

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
        if value is None:
            return None
        return unicode(value)

    def validate(self, value):
        assert isinstance(value, (str, unicode))

        if self.max_length is not None and len(value) > self.max_length:
            error_msg = 'String value is too long'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        if self.min_length is not None and len(value) < self.min_length:
            error_msg = 'String value is too short'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        if self.regex is not None and self.regex.match(value) is None:
            error_msg = 'String value did not match validation regex'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
                               
        if not self.empty and len(value.strip()) == 0:
            error_msg = 'String value cannot be empty'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)                               

        return FieldResult(OK, 'success', self.field_name, value)
    

    def lookup_member(self, member_name):
        return None


###
### Web fields
###

class URLType(StringType):
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
        super(URLType, self).__init__(**kwargs)

    def _jsonschema_format(self):
        return 'url'

    @classmethod
    def _from_jsonschema_formats(self):
        return ['url']

    def validate(self, value):
        if not URLType.URL_REGEX.match(value):
            error_msg = 'Invalid URL'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        if self.verify_exists:
            import urllib2
            try:
                request = urllib2.Request(value)
                urllib2.urlopen(request)
            except Exception:
                error_msg = 'URL does not exist'
                return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                   self.field_name, value)

        return FieldResult(OK, 'success', self.field_name, value)


class EmailType(StringType):
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
        if not EmailType.EMAIL_REGEX.match(value):
            error_msg = 'Invalid email address'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        return FieldResult(OK, 'success', self.field_name, value)


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
    number fields, including DecimalType, which does not inherit from
    NumberType.
    """

    def _jsonschema_type(self):
        return 'number'

    def _jsonschema_maximum(self):
        return self.max_value

    def _jsonschema_minimum(self):
        return self.min_value


class NumberType(JsonNumberMixin, BaseType):
    """A number field.
    """

    def __init__(self, number_class, number_type,
                 min_value=None, max_value=None, **kwargs):
        self.number_class = number_class
        self.number_type = number_type
        self.min_value = min_value
        self.max_value = max_value
        super(NumberType, self).__init__(**kwargs)

    def __set__(self, instance, value):
        if value != None and not isinstance(value, self.number_class):
            if self.number_class:
                value = self.number_class(value)
        instance._data[self.field_name] = value    

    def for_python(self, value):
        return self.number_class(value)

    def validate(self, value):
        try:
            value = self.number_class(value)
        except:
            error_msg = 'Not %s' % self.number_type
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        if self.min_value is not None and value < self.min_value:
            error_msg = '%s value below min_value: %s' % (self.number_type,
                                                          self.min_value)
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        if self.max_value is not None and value > self.max_value:
            error_msg = '%s value above max_value: %s' % (self.number_type,
                                                          self.max_value)
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        return FieldResult(OK, 'success', self.field_name, value)


class IntType(NumberType):
    """A field that validates input as an Integer
    """

    def __init__(self, *args, **kwargs):
        super(IntType, self).__init__(number_class=int,
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


class LongType(NumberType):
    """A field that validates input as a Long
    """
    def __init__(self, *args, **kwargs):
        super(LongType, self).__init__(number_class=long,
                                        number_type='Long',
                                        *args, **kwargs)


class FloatType(NumberType):
    """A field that validates input as a Float
    """
    def __init__(self, *args, **kwargs):
        super(FloatType, self).__init__(number_class=float,
                                         number_type='Float',
                                         *args, **kwargs)


class DecimalType(BaseType, JsonNumberMixin):
    """A fixed-point decimal number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(DecimalType, self).__init__(**kwargs)

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
                error_msg = 'Could not convert to decimal'
                return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                   self.field_name, value)

        if self.min_value is not None and value < self.min_value:
            error_msg ='Decimal value below min_value: %s' % self.min_value
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        if self.max_value is not None and value > self.max_value:
            error_msg = 'Decimal value above max_value: %s' % self.max_value
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        return FieldResult(OK, 'success', self.field_name, value)


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


class MD5Type(BaseType, JsonHashMixin):
    """A field that validates input as resembling an MD5 hash.
    """
    hash_length = 32

    def validate(self, value):
        if len(value) != MD5Type.hash_length:
            error_msg = 'MD5 value is wrong length'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        try:
            value = int(value, 16)
        except:
            error_msg = 'MD5 value is not hex'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        return FieldResult(OK, 'success', self.field_name, value)



class SHA1Type(BaseType, JsonHashMixin):
    """A field that validates input as resembling an SHA1 hash.
    """
    hash_length = 40

    def validate(self, value):
        if len(value) != SHA1Type.hash_length:
            error_msg = 'SHA1 value is wrong length'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        try:
            value = int(value, 16)
        except:
            error_msg = 'SHA1 value is not hex'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        return FieldResult(OK, 'success', self.field_name, value)



###
### Native type'ish fields
###

class BooleanType(BaseType):
    """A boolean field type.
    """

    TRUE = ('True', 'true', '1')
    FALSE = ('False', 'false', '0')

    def _jsonschema_type(self):
        return 'boolean'

    @classmethod
    def _from_jsonschema_types(self):
        return ['boolean']

    @classmethod
    def _from_jsonschema_formats(self):
        return [None]

    def __set__(self, instance, value):
        """
        Accept some form of True/False as string
        """
        if isinstance(value, (str, unicode)):
            if value in BooleanType.TRUE:
                value = True
            elif value in BooleanType.FALSE:
                value = False

        instance._data[self.field_name] = value

    def for_python(self, value):
        return bool(value)

    def validate(self, value):
        if not isinstance(value, bool):
            error_msg = 'Not a boolean'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        return FieldResult(OK, 'success', self.field_name, value)



class DateTimeType(BaseType):
    """A datetime field.
    """

    def _jsonschema_type(self):
        return 'string'

    def __init__(self, format=None, **kwargs):
        if format is None:
            def formatter(dt):
                if dt is None:
                    return None
                else:
                    return dt.isoformat()
            self.format = formatter
        else:
            self.format = format
        super(DateTimeType, self).__init__(**kwargs)

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
        if isinstance(value, (str, unicode)):
            result = DateTimeType.iso8601_to_date(value)
            value = result.value

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
        
        if len(elements) < 1:
            error_msg = 'Date string could not transform to datetime'
            return TypeResult(ERROR, error_msg, datestring)
        
        date_info = elements[0]
        date_digits = [int(d) for d in date_info if d]
        value = datetime.datetime(*date_digits)
        return TypeResult(OK, 'success', value)

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
            error_msg = 'DateTimeType format must be a string or callable'
            return TypeResult(ERROR, error_msg, dt)
        return TypeResult(OK, 'success', iso_dt)

    def validate(self, value):
        if not isinstance(value, datetime.datetime):
            error_msg = 'Not a datetime'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        return FieldResult(OK, 'success', self.field_name, value)

    def for_python(self, value):
        return value

    def for_json(self, value):
        result = DateTimeType.date_to_iso8601(value, self.format)
        return result.value


class DictType(BaseType):
    """A dictionary field that wraps a standard Python dictionary. This is
    similar to an `ModelType`, but the schematic is not defined.
    """

    def _jsonschema_type(self):
        return 'object'

    def __init__(self, basecls=None, *args, **kwargs):
        self.basecls = basecls or BaseType
        
        if not issubclass(self.basecls, BaseType):
            error_msg = 'basecls is not subclass of BaseType'
            return TypeResult(ERROR_TYPE_COERCION, error_msg, basecls)

        kwargs.setdefault('default', lambda: {})
        super(DictType, self).__init__(*args, **kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, dict):
            error_msg = 'Only dictionaries may be used in a DictType'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        ### TODO this can probably be removed
        if any(('.' in k or '$' in k) for k in value):
            error_msg = 'Invalid dictionary key - may not contain "." or "$"'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        return FieldResult(OK, 'success', self.field_name, value)

    def lookup_member(self, member_name):
        return self.basecls(field_name=member_name)


class GeoPointType(BaseType):
    """A list storing a latitude and longitude.
    """

    def _jsonschema_type(self):
        return 'array'

    def _jsonschema_items(self):
        return NumberType().for_jsonschema()

    def _jsonschema_maxLength(self):
        return 2

    def _jsonschema_minLength(self):
        return 2

    def validate(self, value):
        """Make sure that a geo-value is of type (x, y)
        """
        if not len(value) == 2:
            error_msg = 'Value must be a two-dimensional point'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        if isinstance(value, dict):
            for v in value.values():
                if not isinstance(v, (float, int)):
                    error_msg = 'Both values in point must be float or int'
                    return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                       self.field_name, value)
        elif isinstance(value, (list, tuple)):
            if (not isinstance(value[0], (float, int)) and
                not isinstance(value[1], (float, int))):
                error_msg = 'Both values in point must be float or int'
                return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                   self.field_name, value)
        else:
            error_msg = 'GeoPointType can only accept tuples, lists, or dicts'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        return FieldResult(OK, 'success', self.field_name, value)
