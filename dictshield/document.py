import copy

from dictshield.base import ShieldException, json

__all__ = ['DocumentMetaclass', 'TopLevelDocumentMetaclass', 'BaseDocument', 'Document', 'EmbeddedDocument', 'ShieldException']

from dictshield.fields import (DictFieldNotFound,
                               dictshield_fields,
                               BaseField,
                               UUIDField,
                               )

schema_kwargs_to_dictshield  = {
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'pattern' : 'regex',
    'minimum': 'min_value',
    'maximum': 'max_value',
    }


###
### Metaclass design
###
 
class DocumentMetaclass(type):
    """Metaclass for all documents.
    """

    def __new__(cls, name, bases, attrs):
        metaclass = attrs.get('__metaclass__')
        super_new = super(DocumentMetaclass, cls).__new__
        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(cls, name, bases, attrs)

        doc_fields = {}
        class_name = [name]
        superclasses = {}
        simple_class = True
        for base in bases:
            # Include all fields present in superclasses
            if hasattr(base, '_fields'):
                doc_fields.update(base._fields)
                class_name.append(base._class_name)
                # Get superclasses from superclass
                superclasses[base._class_name] = base
                superclasses.update(base._superclasses)

            if hasattr(base, '_meta'):
                # Ensure that the Document class may be subclassed - 
                # inheritance may be disabled to remove dependency on 
                # additional fields _cls and _types
                if base._meta.get('allow_inheritance', True) == False:
                    raise ValueError('Document %s may not be subclassed' %
                                     base.__name__)
                else:
                    simple_class = False

                if base._meta.get('mixin', False) == True:
                    # A dictshield mixin means it adds fields with no effet
                    # on class hierarchy
                    class_name.pop()
                    del superclasses[base._class_name]


        meta = attrs.get('_meta', attrs.get('meta', {}))

        if 'allow_inheritance' not in meta:
            meta['allow_inheritance'] = True

        # Only simple classes - direct subclasses of Document - may set
        # allow_inheritance to False
        if not simple_class and not meta['allow_inheritance']:
            raise ValueError('Only direct subclasses of Document may set '
                             '"allow_inheritance" to False')
        attrs['_meta'] = meta

        attrs['_class_name'] = '.'.join(reversed(class_name))
        attrs['_superclasses'] = superclasses        

        # Add the document's fields to the _fields attribute
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, "__class__") and \
               issubclass(attr_value.__class__, BaseField):
                attr_value.field_name = attr_name
                if not attr_value.uniq_field:
                    attr_value.uniq_field = attr_name
                doc_fields[attr_name] = attr_value
        attrs['_fields'] = doc_fields

        new_class = super_new(cls, name, bases, attrs)
        for field in new_class._fields.values():
            field.owner_document = new_class

        return new_class

    def add_to_class(self, name, value):
        setattr(self, name, value)

