import uuid
import re
import datetime
import decimal
import itertools

from ..exceptions import StopValidation, ValidationError


def force_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    elif not obj is None:
        obj = unicode(obj)

    return obj


class BaseType(object):
    """A base class for Types in a Structures model. Instances of this
    class may be added to subclasses of `Model` to define a model schema.
    """

    def __init__(self, required=False, default=None, serialized_name=None,
                 choices=None, validators=None, description=None):

        self.required = required
        self.default = default
        self.serialized_name = serialized_name
        self.choices = choices
        self.validators = validators or []
        self.description = description

    def __call__(self, value):
        return self.validate(value)

    def to_primitive(self, value):
        """Convert a Structures type into a value safe for JSON encoding
        """
        return value

    def convert(self, value):
        """Convert Python to something safe to serialize to JSON.
        """
        return value

    def validate(self, value):
        """
        Validates the field and returns True or False. `self.errors` will
        contain any errors raised during validation. This is usually only
        called by `Form.validate`. If at the end of validate no errors were
        raised, assign `self.clean` the value. Either `self.errors` or
        `self.clean` is assigned, never both.

        """

        errors = []

        def aggregate_from_exception_errors(e):
            print e.__dict__, e.args
            if e.args and e.args[0]:
                if isinstance(e.args, (tuple, list)):
                    _errors = e.args[0]
                elif isinstance(e.args[0], basestring):
                    _errors = [e.args[0]]
                else:
                    _errors = []
                return errors.extend(_errors)

        validator_chain = itertools.chain(
            [
                self.required_validation,
                self.convert,
                self.choices_validation
            ],
            self.validators or []
        )

        for validator in validator_chain:
            try:
                value = validator(value)
            except ValidationError, e:
                aggregate_from_exception_errors(e)
                if isinstance(e, StopValidation):
                    break
            else:
                # Break validation chain if any of the
                # validators legally returns None
                if not self.required and value is None:
                    break

        if errors:
            raise ValidationError(errors)

        return value

    def required_validation(self, value):
        if self.required and value is None:
            raise StopValidation(u'Field must have a significant value')
        return value

    def choices_validation(self, value):
        # `choices`
        if self.choices is not None:
            if value not in self.choices:
                raise ValidationError(u'Value must be one of %s.' % unicode(self.choices))
        return value

    def _bind(self, model, memo):
        """Method that binds a field to a model. If `model` is None, a copy of
        the field is returned."""
        if model is not None and self.bound:
            raise TypeError('%r already bound' % type(model).__name__)

        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.validators = self.validators[:]

        if model is not None:
            rv.model = model
        return rv

    @property
    def bound(self):
        """True if the form is bound."""
        return 'model' in self.__dict__


class UUIDType(BaseType):
    """A field that stores a valid UUID value and optionally auto-populates
    empty values with new UUIDs.
    """

    def convert(self, value):
        """Make sure the value is a valid uuid representation.  See
        http://docs.python.org/library/uuid.html for accepted formats.
        """

        if not isinstance(value, (uuid.UUID,)):
            value = uuid.UUID(value)

        return value

    def to_primitive(self, value):
        """Return a JSON safe version of the UUID object.
        """
        return str(value)


class StringType(BaseType):
    """A unicode string field. Default minimum length is one. If you want to
    accept empty strings, init with `min_length` 0.

    """

    allow_casts = (int, str)

    def __init__(self, regex=None, max_length=None, min_length=1, **kwargs):
        self.regex = re.compile(regex) if regex else None
        super(StringType, self).__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length

    def convert(self, value):
        if not isinstance(value, unicode):
            if isinstance(value, self.allow_casts):
                if not isinstance(value, str):
                    value = str(value)
                value = unicode(value, 'utf-8')
            else:
                raise ValidationError(u'Illegal data value')

        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(u'String value is too long')

        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(u'String value is too short')

        if self.regex is not None and self.regex.match(value) is None:
            raise ValidationError(u'String value did not match validation regex')

        return value


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

    def convert(self, value):
        if not EmailType.EMAIL_REGEX.match(value):
            raise ValidationError('Invalid email address')
        return value


