import inspect
import copy

from dictshield.base import ShieldException, json

__all__ = ['DocumentMetaclass', 'TopLevelDocumentMetaclass', 'BaseDocument',
           'Document', 'EmbeddedDocument', 'ShieldException']

from dictshield.fields import (DictFieldNotFound,
                               dictshield_fields,
                               BaseField,
                               UUIDField)

schema_kwargs_to_dictshield = {
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'pattern': 'regex',
    'minimum': 'min_value',
    'maximum': 'max_value',
}


###
### Options Models
###

class DocumentOptions(object):
    """This class is a container for all metaclass configuration options. The
    `__init__` method will set the default values for attributes and then
    attempt to map any keyword arguments to attributes of the same name. If an
    attribute is passed as a keyword but the attribute is not given a default
    value prior to called `_parse_kwargs_dict`, it will be ignored.
    """
    def __init__(self, **kwargs):
        self.mixin = False
        ### Relies on attr names above
        self._parse_kwargs_dict(kwargs)

    def _parse_kwargs_dict(self, kwargs_dict):
        """This function receives the dictionary with keyword arguments in
        `__init__` and maps them to existing attributes on the class.
        """
        for k, v in kwargs_dict.items():
            if hasattr(self, k):
                setattr(self, k, v)


class TopLevelDocumentOptions(DocumentOptions):
    """Extends `DocumentOptions` to add configuration values for
    TopLevelDocument instances.
    """
    def __init__(self, **kwargs):
        self.id_field = UUIDField
        self.id_options = {'uniq_field': 'id'}
        self.bucket = None
        ### The call to super should be last
        super(TopLevelDocumentOptions, self).__init__(**kwargs)


###
### Options Parsers
###

def _parse_meta_config(attrs, options_class):
    """Parses the Meta object on the class and translates it into an Option
    instance.
    """
    valid_attrs = dict()
    if 'Meta' in attrs:
        meta = attrs['Meta']
        for attr_name, attr_value in inspect.getmembers(meta):
            if not attr_name.startswith('_'):
                valid_attrs[attr_name] = attr_value
    oc = options_class(**valid_attrs)
    return oc


def _gen_options(klass, attrs):
    """Processes the attributes and class parameters to generate the correct
    options structure.

    Defaults to `DocumentOptions` but it's ideal to define `__optionsclass_` on the
    Document's metaclass.
    """
    ### Parse Meta
    options_class = DocumentOptions
    if hasattr(klass, '__optionsclass__'):
        options_class = klass.__optionsclass__
    options = _parse_meta_config(attrs, options_class)
    return options


###
### Metaclass design
###

class DocumentMetaclass(type):
    """Metaclass for all documents. Additional meta-functionality can be
    constructed via subclassing this document.
    """
    def __new__(cls, name, bases, attrs):
        """Processes a configuration of a Document type into a class.
        """
        ### Gen a class instance
        klass = type.__new__(cls, name, bases, attrs)

        metaclass = attrs.get('__metaclass__')
        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return klass

        ### Parse metaclass config into options structure
        options = _gen_options(klass, attrs)
        setattr(klass, '_options', options)
        if hasattr(klass, 'Meta'):
            delattr(klass, 'Meta')

        ### Fields for collecting structure information
        doc_fields = {}
        class_name = [name]
        superclasses = {}
        simple_class = True

        ###
        ### Handle Base Classes
        ###
        
        for base in bases:
            ### Configure `_fields` list
            if hasattr(base, '_fields'):
                doc_fields.update(base._fields)
                class_name.append(base._class_name)
                superclasses[base._class_name] = base
                superclasses.update(base._superclasses)

                ### Handle class options
                if hasattr(base, '_options'):
                    ### Mixin
                    if base._options.mixin == True:
                        class_name.pop()
                        del superclasses[base._class_name]

        ###
        ### Construct The Class Instance
        ###

        ### Collect field info
        for attr_name, attr_value in attrs.items():
            has_class = hasattr(attr_value, "__class__")
            if has_class and issubclass(attr_value.__class__, BaseField):
                attr_value.field_name = attr_name
                if not attr_value.uniq_field:
                    attr_value.uniq_field = attr_name
                doc_fields[attr_name] = attr_value

        ### Attach collected data to klass
        setattr(klass, '_fields', doc_fields)
        setattr(klass, '_class_name', '.'.join(reversed(class_name)))
        setattr(klass, '_superclasses', superclasses)

        ### Set owner in field instances to klass
        for field in klass._fields.values():
            field.owner_document = klass

        ### Fin.
        return klass


