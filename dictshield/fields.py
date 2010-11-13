from base import BaseField, ObjectIdField, DictPunch, get_document
from document import Document, EmbeddedDocument
from operator import itemgetter

import re
import pymongo
import pymongo.dbref
import pymongo.son
import pymongo.binary
import datetime
import decimal
import gridfs
import warnings
import types


__all__ = ['StringField', 'IntField', 'FloatField', 'LongField', 'BooleanField',
           'MD5Field', 'SHA1Field',
           'DateTimeField', 'EmbeddedDocumentField', 'ListField', 'DictField',
           'ObjectIdField', 'ReferenceField', 'DictPunch',
           'DecimalField', 'URLField', 'GenericReferenceField', 'FileField',
           'BinaryField', 'SortedListField', 'EmailField', 'GeoPointField']

RECURSIVE_REFERENCE_CONSTANT = 'self'


class StringField(BaseField):
    """A unicode string field.
    """

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super(StringField, self).__init__(**kwargs)

    def to_python(self, value):
        return unicode(value)

    def validate(self, value):
        assert isinstance(value, (str, unicode))

        if self.max_length is not None and len(value) > self.max_length:
            raise DictPunch('String value is too long')

        if self.min_length is not None and len(value) < self.min_length:
            raise DictPunch('String value is too short')

        if self.regex is not None and self.regex.match(value) is None:
            message = 'String value did not match validation regex'
            raise DictPunch(message)

    def lookup_member(self, member_name):
        return None


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
            raise DictPunch('Invalid URL: %s' % value)

        if self.verify_exists:
            import urllib2
            try:
                request = urllib2.Request(value)
                response = urllib2.urlopen(request)
            except Exception, e:
                message = 'This URL appears to be a broken link: %s' % e
                raise DictPunch(message)


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
            raise DictPunch('Invalid Mail-address: %s' % value)


class IntField(BaseField):
    """An integer field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(IntField, self).__init__(**kwargs)

    def to_python(self, value):
        return int(value)

    def validate(self, value):
        try:
            value = int(value)
        except:
            raise DictPunch('%s could not be converted to int' % value)

        if self.min_value is not None and value < self.min_value:
            raise DictPunch('Integer value is too small')

        if self.max_value is not None and value > self.max_value:
            raise DictPunch('Integer value is too large')

class LongField(BaseField):
    """A field that validates input as a Long
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(LongField, self).__init__(**kwargs)

    def to_python(self, value):
        return long(value)

    def validate(self, value):
        try:
            value = long(value)
        except:
            raise DictPunch('%s could not be converted to long' % value)

        if self.min_value is not None and value < self.min_value:
            raise DictPunch('Long value is too small')

        if self.max_value is not None and value > self.max_value:
            raise DictPunch('Long value is too large')
        

class FloatField(BaseField):
    """An floating point number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(FloatField, self).__init__(**kwargs)

    def to_python(self, value):
        return float(value)

    def validate(self, value):
        if isinstance(value, int):
            value = float(value)
        assert isinstance(value, float)

        if self.min_value is not None and value < self.min_value:
            raise DictPunch('Float value is too small')

        if self.max_value is not None and value > self.max_value:
            raise DictPunch('Float value is too large')

        
class DecimalField(BaseField):
    """A fixed-point decimal number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(DecimalField, self).__init__(**kwargs)

    def to_python(self, value):
        if not isinstance(value, basestring):
            value = unicode(value)
        return decimal.Decimal(value)

    def to_mongo(self, value):
        return unicode(value)

    def validate(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, basestring):
                value = str(value)
            try:
                value = decimal.Decimal(value)
            except Exception, exc:
                raise DictPunch('Could not convert to decimal: %s' % exc)

        if self.min_value is not None and value < self.min_value:
            raise DictPunch('Decimal value is too small')

        if self.max_value is not None and value > self.max_value:
            raise DictPunch('Decimal value is too large')


class MD5Field(BaseField):
    """A field that validates input as resembling an MD5 hash.
    """
    hash_length = 32

    def validate(self, value):
        if len(value) != MD5Field.hash_length:
            raise DictPunch('MD5 value is wrong length')
        try:
            x = int(value, 16)
        except:
            raise DictPunch('MD5 value is not hex')

        
class SHA1Field(BaseField):
    """A field that validates input as resembling an SHA1 hash.
    """
    hash_length = 40

    def validate(self, value):
        if len(value) != SHA1Field.hash_length:
            raise DictPunch('SHA1 value is wrong length')
        try:
            x = int(value, 16)
        except:
            raise DictPunch('SHA1 value is not hex')
        

class BooleanField(BaseField):
    """A boolean field type.
    """

    def to_python(self, value):
        return bool(value)

    def validate(self, value):
        assert isinstance(value, bool)


