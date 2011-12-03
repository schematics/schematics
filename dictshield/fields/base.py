from dictshield.base import BaseField, UUIDField, ShieldException, InvalidShield
from dictshield.datastructures import MultiValueDict
from dictshield.document import EmbeddedDocument
from ..datastructures import MultiValueDict

from operator import itemgetter
import re
import datetime
import decimal

RECURSIVE_REFERENCE_CONSTANT = 'self'


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
            raise ShieldException('String value is too long', self.field_name, value)

        if self.min_length is not None and len(value) < self.min_length:
            raise ShieldException('String value is too short', self.uniq_field, value)

        if self.regex is not None and self.regex.match(value) is None:
            message = 'String value did not match validation regex',
            raise ShieldException(message, self.uniq_field, value)

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


class EmailField(StringField):
    """A field that validates input as an E-Mail-Address.
    """

    EMAIL_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE # domain
    )

    def validate(self, value):
        if not EmailField.EMAIL_REGEX.match(value):
            raise ShieldException('Invalid email address', self.field_name,
                                  value)

    def _jsonschema_format(self):
        return 'email'

###
### Numbers
###

class JsonNumberMixin(object):
    """A mixin to support json schema validation for max, min, and type for all number fields,
    including DecimalField, which does not inherit from NumberField.
    """

    def _jsonschema_type(self):
        return 'number'

    def _jsonschema_maximum(self):
        return self.max_value

    def _jsonschema_minimum(self):
        return self.min_value


class NumberField(BaseField, JsonNumberMixin):
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

class IntField(NumberField):
    """A field that validates input as an Integer
    """

    def __init__(self, *args, **kwargs):
        super(IntField, self).__init__(number_class=int,
                                       number_type='Int',
                                       *args, **kwargs)

    def _jsonschema_type(self):
        return 'integer'

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

        
class SHA1Field(BaseField, JsonHashMixin):
    """A field that validates input as resembling an SHA1 hash.
    """
    hash_length = 40

    def validate(self, value):
        if len(value) != SHA1Field.hash_length:
            raise ShieldException('SHA1 value is wrong length', self.field_name,
                                  value)
        try:
            int(value, 16)
        except:
            raise ShieldException('SHA1 value is not hex', self.field_name,
                                  value)


###
### Native type'ish fields
###

class BooleanField(BaseField):
    """A boolean field type.
    """

    def _jsonschema_type(self):
        return 'boolean'

    def for_python(self, value):
        return bool(value)

    def validate(self, value):
        if not isinstance(value, bool):
            raise ShieldException('Not a boolean', self.field_name, value)


class DateTimeField(BaseField):
    """A datetime field.
    """

    def _jsonschema_type(self):
        return 'string'

    def _jsonschema_format(self):
        return 'date-time'

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
        iso8601 = '(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d\d\d\d\d\d))?'
        elements = re.findall(iso8601, datestring)
        date_info = elements[0]
        date_digits = [int(d) for d in date_info if d]
        value = datetime.datetime(*date_digits)
        return value

    @classmethod
    def date_to_iso8601(cls, dt):
        """Classmethod that goes the opposite direction of iso8601_to_date.
        """
        iso_dt = dt.isoformat()            
        return iso_dt

    def validate(self, value):
        if not isinstance(value, datetime.datetime):
            raise ShieldException('Not a datetime', self.field_name, value)

    def for_python(self, value):
        return value

    def for_json(self, value):
        v = DateTimeField.date_to_iso8601(value)
        return v