class TopLevelDocumentMetaclass(DocumentMetaclass):
    """Metaclass for top-level documents (i.e. documents that have their own
    collection in the database.
    """

    def __new__(cls, name, bases, attrs):
        super_new = super(TopLevelDocumentMetaclass, cls).__new__
        # Classes defined in this package are abstract and should not have 
        # their own metadata with DB collection, etc.
        # __metaclass__ is only set on the class with the __metaclass__ 
        # attribute (i.e. it is not set on subclasses). This differentiates
        # 'real' documents from the 'Document' class
        if attrs.get('__metaclass__') == TopLevelDocumentMetaclass:
            return super_new(cls, name, bases, attrs)

        collection = name.lower()
        id_field = None

        base_meta = {}

        # Subclassed documents inherit collection from superclass
        for base in bases:
            if hasattr(base, '_meta'):
                if 'collection' in base._meta:
                    collection = base._meta['collection']
                id_field = id_field or base._meta.get('id_field')

        meta = {
            'collection': collection,
            'max_documents': None,
            'max_size': None,
            'id_field': id_field,            
        }
        meta.update(base_meta)

        # Apply document-defined meta options
        meta.update(attrs.get('meta', {}))
        attrs['_meta'] = meta

        # Set up collection manager, needs the class to have fields so use
        # DocumentMetaclass before instantiating CollectionManager object
        new_class = super_new(cls, name, bases, attrs)

        for field_name, field in new_class._fields.items():
            # Check for custom id key
            if field.id_field:
                current_id = new_class._meta['id_field']
                if current_id and current_id != field_name:
                    raise ValueError('Cannot override id_field')

                new_class._meta['id_field'] = field_name
                # Make 'Document.id' an alias to the real primary key field
                new_class.id = field

        if not new_class._meta['id_field']:
            new_class._meta['id_field'] = 'id'
            new_class._fields['id'] = UUIDField(uniq_field='_id')
            new_class.id = new_class._fields['id']

        return new_class

    def __str__(self):
        if hasattr(self, '__unicode__'):
            return unicode(self).encode('utf-8')
        return '%s object' % self.__class__.__name__


    ###
    ### Instance Serialization
    ###

    def _to_fields(self, field_converter):
        """Returns a Python dictionary representing the Document's metastructure
        and values.
        """
        data = {}

        # First map the subclasses of BaseField
        for field_name, field in self._fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
                data[field.uniq_field] = field_converter(field, value)
                
        # Only add _cls and _types if allow_inheritance is not False
        if not (hasattr(self, '_meta') and
                self._meta.get('allow_inheritance', True) == False):
            data['_cls'] = self._class_name
            data['_types'] = self._superclasses.keys() + [self._class_name]
            
        if data.has_key('_id') and not data['_id']:
            del data['_id']
            
        return data

    def to_python(self):
        """Returns a Python dictionary representing the Document's metastructure
        and values.
        """
        fun = lambda f, v: f.for_python(v)
        data = self._to_fields(fun)
        return data

    def to_json(self, encode=True):
        """Return data prepared for JSON. By default, it returns a JSON encoded
        string, but disabling the encoding to prevent double encoding with
        embedded documents.
        """
        fun = lambda f, v: f.for_json(v)
        data = self._to_fields(fun)
        if encode:
            return json.dumps(data)
        else:
            return data


class QueryableTopLevelDocumentMetaclass(DocumentMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(QueryableTopLevelDocumentMetaclass, cls).__new__(cls, name, bases, attrs)
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, 'set_document_class'):
                if isinstance(attr_value, type):
                    attr_value = attr_value()
                attr_value.set_document_class(new_class)

        return new_class

###
### Document structures
###

class BaseDocumentManager(object):
    '''A base class which can be extended to add querying functionality to
    documents.
    '''

    def set_document_class(self, document_class):
        self.document_class = document_class