class TopLevelDocumentMetaclass(DocumentMetaclass):
    """Metaclass for top-level documents. A Top-level document in DictShield
    represents the kind of structure that will be stored in a database. The
    `TopLevelDocumentMetaclass` is therefore responsible for the kind of
    attributes that make a document saveable, like an id field.
    """

    def __new__(cls, name, bases, attrs):
        ### Gen a class instance
        super_new = super(TopLevelDocumentMetaclass, cls).__new__
        klass = super_new(cls, name, bases, attrs)
    
        if attrs.get('__metaclass__') == TopLevelDocumentMetaclass:
            return klass

        for base in bases:
            ### Configure `_fields` list
            if hasattr(base, '_options'):

                if hasattr(base._options, 'id_field'):
                    ### Carry over id field data
                    klass._options.id_field = base._options.id_field

        for field_name, field in klass._fields.items():
            # Check for custom id key
            if hasattr(field, 'id_field') and field.id_field:
                current_id = klass._options.id_field
                if current_id and current_id != field_name:
                    raise ValueError('Cannot override id_field')

                klass._options.id_field = field
                # Make 'Document.id' an alias to the real primary key field
                klass.id = field(uniq_field='id')

        id_options = {'uniq_field': '_id'}
        if hasattr(klass._options, 'id_options'):
            id_options.update(klass._options.id_options)

        ### Create ID field system
        if hasattr(klass._options, 'id_field'):
            id_field = klass._options.id_field
            klass._fields['id'] = id_field(**id_options)
            #klass.id = id_field(**id_options)
            klass.id = id_field(**id_options)
        else:
            id_field = UUIDField

        return klass
        
    def __str__(self):
        if hasattr(self, '__unicode__'):
            return unicode(self).encode('utf-8')
        return '%s object' % self.__class__.__name__

    ###
    ### Instance Serialization
    ###

    def _to_fields(self, field_converter):
        """Returns a Python dictionary representing the Document's
        metastructure and values.
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

        if 'id' in data and not data['_id']:
            del data['_id']

        return data

    def to_python(self):
        """Returns a Python dictionary representing the Document's
        metastructure and values.
        """
        fun = lambda f, v: f.for_python(v)
        data = self._to_fields(fun)
        return data

    def to_json(self, encode=True, sort_keys=False):
        """Return data prepared for JSON. By default, it returns a JSON encoded
        string, but disabling the encoding to prevent double encoding with
        embedded documents.
        """
        fun = lambda f, v: f.for_json(v)
        data = self._to_fields(fun)
        if encode:
            return json.dumps(data, sort_keys=sort_keys)
        else:
            return data


###
### Document structures
###

class BaseDocument(object):

    def __init__(self, **values):
        self._data = {}
        minimized_field_map = {}

        # Assign default values to instance
        for attr_name, attr_value in self._fields.items():
            # Use default value if present
            value = getattr(self, attr_name, None)
            setattr(self, attr_name, value)
            if attr_value.minimized_field_name:
                field_name = attr_value.minimized_field_name
                minimized_field_map[field_name] = attr_value.uniq_field

        # Assign initial values to instance
        for attr_name, attr_value in values.items():
            try:
                if attr_name == '_id':
                    attr_name = 'id'
                setattr(self, attr_name, attr_value)
                if attr_name in minimized_field_map:
                    setattr(self, minimized_field_map[attr_name], attr_value)
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
            # treat empty strings is nonexistent
            if value is not None and value != '':
                try:
                    return field._validate(value)
                except (ValueError, AttributeError, AssertionError):
                    raise ShieldException('Invalid value', field.field_name,
                                          value)
            elif field.required:
                raise ShieldException('Required field missing',
                                      field.field_name,
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
            properties['_id'] = cls._fields['id'].for_jsonschema()

        for name in field_names:
            properties[name] = cls._fields[name].for_jsonschema()

        return {
            'type': 'object',
            'title': cls.__name__,
            'properties': properties
        }

    @classmethod
    def to_jsonschema(cls):
        """Returns a representation of this DictShield class as a JSON schema.
        If certain fields are marked public, only those fields will be
        represented in the schema.

        Certain DictShield fields do not map precisely to JSON schema types or
        formats.
        """
        return json.dumps(cls.for_jsonschema())

    ###
    ### Instance Serialization
    ###

    def _to_fields(self, field_converter):
        """Returns a Python dictionary representing the Document's
        metastructure and values.
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

        if '_id' in data and not data['_id']:
            del data['_id']

        return data

    def to_python(self):
        """Returns a Python dictionary representing the Document's
        metastructure and values.
        """
        fun = lambda f, v: f.for_python(v)
        data = self._to_fields(fun)
        return data

    def to_json(self, encode=True, sort_keys=False):
        """Return data prepared for JSON. By default, it returns a JSON encoded
        string, but disabling the encoding to prevent double encoding with
        embedded documents.
        """
        fun = lambda f, v: f.for_json(v)
        data = self._to_fields(fun)
        if encode:
            return json.dumps(data, sort_keys=sort_keys)
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
        """Generate a dictshield Document class from a JSON schema.  The JSON
        schema's title field will be the name of the class.  You must specify a
        title and at least one property or there will be an AttributeError.
        """
        os = schema
        # this is a desctructive op. This should be only strings/dicts, so this
        # should be cheap
        schema = copy.deepcopy(schema)
        if schema.get('title', False):
            class_name = schema['title']
        else:
            raise AttributeError('JSON Schema missing Document title')

        if 'description' in schema:
            # TODO figure out way to put this in to resulting obj
            doc = schema['description']

        if 'properties' in schema:
            dictfields = {}
            for field_name, schema_field in schema['properties'].iteritems():
                if field_name == "_id":
                    field_name = "id"
                field = cls.map_jsonschema_field_to_dictshield(schema_field)
                dictfields[field_name] = field
            return type(class_name, (cls,), dictfields)
        else:
            raise AttributeError('JSON schema missing one or more properties')

    @classmethod
    def map_jsonschema_field_to_dictshield(cls, schema_field, field_name=None):
        # get the kind of field this is
        if not 'type' in schema_field:
            return  # not data, so ignore
        tipe = schema_field.pop('type')
        fmt = schema_field.pop('format', None)

        dictshield_field_type = dictshield_fields.get((tipe, fmt,), None)
        if not dictshield_field_type:
            raise DictFieldNotFound

        kwargs = {}
        if tipe == 'array':  # list types
            items = schema_field.pop('items', None)
            if items == None:  # any possible item isn't allowed by listfield
                raise NotImplementedError
            elif isinstance(items, dict):  # list of a single type
                items = [items]
            kwargs['fields'] = [cls.map_jsonschema_field_to_dictshield(item)
                                for item in items]

        if tipe == "object":  # embedded objects
            #schema_field['title'] = field_name
            document_type = EmbeddedDocument.from_jsonschema(schema_field)
            kwargs['document_type'] = document_type
            schema_field.pop('properties')

        schema_field.pop('title', None)  # make sure this isn't in here

        for kwarg_name, v in schema_field.items():
            if kwarg_name in schema_kwargs_to_dictshield:
                kwarg_name = schema_kwargs_to_dictshield[kwarg_name]
            kwargs[kwarg_name] = v

        return dictshield_field_type(**kwargs)