class ListField(BaseField):
    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the model.
    """

    def __init__(self, field, **kwargs):
        if not isinstance(field, BaseField):
            raise InvalidShield('Argument to ListField constructor must be '
                                'a valid field')
        self.field = field
        kwargs.setdefault('default', list)
        super(ListField, self).__init__(**kwargs)

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document.
        """
        if isinstance(self.field, EmbeddedDocumentField):
            list_of_docs = list()
            for doc in value:
                if isinstance(doc, dict):
                    doc_obj = self.field.document_type_obj(**doc)
                    doc = doc_obj
                list_of_docs.append(doc)
            value = list_of_docs
        instance._data[self.field_name] = value

    def _jsonschema_type(self):
        return 'array'

    def _jsonschema_items(self):
        return self.field.for_jsonschema()

    def for_python(self, value):
        if value is None:
            return list()
        return [self.field.for_python(item) for item in value]

    def for_json(self, value):
        """for_json must be careful to expand embedded documents into Python,
        not JSON.
    pp    """
        if value is None:
            return list()
        return [self.field.for_json(item) for item in value]

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (list, tuple)):
            error_msg = 'Only lists and tuples may be used in a list field'
            raise ShieldException(error_msg, self.field_name, value)

        try:
            [self.field.validate(item) for item in value]
        except Exception:
            raise ShieldException('Invalid ListField item', self.field_name,
                                  str(item))

    def lookup_member(self, member_name):
        return self.field.lookup_member(member_name)

    def _set_owner_document(self, owner_document):
        self.field.owner_document = owner_document
        self._owner_document = owner_document

    def _get_owner_document(self, owner_document):
        self._owner_document = owner_document

    owner_document = property(_get_owner_document, _set_owner_document)

class SortedListField(ListField):
    """A ListField that sorts the contents of its list before writing to
    the database in order to ensure that a sorted list is always
    retrieved.
    """

    _ordering = None

    def __init__(self, field, **kwargs):
        if 'ordering' in kwargs.keys():
            self._ordering = kwargs.pop('ordering')
        super(SortedListField, self).__init__(field, **kwargs)

    def for_json(self, value):
        if self._ordering is not None:
            return sorted([self.field.for_json(item) for item in value],
                          key=itemgetter(self._ordering))
        return sorted([self.field.for_json(item) for item in value])

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

    def lookup_member(self, member_name):
        return self.basecls(uniq_field=member_name)


class MultiValueDictField(DictField):
    def __init__(self, basecls=None, *args, **kwargs):
        self.basecls = basecls or BaseField
        if not issubclass(self.basecls, BaseField):
            raise InvalidShield('basecls is not subclass of BaseField')
        kwargs.setdefault('default', lambda: MultiValueDict())
        super(MultiValueDictField, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, MultiValueDict):
            value = MultiValueDict(value)

        super(MultiValueDictField, self).__set__(instance, value)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (dict, MultiValueDict)):
            raise ShieldException('Only dictionaries or MultiValueDict may be '
                                  'used in a DictField', self.field_name, value)

        if any(('.' in k or '$' in k) for k in value):
            raise ShieldException('Invalid dictionary key name - keys may not '
                                  'contain "." or "$" characters',
                                  self.field_name, value)

    def for_json(self, value):
        output = {}
        for key, values in value.iterlists():
            output[key] = values

        return output

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


###
### Sub structures
###

class EmbeddedDocumentField(BaseField):
    """An embedded document field. Only valid values are subclasses of
    :class:`~dictshield.EmbeddedDocument`.
    """

    def __init__(self, document_type, **kwargs):
        if not isinstance(document_type, basestring):
            if not issubclass(document_type, EmbeddedDocument):
                raise ShieldException('Invalid embedded document class '
                                      'provided to an EmbeddedDocumentField')
        self.document_type_obj = document_type
        super(EmbeddedDocumentField, self).__init__(**kwargs)

    def __set__(self, instance, value):
        if value is None:
            return
        if not isinstance(value, self.document_type):
            value = self.document_type(**value)
        instance._data[self.field_name] = value

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, basestring):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
        return self.document_type_obj

    def _jsonschema_type(self):
        return 'object'

    def for_jsonschema(self):
        fieldDict = self.for_jsonschema()
        fieldDict.update(self._data[self.field_name].for_jsonschema())
        
        return fieldDict

    def for_python(self, value):
        return value

    def for_json(self, value):
        return value.to_json(encode=False)

    def validate(self, value):
        """Make sure that the document instance is an instance of the
        EmbeddedDocument subclass provided when the document was defined.
        """
        # Using isinstance also works for subclasses of self.document
        if not isinstance(value, self.document_type):
            raise ShieldException('Invalid embedded document instance '
                                  'provided to an EmbeddedDocumentField')
        self.document_type.validate(value)

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)