class BaseDocument(object):

    def __init__(self, **values):
        self._data = {}

        # Assign default values to instance
        for attr_name, attr_value in self._fields.items():
            # Use default value if present
            value = getattr(self, attr_name, None)
            setattr(self, attr_name, value)

        # Assign initial values to instance
        for attr_name,attr_value in values.items():
            try:
                if attr_name == '_id':
                    attr_name = 'id'
                setattr(self, attr_name, attr_value)
            # Put a diaper on the keys that don't belong and send 'em home
            except AttributeError:
                pass

    def validate(self):
        """Ensure that all fields' values are valid and that required fields
        are present.
        """
        # Get a list of tuples of field names and their current values
        fields = [(field, getattr(self, name)) 
                  for name, field in self._fields.items()]

        # Ensure that each field is matched to a valid value
        for field, value in fields:
            if value is not None and value != '': # treat empty strings is nonexistent
                try:
                    field._validate(value)
                except (ValueError, AttributeError, AssertionError):
                    raise ShieldException('Invalid value', field.field_name,
                                          value)
            elif field.required:
                raise ShieldException('Required field missing', field.field_name,
                                      value)

    @classmethod
    def _get_subclasses(cls):
        """Return a dictionary of all subclasses (found recursively).
        """
        try:
            subclasses = cls.__subclasses__()
        except:
            subclasses = cls.__subclasses__(cls)

        all_subclasses = {}
        for subclass in subclasses:
            all_subclasses[subclass._class_name] = subclass
            all_subclasses.update(subclass._get_subclasses())
        return all_subclasses

    def __iter__(self):
        return iter(self._fields)

    def __getitem__(self, name):
        """Dictionary-style field access, return a field's value if present.
        """
        try:
            if name in self._fields:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        """Dictionary-style field access, set a field's value.
        """
        # Ensure that the field exists before settings its value
        if name not in self._fields:
            raise KeyError(name)
        return setattr(self, name, value)

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return u"<%s: %s>" % (self.__class__.__name__, u)

    def __str__(self):
        if hasattr(self, '__unicode__'):
            return unicode(self).encode('utf-8')
        return '%s object' % self.__class__.__name__

    ###
    ### Class serialization
    ###

    @classmethod
    def for_jsonschema(cls):
        """Returns a representation of this DictShield class as a JSON schema,
        but not yet serialized to JSON. If certain fields are marked public,
        only those fields will be represented in the schema.

        Certain DictShield fields do not map precisely to JSON schema types or
        formats.
        """

        # Place all fields in the schema unless public ones are specified.
        if cls._public_fields is None:
            field_names = cls._fields.keys()
        else:
            field_names = copy.copy(cls._public_fields)
        
        properties = {}        
        if 'id' in field_names:
            field_names.remove('id')
            properties['_id'] = cls._fields[ 'id' ].for_jsonschema()

        for name in field_names:
            properties[ name ] = cls._fields[ name ].for_jsonschema()
        
        return {
            'type'       : 'object',
            'title'      : cls.__name__,
            'properties' : properties
            }

    @classmethod
    def to_jsonschema(cls):
        """Returns a representation of this DictShield class as a JSON schema.
        If certain fields are marked public, only those fields will be represented
        in the schema.

        Certain DictShield fields do not map precisely to JSON schema types or
        formats.
        """
        return json.dumps(cls.for_jsonschema())

    ###
    ### Instance Serialization
    ###

    def _to_fields(self, field_converter):
        """Returns a Python dictionary representing the Document's metastructure
        and values.
        """
        data = {}

        # First map the subclasses of BaseField
        for field_name, field in self._fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
                data[field.uniq_field] = field_converter(field, value)

        # Only add _cls and _types if allow_inheritance is not False
        if not (hasattr(self, '_meta') and
                self._meta.get('allow_inheritance', True) == False):
            data['_cls'] = self._class_name
            data['_types'] = self._superclasses.keys() + [self._class_name]
            
        if data.has_key('_id') and not data['_id']:
            del data['_id']
            
        return data

    def to_python(self):
        """Returns a Python dictionary representing the Document's metastructure
        and values.
        """
        fun = lambda f, v: f.for_python(v)
        data = self._to_fields(fun)
        return data

    def to_json(self, encode=True):
        """Return data prepared for JSON. By default, it returns a JSON encoded
        string, but disabling the encoding to prevent double encoding with
        embedded documents.
        """
        fun = lambda f, v: f.for_json(v)
        data = self._to_fields(fun)
        if encode:
            return json.dumps(data)
        else:
            return data

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            keys = self._fields
            if not hasattr(other, '_id'):
                keys.pop("_id", None)
            for key in keys:
                if self[key] != other[key]:
                    return False
            return True
        return False


    @classmethod
    def from_jsonschema(cls, schema):
        """Generate a dictshield Document class from a JSON schema.  The JSON schema's
        title field will be the name of the class.  You must specify a title and at
        least one property or there will be an AttributeError.
        """
        os = schema
        schema = copy.deepcopy(schema) # this is a desctructive op. This should be only strings/dicts, so this should be cheap
        if schema.get('title', False):
            class_name = schema['title']
        else:
            import pdb
            pdb.set_trace()
            raise AttributeError('Your JSON schema must specify a title to be the Document class name')

        if schema.has_key('description'):
            doc = schema['description'] #TODO: figure out way to put this in to resulting obj

        if schema.has_key('properties'):
            dictfields = {}
            for field_name, schema_field in schema['properties'].iteritems():
                if field_name == "_id":
                    field_name = "id"
                dictfields[field_name] = cls.map_jsonschema_field_to_dictshield(schema_field)
            return type(class_name,
                    (cls,),
                    dictfields,
                    )
        else:
            raise AttributeError('Your JSON schema must have at least one property')

    @classmethod
    def map_jsonschema_field_to_dictshield(cls, schema_field, field_name=None):
        #get the kind of field this is
        if not 'type' in schema_field: 
            return #not data, so ignore
        tipe = schema_field.pop('type')
        fmt = schema_field.pop('format', None)

        dictshield_field_type = dictshield_fields.get((tipe, fmt,), None)
        if not dictshield_field_type:
            raise DictFieldNotFound

        kwargs =  {}
        if tipe == 'array': #list types
            items = schema_field.pop('items', None)
            if items == None: #any possible item isn't allowed by listfield
                raise NotImplementedError
            elif isinstance(items, dict): #list of a single type
                items = [items]
            kwargs['fields'] = [cls.map_jsonschema_field_to_dictshield(item) for item in items]
            

        if tipe == "object": #embedded objects
            #schema_field['title'] = field_name
            kwargs['document_type'] = EmbeddedDocument.from_jsonschema(schema_field)
            schema_field.pop('properties')

        schema_field.pop('title', None) # make sure this isn't in here


        for kwarg_name, v in schema_field.items():
            if kwarg_name in schema_kwargs_to_dictshield:
                kwarg_name = schema_kwargs_to_dictshield[kwarg_name]
            kwargs[kwarg_name] = v
        return dictshield_field_type(**kwargs)
        