class NumberType(BaseType):
    """A number field.
    """

    def __init__(self, number_class, number_type,
                 min_value=None, max_value=None, **kwargs):
        self.number_class = number_class
        self.number_type = number_type
        self.min_value = min_value
        self.max_value = max_value
        super(NumberType, self).__init__(**kwargs)

    def convert(self, value):
        try:
            value = self.number_class(value)
        except ValueError, e:
            raise ValidationError('Not %s' % self.number_type)

        if self.min_value is not None and value < self.min_value:
            raise ValidationError('%s value below min_value: %s' % (
                self.number_type, self.min_value))

        if self.max_value is not None and value > self.max_value:
            raise ValidationError('%s value above max_value: %s' % (
                self.number_type, self.max_value))

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


class DecimalType(BaseType):
    """A fixed-point decimal number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(DecimalType, self).__init__(**kwargs)

    def to_primitive(self, value):
        return unicode(value)

    def convert(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, basestring):
                value = str(value)
            try:
                value = decimal.Decimal(value)
            except Exception:
                raise ValidationError('Could not convert to decimal')

        if self.min_value is not None and value < self.min_value:
            raise ValidationError('Decimal value below min_value: %s' % self.min_value)

        if self.max_value is not None and value > self.max_value:
            raise ValidationError('Decimal value above max_value: %s' % self.max_value)

        return value


class MD5Type(BaseType):
    """A field that validates input as resembling an MD5 hash.
    """
    hash_length = 32

    def convert(self, value):
        if len(value) != MD5Type.hash_length:
            raise ValidationError('MD5 value is wrong length')
        try:
            value = int(value, 16)
        except:
            raise ValidationError('MD5 value is not hex')

        return value


class SHA1Type(BaseType):
    """A field that validates input as resembling an SHA1 hash.
    """
    hash_length = 40

    def convert(self, value):
        if len(value) != SHA1Type.hash_length:
            raise ValidationError('SHA1 value is wrong length')
        try:
            value = int(value, 16)
        except:
            raise ValidationError('SHA1 value is not hex')

        return value


class BooleanType(BaseType):
    """A boolean field type.
    """

    TRUE = ('True', 'true', '1')
    FALSE = ('False', 'false', '0')

    def convert(self, value):
        if isinstance(value, basestring):
            if value in BooleanType.TRUE:
                value = True
            elif value in BooleanType.FALSE:
                value = False
            else:
                raise ValueError(u'Invalid boolean value')
        return value


class DateTimeType(BaseType):
    """A datetime field.
    """

    input_formats = ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S')

    def __init__(self, input_format=None, format=input_formats[0], **kwargs):
        if input_format is not None:
            if not isinstance(input_format, (tuple, list)):
                input_format = [input_format]
            self.input_formats = input_format
        self.format = format
        super(DateTimeType, self).__init__(**kwargs)

    def convert(self, value):
        """Takes a string in ISO8601 format and converts it to a Python
        datetime. http://www.w3.org/TR/NOTE-datetime

        """

        for format in self.input_formats:
            print value, format
            try:
                return datetime.datetime.strptime(value, format)
            except (ValueError, TypeError):
                continue
        raise ValidationError(u'Could not parse {}. Should be ISO8601.'.format(value))

    def to_primitive(self, value):
        if callable(self.format):
            return format(value)
        return value.strftime(self.format)


class GeoPointType(BaseType):
    """A list storing a latitude and longitude.
    """

    def convert(self, value):
        """Make sure that a geo-value is of type (x, y)
        """
        if not len(value) == 2:
            raise ValidationError('Value must be a two-dimensional point')
        if isinstance(value, dict):
            for v in value.values():
                if not isinstance(v, (float, int)):
                    raise ValidationError('Both values in point must be float or int')
        elif isinstance(value, (list, tuple)):
            if (not isinstance(value[0], (float, int)) and
                not isinstance(value[1], (float, int))):
                raise ValidationError('Both values in point must be float or int')
        else:
            raise ValidationError('GeoPointType can only accept tuples, lists, or dicts')

        return value