class DateTimeField(BaseField):
    """A datetime field.
    """

    def validate(self, value):
        assert isinstance(value, datetime.datetime)


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

    def to_python(self, value):
        if not isinstance(value, self.document_type):
            return self.document_type._from_son(value)
        return value

    def to_mongo(self, value):
        return self.document_type.to_mongo(value)

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


class ListField(BaseField):
    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the database.
    """

    # ListFields cannot be indexed with _types - MongoDB doesn't support this
    _index_with_types = False

    def __init__(self, field, **kwargs):
        if not isinstance(field, BaseField):
            raise DictPunch('Argument to ListField constructor must be '
                                  'a valid field')
        self.field = field
        kwargs.setdefault('default', lambda: [])
        super(ListField, self).__init__(**kwargs)

    def __get__(self, instance, owner):
        """Descriptor to automatically dereference references.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self

        if isinstance(self.field, ReferenceField):
            referenced_type = self.field.document_type
            # Get value from document instance if available 
            value_list = instance._data.get(self.name)
            if value_list:
                deref_list = []
                for value in value_list:
                    # Dereference DBRefs
                    if isinstance(value, (pymongo.dbref.DBRef)):
                        value = _get_db().dereference(value)
                        deref_list.append(referenced_type._from_son(value))
                    else:
                        deref_list.append(value)
                instance._data[self.name] = deref_list

        if isinstance(self.field, GenericReferenceField):
            value_list = instance._data.get(self.name)
            if value_list:
                deref_list = []
                for value in value_list:
                    # Dereference DBRefs
                    if isinstance(value, (dict, pymongo.son.SON)):
                        deref_list.append(self.field.dereference(value))
                    else:
                        deref_list.append(value)
                instance._data[self.name] = deref_list

        return super(ListField, self).__get__(instance, owner)

    def to_python(self, value):
        return [self.field.to_python(item) for item in value]

    def to_mongo(self, value):
        return [self.field.to_mongo(item) for item in value]

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (list, tuple)):
            raise DictPunch('Only lists and tuples may be used in a '
                                  'list field')

        try:
            [self.field.validate(item) for item in value]
        except Exception, err:
            raise DictPunch('Invalid ListField item (%s)' % str(item))

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

    def to_mongo(self, value):
        if self._ordering is not None:
            return sorted([self.field.to_mongo(item) for item in value],
                          key=itemgetter(self._ordering))
        return sorted([self.field.to_mongo(item) for item in value])


class DictField(BaseField):
    """A dictionary field that wraps a standard Python dictionary. This is
    similar to an embedded document, but the structure is not defined.
    """

    def __init__(self, basecls=None, *args, **kwargs):
        self.basecls = basecls or BaseField
        assert issubclass(self.basecls, BaseField)
        kwargs.setdefault('default', lambda: {})
        super(DictField, self).__init__(*args, **kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, dict):
            raise DictPunch('Only dictionaries may be used in a '
                                  'DictField')

        if any(('.' in k or '$' in k) for k in value):
            raise DictPunch('Invalid dictionary key name - keys may not '
                                  'contain "." or "$" characters')

    def lookup_member(self, member_name):
        return self.basecls(db_field=member_name)