class SafeableMixin:
    """A `SafeableMixin` is used to add unix style permissions to fields in a
    `Document`. It creates this by using a black list and a white list in the
    form of three lists called `_internal_fields`, `_private_fields` and
    `_public_fields`.

    `_internal_fields` is used to list fields which are private and not meant
    to leave the system. This generally consists of `_id`, `_cls` and `_types`
    but a user can extend the list of internal fields by defining a class level
    list field called _private_fields. Any field listed here will be removed
    with any call to a make*safe method.

    `make_json_ownersafe` is defined to remove the keys listed in both
    fields, making it our blacklist.

    If `_public_fields` is defined, `make_json_publicsafe` can be used to create
    a structure made of only the fields in this list, making it our white list.
    """
    _internal_fields = [
        '_id', 'id', '_cls', '_types',
    ]

    _public_fields = None

    @classmethod
    def _get_internal_fields(cls):
        """Helper function that determines the union of :attr:`_internal_fields`
        and :attr:`_private_fields`, else returns just :attr:`_internal_fields`.
        """
        internal_fields = set(cls._internal_fields)
        if hasattr(cls, '_private_fields'):
            private_fields = set(cls._private_fields)
            internal_fields = internal_fields.union(private_fields)
        return internal_fields

    @classmethod
    def _safe_data_from_input(cls, fun, data):
        """Helper function for handling variable inputs to make_json_*safe
        functions.

        Returns a safe doc if given one element.

        Returns an list if given a list. Can handle a list of dicts or
        list of docs.
        """
        # single cls instance
        if isinstance(data, cls):
            return fun(data.to_python())

        # single dict instance
        elif isinstance(data, dict):
            return fun(data)

        # list of cls instances or list of dicts
        elif isinstance(data, list):
            if len(data) < 1:
                return list()
            elif isinstance(data[0], dict):
                pass # written for clarity
            elif isinstance(data[0], cls):
                data = [d.to_python() for d in data]
            return map(fun, data)

    @classmethod
    def make_ownersafe(cls, doc_dict_or_dicts):
        """This function removes internal fields and handles any steps
        required for making the data stucture (list, dict or Document)
        safe for transmission to the owner of the data.

        It also knows to check for EmbeddedDocument's which contain their own
        private/public data.

        It attempts to handle multiple inputs types to avoid as many
        translation steps as possible.
        """
        internal_fields = cls._get_internal_fields()

        # This `handle_doc` implementation behaves as a blacklist
        containers = (list, dict)
        def handle_doc(doc_dict):
            for k,v in doc_dict.items():
                if k in internal_fields:
                    del doc_dict[k]
                elif isinstance(v, EmbeddedDocument):
                    doc_dict[k] = v.make_ownersafe(v.to_python())
                elif isinstance(v, containers) and len(v) > 0:
                    if isinstance(v[0], EmbeddedDocument):
                        doc_dict[k] = [doc.make_ownersafe(doc.to_python())
                                       for doc in v]
            return doc_dict

        trimmed = cls._safe_data_from_input(handle_doc, doc_dict_or_dicts)
        return trimmed

    @classmethod
    def make_json_ownersafe(cls, doc_dict_or_dicts):
        """Trims the object using make_ownersafe and dumps to JSON
        """
        trimmed = cls.make_ownersafe(doc_dict_or_dicts)
        return json.dumps(trimmed)

    @classmethod
    def make_publicsafe(cls, doc_dict_or_dicts):
        """This funciton ensures found_data only contains the keys as
        listed in cls._public_fields.

        It also knows to check for EmbeddedDocument's which contain their own
        private/public data.

        This function can be safely called without calling make_json_ownersafe
        first because it treats cls._public_fields as a whitelist and
        removes anything not listed.
        """
        if cls._public_fields is None:
            return cls.make_ownersafe(doc_dict_or_dicts)

        # This `handle_doc` implementation behaves as a whitelist
        containers = (list, dict)
        def handle_doc(doc_dict):
            for k,v in doc_dict.items():
                if k not in cls._public_fields:
                    del doc_dict[k]
                elif isinstance(v, EmbeddedDocument):
                    doc_dict[k] = v.make_publicsafe(v.to_python())
                elif isinstance(v, containers) and len(v) > 0:
                    if isinstance(v[0], EmbeddedDocument):
                        doc_dict[k] = [doc.make_publicsafe(doc.to_python())
                                       for doc in v]
            return doc_dict

        trimmed = cls._safe_data_from_input(handle_doc, doc_dict_or_dicts)
        return trimmed

    @classmethod
    def make_json_publicsafe(cls, doc_dict_or_dicts):
        """Trims the object using make_publicsafe and dumps to JSON
        """
        trimmed = cls.make_publicsafe(doc_dict_or_dicts)
        return json.dumps(trimmed)

    @classmethod
    def _gen_handle_exception(cls, validate_all, exception_list):
        """Generates a function for either raising exceptions or collecting them
        in a list.
        """
        if validate_all:
            def handle_exception(e):
                exception_list.append(e)
        else:
            def handle_exception(e):
                raise e

        return handle_exception

    @classmethod
    def _gen_handle_class_field(cls, delete_rogues, field_list):
        """Generates a function that either accumulates observed fields or
        makes no attempt to collect them.

        The case where nothing accumulates is to prevent growing data structures
        unnecessarily.
        """
        if delete_rogues:
            def handle_class_field(cf):
                field_list.append(cf)
        else:
            def handle_class_field(cf):
                pass

        return handle_class_field

    @classmethod
    def _validate_helper(cls, field_inspector, values, validate_all=False,
                         delete_rogues=True):
        """This is a convenience function that loops over the given values
        and attempts to validate them against the class definition. It only
        validates the data in values and does not guarantee a complete document
        is present.

        'not present' is defined as not having a value OR having '' (or u'')
        as a value.
        """
        if not hasattr(cls, '_fields'):
            raise ValueError('cls is not a Document instance')

        internal_fields = cls._get_internal_fields()

        # Create function for handling exceptions
        exceptions = list()
        handle_exception = cls._gen_handle_exception(validate_all, exceptions)

        # Create function for handling a flock of frakkin palins (rogue fields)
        data_fields = set(values.keys())
        class_fields = list()
        handle_class_field = cls._gen_handle_class_field(delete_rogues,
                                                         class_fields)

        # Loop across fields present in model
        for k,v in cls._fields.items():

            # handle common id name
            if k is 'id': k = '_id'

            handle_class_field(k)

            # we don't accept internal fields from users
            if k in internal_fields and k in values:
                value_is_default = (values[k] is v.default)
                if not value_is_default:
                    e = ShieldException('Overwrite of internal fields attempted', k, v)
                    handle_exception(e)
                    continue

            if field_inspector(k, v):
                datum = values[k]
                # if datum is None, skip
                if datum is None:
                    continue
                # treat empty strings as empty values and skip
                if isinstance(datum, (str, unicode)) and len(datum.strip()) == 0:
                    continue
                try:
                    v.validate(datum)
                except ShieldException, e:
                    handle_exception(e)

        # Remove rogue fields
        if len(class_fields) > 0: # if accumulation is not disabled
            palins = data_fields - set(class_fields)
            for rogue_field in palins:
                del values[rogue_field]

        # Reaches here only if exceptions are aggregated or validation passed
        if validate_all:
            return exceptions
        else:
            return True


    @classmethod
    def validate_class_fields(cls, values, validate_all=False):
        """This is a convenience function that loops over _fields in
        cls to validate them. If the field is not required AND not present,
        it is skipped.
        """
        fun = lambda k,v: v.required or k in values
        return cls._validate_helper(fun, values, validate_all=validate_all)

    @classmethod
    def validate_class_partial(cls, values, validate_all=False):
        """This is a convenience function that loops over _fields in
        cls to validate them. This function is a partial validatation
        only, meaning the values given and does not check if the document
        is complete.
        """
        fun = lambda k,v: k in values
        return cls._validate_helper(fun, values, validate_all=validate_all)


