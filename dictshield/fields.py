from base import BaseField, ObjectIdField, DictPunch, InvalidShield, get_document
from document import EmbeddedDocument
from operator import itemgetter

import re
import datetime
import decimal

__all__ = ['StringField', 'IntField', 'FloatField', 'LongField', 'BooleanField',
           'DateTimeField', 'EmbeddedDocumentField', 'ListField', 'DictField',
           'ObjectIdField', 'DecimalField', 'URLField', 'MD5Field', 'SHA1Field',
           'SortedListField', 'EmailField', 'GeoPointField',
           'DictPunch', 'InvalidShield'] 

RECURSIVE_REFERENCE_CONSTANT = 'self'

class StringField(BaseField):
    """A unicode string field.
    """

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super(StringField, self).__init__(**kwargs)

    def for_python(self, value):
        return unicode(value)

    def validate(self, value):
        assert isinstance(value, (str, unicode))

        if self.max_length is not None and len(value) > self.max_length:
            raise DictPunch('String value is too long', self.field_name, value)

        if self.min_length is not None and len(value) < self.min_length:
            raise DictPunch('String value is too short', self.uniq_field, value)

        if self.regex is not None and self.regex.match(value) is None:
            message = 'String value did not match validation regex',
            raise DictPunch(message, self.uniq_field, value)

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

    def validate(self, value):
        if not URLField.URL_REGEX.match(value):
            raise DictPunch('Invalid URL', self.field_name, value)

        if self.verify_exists:
            import urllib2
            try:
                request = urllib2.Request(value)
                urllib2.urlopen(request)
            except Exception:
                message = 'URL does not exist'
                raise DictPunch(message, self.field_name, value)


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
            raise DictPunch('Invalid email address', self.field_name, value)

###
### Numbers
###

class NumberField(BaseField):
    """An integer field.
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
            raise DictPunch('Not %s' % self.number_type,
                            self.field_name, value)

        if self.min_value is not None and value < self.min_value:
            raise DictPunch('%s value below min_value: %s' % (self.number_type,
                                                              self.min_value),
                            self.field_name, value)

        if self.max_value is not None and value > self.max_value:
            raise DictPunch('%s value above max_value: %s' % (self.number_type,
                                                              self.max_value),
                            self.field_name, value)

class IntField(NumberField):
    """A field that validates input as an Integer
    """

    def __init__(self, *args, **kwargs):
        super(IntField, self).__init__(number_class=int,
                                       number_type='Int',
                                           *args, **kwargs)

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
        
class DecimalField(BaseField):
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
                raise DictPunch('Could not convert to decimal',
                                self.field_name, value)

        if self.min_value is not None and value < self.min_value:
            raise DictPunch('Decimal value below min_value: %s' % self.min_value,
                            self.field_name, value)

        if self.max_value is not None and value > self.max_value:
            raise DictPunch('Decimal value above max_value: %s' % self.max_value,
                            self.field_name, value)


###
### Hashing fields
###

class MD5Field(BaseField):
    """A field that validates input as resembling an MD5 hash.
    """
    hash_length = 32

    def validate(self, value):
        if len(value) != MD5Field.hash_length:
            raise DictPunch('MD5 value is wrong length',
                            self.field_name, value)
        try:
            int(value, 16)
        except:
            raise DictPunch('MD5 value is not hex',
                            self.field_name, value)

        
class SHA1Field(BaseField):
    """A field that validates input as resembling an SHA1 hash.
    """
    hash_length = 40

    def validate(self, value):
        if len(value) != SHA1Field.hash_length:
            raise DictPunch('SHA1 value is wrong length',
                            self.field_name, value)
        try:
            int(value, 16)
        except:
            raise DictPunch('SHA1 value is not hex',
                            self.field_name, value)

###
### Native type'ish fields
###

class BooleanField(BaseField):
    """A boolean field type.
    """

    def for_python(self, value):
        return bool(value)

    def validate(self, value):
        if not isinstance(value, bool):
            raise DictPunch('Not a boolean', self.field_name, value)

class DateTimeField(BaseField):
    """A datetime field.
    """

    def validate(self, value):
        if not isinstance(value, datetime.datetime):
            raise DictPunch('Not a datetime', self.field_name, value)

class ListField(BaseField):
    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the model.
    """

    def __init__(self, field, **kwargs):
        if not isinstance(field, BaseField):
            raise InvalidShield('Argument to ListField constructor must be '
                                'a valid field')
        self.field = field
        kwargs.setdefault('default', lambda: [])
        super(ListField, self).__init__(**kwargs)

    def for_python(self, value):
        return [self.field.for_python(item) for item in value]

    def for_json(self, value):
        return [self.field.for_json(item) for item in value]

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (list, tuple)):
            raise DictPunch('Only lists and tuples may be used in a '
                            'list field', self.field_name, value)

        try:
            [self.field.validate(item) for item in value]
        except Exception:
            raise DictPunch('Invalid ListField item',
                            self.field_name, str(item))

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
            raise DictPunch('Only dictionaries may be used in a '
                            'DictField', self.field_name, value)

        if any(('.' in k or '$' in k) for k in value):
            raise DictPunch('Invalid dictionary key name - keys may not '
                            'contain "." or "$" characters',
                            self.field_name, value)

    def lookup_member(self, member_name):
        return self.basecls(uniq_field=member_name)

class GeoPointField(BaseField):
    """A list storing a latitude and longitude.
    """

    def validate(self, value):
        """Make sure that a geo-value is of type (x, y)
        """
        if not isinstance(value, (list, tuple)):
            raise DictPunch('GeoPointField can only accept tuples or '
                            'lists of (x, y)', self.field_name, value)

        if not len(value) == 2:
            raise DictPunch('Value must be a two-dimensional point',
                            self.field_name, value)
        if (not isinstance(value[0], (float, int)) and
            not isinstance(value[1], (float, int))):
            raise DictPunch('Both values in point must be float or int',
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
                raise DictPunch('Invalid embedded document class '
                                      'provided to an EmbeddedDocumentField')
        self.document_type_obj = document_type
        super(EmbeddedDocumentField, self).__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, basestring):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def for_python(self, value):
        if not isinstance(value, self.document_type):
            return self.document_type._from_son(value)
        return value

    def for_json(self, value):
        return self.document_type.for_json(value)

    def validate(self, value):
        """Make sure that the document instance is an instance of the
        EmbeddedDocument subclass provided when the document was defined.
        """
        # Using isinstance also works for subclasses of self.document
        if not isinstance(value, self.document_type):
            raise DictPunch('Invalid embedded document instance '
                                  'provided to an EmbeddedDocumentField')
        self.document_type.validate(value)

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)