###
### Model Manipulation Functions
###

def _swap_field(klass, new_field, fields):
    """This function takes an existing class definition `klass` and create a
    new version of the structure with the fields in `fields` converted to
    `field` instances.

    Effectively doing this:

        class.field_name = id_field()  # like ObjectIdField, perhaps

    Returns the class for compatibility, making it compatible with a decorator.
    """
    ### The metaclass attributes will fake not having inheritance
    cn = klass._class_name
    sc = klass._superclasses
    klass_name = klass.__name__

    ### Generate the id_fields for each field we're updating. Mark the actual
    ### id_field as the uniq_field named '_id'
    fields_dict = dict()
    for f in fields:
        if f is klass._meta['id_field']:
            fields_dict[f] = new_field(uniq_field='_id')
        else:
            fields_dict[f] = new_field()

    ### Generate new class
    new_klass = type(klass_name, (klass,), fields_dict)

    ### Meta attributes act like it never happened. :)
    new_klass._class_name = cn
    new_klass._superclasses = sc

    return new_klass


def diff_id_field(id_field, field_list, *arg):
    """This function is a decorator that takes an id field, like ObjectIdField,
    and replaces the fields in `field_list` to use `id_field` instead.

    Wrap a class definition and it will apply the field swap in an simply and
    expressive way.

    The function can be used as a decorator OR the adjusted class can be passed
    as an optional third argument.
    """
    if len(arg) == 1:
        return _swap_field(arg[0], id_field, field_list)

    def wrap(klass):
        klass = _swap_field(klass, id_field, field_list)
        return klass
    return wrap