class ReferenceField(BaseField):
    """A reference to a document that will be automatically dereferenced on
    access (lazily).
    """

    def __init__(self, document_type, **kwargs):
        if not isinstance(document_type, basestring):
            if not issubclass(document_type, (Document, basestring)):
                raise DictPunch('Argument to ReferenceField constructor '
                                      'must be a document class or a string')
        self.document_type_obj = document_type
        super(ReferenceField, self).__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, basestring):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def __get__(self, instance, owner):
        """Descriptor to allow lazy dereferencing.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        value = instance._data.get(self.name)
        # Dereference DBRefs
        if isinstance(value, (pymongo.dbref.DBRef)):
            value = _get_db().dereference(value)
            if value is not None:
                instance._data[self.name] = self.document_type._from_son(value)

        return super(ReferenceField, self).__get__(instance, owner)

    def to_mongo(self, document):
        id_field_name = self.document_type._meta['id_field']
        id_field = self.document_type._fields[id_field_name]

        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.id
            if id_ is None:
                raise DictPunch('You can only reference documents once '
                                      'they have been saved to the database')
        else:
            id_ = document

        id_ = id_field.to_mongo(id_)
        collection = self.document_type._meta['collection']
        return pymongo.dbref.DBRef(collection, id_)

    def validate(self, value):
        assert isinstance(value, (self.document_type, pymongo.dbref.DBRef))

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)


class GenericReferenceField(BaseField):
    """A reference to *any* :class:`~dictshield.document.Document` subclass
    that will be automatically dereferenced on access (lazily).
    """

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = instance._data.get(self.name)
        if isinstance(value, (dict, pymongo.son.SON)):
            instance._data[self.name] = self.dereference(value)

        return super(GenericReferenceField, self).__get__(instance, owner)

    def dereference(self, value):
        doc_cls = get_document(value['_cls'])
        reference = value['_ref']
        doc = _get_db().dereference(reference)
        if doc is not None:
            doc = doc_cls._from_son(doc)
        return doc

    def to_mongo(self, document):
        id_field_name = document.__class__._meta['id_field']
        id_field = document.__class__._fields[id_field_name]

        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.id
            if id_ is None:
                raise DictPunch('You can only reference documents once '
                                      'they have been saved to the database')
        else:
            id_ = document

        id_ = id_field.to_mongo(id_)
        collection = document._meta['collection']
        ref = pymongo.dbref.DBRef(collection, id_)
        return {'_cls': document.__class__.__name__, '_ref': ref}


class BinaryField(BaseField):
    """A binary data field.
    """

    def __init__(self, max_bytes=None, **kwargs):
        self.max_bytes = max_bytes
        super(BinaryField, self).__init__(**kwargs)

    def to_mongo(self, value):
        return pymongo.binary.Binary(value)

    def to_python(self, value):
        # Returns str not unicode as this is binary data
        return str(value)

    def validate(self, value):
        assert isinstance(value, str)

        if self.max_bytes is not None and len(value) > self.max_bytes:
            raise DictPunch('Binary value is too long')


class GridFSError(Exception):
    pass


class GridFSProxy(object):
    """Proxy object to handle writing and reading of files to and from GridFS
    """

    def __init__(self, grid_id=None):
        self.fs = gridfs.GridFS(_get_db())  # Filesystem instance
        self.newfile = None                 # Used for partial writes
        self.grid_id = grid_id              # Store GridFS id for file

    def __getattr__(self, name):
        obj = self.get()
        if name in dir(obj):
            return getattr(obj, name)
        raise AttributeError

    def __get__(self, instance, value):
        return self

    def get(self, id=None):
        if id:
            self.grid_id = id
        try:
            return self.fs.get(id or self.grid_id)
        except:
            # File has been deleted
            return None

    def new_file(self, **kwargs):
        self.newfile = self.fs.new_file(**kwargs)
        self.grid_id = self.newfile._id

    def put(self, file, **kwargs):
        if self.grid_id:
            raise GridFSError('This document already has a file. Either delete '
                              'it or call replace to overwrite it')
        self.grid_id = self.fs.put(file, **kwargs)

    def write(self, string):
        if self.grid_id:
            if not self.newfile:
                raise GridFSError('This document already has a file. Either '
                                  'delete it or call replace to overwrite it')
        else:
            self.new_file()
        self.newfile.write(string)

    def writelines(self, lines):
        if not self.newfile:
            self.new_file()
            self.grid_id = self.newfile._id
        self.newfile.writelines(lines) 

    def read(self):
        try:
            return self.get().read()
        except:
            return None

    def delete(self):
        # Delete file from GridFS, FileField still remains
        self.fs.delete(self.grid_id)
        self.grid_id = None

    def replace(self, file, **kwargs):
        self.delete()
        self.put(file, **kwargs)

    def close(self):
        if self.newfile:
            self.newfile.close()
        else:
            msg = "The close() method is only necessary after calling write()"
            warnings.warn(msg)


class FileField(BaseField):
    """A GridFS storage field.
    """

    def __init__(self, **kwargs):
        super(FileField, self).__init__(**kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Check if a file already exists for this model
        grid_file = instance._data.get(self.name)
        self.grid_file = grid_file
        if self.grid_file:
            return self.grid_file
        return GridFSProxy()

    def __set__(self, instance, value):
        if isinstance(value, file) or isinstance(value, str):
            # using "FileField() = file/string" notation
            grid_file = instance._data.get(self.name)
            # If a file already exists, delete it
            if grid_file:
                try:
                    grid_file.delete()
                except:
                    pass
                # Create a new file with the new data
                grid_file.put(value)
            else:
                # Create a new proxy object as we don't already have one
                instance._data[self.name] = GridFSProxy()
                instance._data[self.name].put(value)
        else:
            instance._data[self.name] = value

    def to_mongo(self, value):
        # Store the GridFS file id in MongoDB
        if isinstance(value, GridFSProxy) and value.grid_id is not None:
            return value.grid_id
        return None

    def to_python(self, value):
        if value is not None:
            return GridFSProxy(value)

    def validate(self, value):
        if value.grid_id is not None:
            assert isinstance(value, GridFSProxy)
            assert isinstance(value.grid_id, pymongo.objectid.ObjectId)


class GeoPointField(BaseField):
    """A list storing a latitude and longitude.
    """

    _geo_index = True

    def validate(self, value):
        """Make sure that a geo-value is of type (x, y)
        """
        if not isinstance(value, (list, tuple)):
            raise DictPunch('GeoPointField can only accept tuples or '
                                  'lists of (x, y)')

        if not len(value) == 2:
            raise DictPunch('Value must be a two-dimensional point.')
        if (not isinstance(value[0], (float, int)) and
            not isinstance(value[1], (float, int))):
            raise DictPunch('Both values in point must be float or int.')