class EmbeddedDocument(BaseDocument, SafeableMixin):
    """A :class:`~dictshield.Document` that isn't stored in its own
    collection.  :class:`~dictshield.EmbeddedDocument`\ s should be used as
    fields on :class:`~dictshield.Document`\ s through the
    :class:`~dictshield.EmbeddedDocumentField` field type.
    """

    __metaclass__ = DocumentMetaclass


class Document(BaseDocument, SafeableMixin):
    """The base class used for defining the structure and properties of
    collections of documents modeled in DictShield. Inherit from this class,
    and add fields as class attributes to define a document's structure.
    Individual documents may then be created by making instances of the
    :class:`~dictshield.Document` subclass.

    A :class:`~dictshield.Document` subclass may be itself subclassed, to
    create a specialised version of the document that can be stored in the
    same collection. To facilitate this behaviour, `_cls` and `_types`
    fields are added to documents to specify the install class and the types
    in the Document class hierarchy. To disable this behaviour and remove
    the dependence on the presence of `_cls` and `_types`, set
    :attr:`allow_inheritance` to ``False`` in the :attr:`meta` dictionary.
    """

    __metaclass__ = TopLevelDocumentMetaclass


class QueryableDocument(BaseDocument, SafeableMixin):

    __metaclass__ = QueryableTopLevelDocumentMetaclass
