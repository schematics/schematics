from base import (BaseDocument, DictPunch, DocumentMetaclass, TopLevelDocumentMetaclass)

__all__ = ['Document', 'EmbeddedDocument', 'DictPunch']


class EmbeddedDocument(BaseDocument):
    """A :class:`~dictshield.Document` that isn't stored in its own
    collection.  :class:`~dictshield.EmbeddedDocument`\ s should be used as
    fields on :class:`~dictshield.Document`\ s through the
    :class:`~dictshield.EmbeddedDocumentField` field type.
    """

    __metaclass__ = DocumentMetaclass


class Document(BaseDocument):
    """The base class used for defining the structure and properties of
    collections of documents stored in MongoDB. Inherit from this class, and
    add fields as class attributes to define a document's structure.
    Individual documents may then be created by making instances of the
    :class:`~dictshield.Document` subclass.

    By default, the MongoDB collection used to store documents created using a
    :class:`~dictshield.Document` subclass will be the name of the subclass
    converted to lowercase. A different collection may be specified by
    providing :attr:`collection` to the :attr:`meta` dictionary in the class
    definition.

    A :class:`~dictshield.Document` subclass may be itself subclassed, to
    create a specialised version of the document that will be stored in the
    same collection. To facilitate this behaviour, `_cls` and `_types`
    fields are added to documents (hidden though the Dictshield interface
    though). To disable this behaviour and remove the dependence on the
    presence of `_cls` and `_types`, set :attr:`allow_inheritance` to
    ``False`` in the :attr:`meta` dictionary.

    A :class:`~dictshield.Document` may use a **Capped Collection** by 
    specifying :attr:`max_documents` and :attr:`max_size` in the :attr:`meta`
    dictionary. :attr:`max_documents` is the maximum number of documents that
    is allowed to be stored in the collection, and :attr:`max_size` is the 
    maximum size of the collection in bytes. If :attr:`max_size` is not 
    specified and :attr:`max_documents` is, :attr:`max_size` defaults to 
    10000000 bytes (10MB).
    """

    __metaclass__ = TopLevelDocumentMetaclass

    _internal_fields = [
        '_id', '_cls', '_types',
    ]

    _public_fields = None

    @classmethod
    def make_json_safe(cls, found_data):
        """This function removes internal fields and handles any steps
        required for making the data stucture (list, dict or Document)
        safe for transmission.
        """
        removeable_fields = set(cls._internal_fields)
        if hasattr(cls, '_private_fields'):
            priv_fields = set(cls._private_fields)
            removeable_fields = removeable_fields.union(priv_fields)
            
        def fix_dict(s):
            for f in removeable_fields:
                if s.has_key(f):
                    del s[f]
            return s
    
        def fix_engine_obj(s):
            return fix_dict(s.to_mongo())

        fix = fix_dict

        # If found_data is a list, return the results of fixing each item
        # Treats 'item' as a dict.
        # If you have a list of Documents, consider something more efficient
        if type(found_data) is list:
            return [(fix(s)) for s in found_data]
        # Clean fields for external transmission
        elif type(found_data) is dict: 
            return fix(found_data)
        # Fix Document and return cleaned dictionary
        elif isinstance(found_data, Document):
            fix = fix_engine_obj
            return fix(found_data)
        else:
            logging.debug('Called make_json_safe on incompatible obj')
            return None


    @classmethod
    def make_json_publicsafe(cls, found_data):
        """This funciton ensures found_data only contains the keys as
        required by cls.public_fields
        """
        if cls._public_fields is None:
            raise DictPunch('make_json_publicsafe called cls with no _public_fields')
        
        def fix_dict(s):
            for f in s.keys():
                if f not in cls._public_fields:
                    del s[f]
            return s
    
        if type(found_data) is list: # list of dicts
            return [(fix_dict(s)) for s in found_data]
        elif type(found_data) is dict: # single dict
            return fix_dict(found_data)    

        
    @classmethod
    def check_class_fields(cls, dict, log_fd=None):
        """This is a convenience function that loops over _fields in
        cls to validate them. If the field is not required AND not present,
        it is skipped.
    
        'not present' is defined as not having a value OR having '' (or u'')
        as a value.
        """
        # TODO Get rid of this soon
        if log_fd is None:
            write_to_log = lambda x: None
        else:
            write_to_log = log_fd.write
        
        if not hasattr(cls, '_fields'):
            raise ValueError('cls does not have _fields member')
        
        try:
            for k,v in cls._fields.items():
                # mongoengine!
                if k is 'id': 
                    k = '_id'
        
                # we don't accept forbidden_fields from users, so validation will fail
                if hasattr(cls, '_internal_fields') and k in cls._internal_fields:
                    continue
        
                # Fields are often populated with "" instead of their native types.
                # This is not ideal, but must be handled, so "" is treated as empty
                # data instead of a string value, so they are skipped
                if v.required or dict.has_key(k):
                    user_data = dict[k]
                    data_type = type(user_data)
                    if data_type is str and user_data.strip() is "": 
                        continue
                    if data_type is unicode and user_data.strip() is u'': 
                        continue
                    user_data = dict[k]
                    v.validate(user_data)
        except Exception, e:
            write_to_log('Field %s :: %s' % (k, e))
            return False
        return True
        

class MapReduceDocument(object):
    """A document returned from a map/reduce query.

    :param collection: An instance of :class:`~pymongo.Collection`
    :param key: Document/result key, often an instance of 
                :class:`~pymongo.objectid.ObjectId`. If supplied as 
                an ``ObjectId`` found in the given ``collection``, 
                the object can be accessed via the ``object`` property.
    :param value: The result(s) for this key.
    """

    def __init__(self, document, collection, key, value):
        self._document = document
        self._collection = collection
        self.key = key
        self.value = value