###
### Documents Models
###

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

    If `_public_fields` is defined, `make_json_publicsafe` can be used to
    create a structure made of only the fields in this list, making it our
    white list.
    """
    _internal_fields = [
        '_id', 'id', '_cls', '_types',
    ]

    _public_fields = None

    @classmethod
    def _get_internal_fields(cls):
        """Helper function that determines the union of
        :attr:`_internal_fields` and :attr:`_private_fields`, else returns just
        :attr:`_internal_fields`.
        """
        internal_fields = set(cls._internal_fields)
        if hasattr(cls, '_private_fields'):
            private_fields = set(cls._private_fields)
            internal_fields = internal_fields.union(private_fields)
        return internal_fields

    ###
    ### Make Safe Functions
    ###

    @classmethod
    def make_safe(cls, doc_dict_or_dicts, field_converter, doc_converter,
                  doc_encoder, field_list=None, white_list=True):
        """This function is the building block of the safe mechanism. This
        class method takes a doc, dict or dicts and converts them into the
        equivalent structure with three basic rules applied.

          1. The fields must be converted from the model into a type. This is
             currently scene as calling `for_python()` or `for_json()` on
             fields.

          2. A function that knows how to handle `EmbeddedDocument` instances,
             using the same security parameters as the caller; this function.

          3. The field list that acts as either a white list or a black list. A
             white list preserves only the keys explicitly listed. A black list
             preserves any keys not explicitly listed.
        """
        ### Field list defaults to `_internal_fields` + `_public_fields`
        if field_list is None:
            field_list = cls._get_internal_fields()

        ### Setup white or black list detection
        gottago = lambda k, v: k not in field_list or v is None
        if not white_list:
            gottago = lambda k, v: k in field_list or v is None

        if isinstance(doc_dict_or_dicts, BaseDocument):
            doc_dict = dict((f, doc_dict_or_dicts[f])
                            for f in doc_dict_or_dicts)
        else:
            doc_dict = doc_dict_or_dicts

        ### Transform each field (Docs implement dictionary-style field access)
        for k, v in doc_dict.items():
            if gottago(k, v):
                del doc_dict[k]
            elif isinstance(v, EmbeddedDocument):
                doc_dict[k] = doc_converter(v)
            elif isinstance(v, list) and len(v) > 0:
                if isinstance(v[0], EmbeddedDocument):
                    doc_dict[k] = [doc_converter(vi) for vi in v]
            else:
                doc_dict[k] = field_converter(k, v)

            if k in doc_dict and \
                   k in cls._fields and \
                   cls._fields[k].minimized_field_name:
                doc_dict[cls._fields[k].minimized_field_name] = doc_dict[k]
                del doc_dict[k]

        return doc_dict

    @classmethod
    def make_ownersafe(cls, doc_dict_or_dicts):
        field_converter = lambda f, v: v
        doc_encoder = lambda d: d.to_python()
        doc_converter = lambda d: d.make_ownersafe(d)
        field_list = cls._get_internal_fields()
        white_list = False

        return cls.make_safe(doc_dict_or_dicts, field_converter, doc_converter,
                             doc_encoder, field_list=field_list,
                             white_list=white_list)

    @classmethod
    def make_json_ownersafe(cls, doc_dict_or_dicts, encode=True,
                            sort_keys=False):
        field_converter = lambda f, v: cls._fields[f].for_json(v)
        doc_encoder = lambda d: d.to_json(encode=False)
        doc_converter = lambda d: d.make_json_ownersafe(d, encode=False,
                                                        sort_keys=sort_keys)
        field_list = cls._get_internal_fields()
        white_list = False

        safed = cls.make_safe(doc_dict_or_dicts, field_converter,
                              doc_converter, doc_encoder,
                              field_list=field_list, white_list=white_list)
        if encode:
            return json.dumps(safed, sort_keys=sort_keys)
        else:
            return safed

    @classmethod
    def make_publicsafe(cls, doc_dict_or_dicts):
        field_converter = lambda f, v: v
        doc_encoder = lambda d: d.to_python()
        doc_converter = lambda d: d.make_publicsafe(d)
        field_list = cls._public_fields
        white_list = True

        return cls.make_safe(doc_dict_or_dicts, field_converter, doc_converter,
                             doc_encoder,  field_list=cls._public_fields,
                             white_list=white_list)

    @classmethod
    def make_json_publicsafe(cls, doc_dict_or_dicts, encode=True,
                             sort_keys=False):
        field_converter = lambda f, v: cls._fields[f].for_json(v)
        doc_encoder = lambda d: d.to_json(encode=False)
        doc_converter = lambda d: d.make_json_publicsafe(d, encode=False,
                                                         sort_keys=sort_keys)
        field_list = cls._public_fields
        white_list = True

        safed = cls.make_safe(doc_dict_or_dicts, field_converter,
                              doc_converter, doc_encoder,
                              field_list=field_list, white_list=white_list)
        if encode:
            return json.dumps(safed, sort_keys=sort_keys)
        else:
            return safed

    ###
    ### Validation
    ###

    @classmethod
    def _gen_handle_exception(cls, validate_all, exception_list):
        """Generates a function for either raising exceptions or collecting
        them in a list.
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

        The case where nothing accumulates is to prevent growing data
        structures unnecessarily.
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
        for k, v in cls._fields.items():

            # handle common id name
            if k is 'id':
                k = '_id'

            handle_class_field(k)

            # we don't accept internal fields from users
            if k in internal_fields and k in values:
                value_is_default = (values[k] is v.default)
                if not value_is_default:
                    error_msg = 'Overwrite of internal fields attempted'
                    e = ShieldException(error_msg, k, v)
                    handle_exception(e)
                    continue

            if field_inspector(k, v):
                datum = values[k]
                # if datum is None, skip
                if datum is None:
                    continue
                # treat empty strings as empty values and skip
                if isinstance(datum, (str, unicode)) and \
                       len(datum.strip()) == 0:
                    continue
                try:
                    v.validate(datum)
                except ShieldException, e:
                    handle_exception(e)

        # Remove rogue fields
        if len(class_fields) > 0:  # if accumulation is not disabled
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
        fun = lambda k, v: v.required or k in values
        return cls._validate_helper(fun, values, validate_all=validate_all)

    @classmethod
    def validate_class_partial(cls, values, validate_all=False):
        """This is a convenience function that loops over _fields in
        cls to validate them. This function is a partial validatation
        only, meaning the values given and does not check if the document
        is complete.
        """
        fun = lambda k, v: k in values
        return cls._validate_helper(fun, values, validate_all=validate_all)


class EmbeddedDocument(BaseDocument, SafeableMixin):
    """A :class:`~dictshield.Document` that isn't stored in its own
    collection.  :class:`~dictshield.EmbeddedDocument`\ s should be used as
    fields on :class:`~dictshield.Document`\ s through the
    :class:`~dictshield.EmbeddedDocumentField` field type.
    """

    __metaclass__ = DocumentMetaclass
    __optionsclass__ = DocumentOptions


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
    __optionsclass__ = TopLevelDocumentOptions

