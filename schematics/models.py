import inspect
import copy

from schematics.base import TypeException, ModelException, json

__all__ = ['ModelMetaclass', 'TopLevelModelMetaclass', 'BaseModel',
           'Model', 'TypeException']

from schematics.types import (DictFieldNotFound,
                              schematic_types,
                              BaseType,
                              UUIDType)

schema_kwargs_to_schematics = {
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'pattern': 'regex',
    'minimum': 'min_value',
    'maximum': 'max_value',
}


###
### Metaclass Configuration
###

class ModelOptions(object):
    """This class is a container for all metaclass configuration options. The
    `__init__` method will set the default values for attributes and then
    attempt to map any keyword arguments to attributes of the same name.
    """
    def __init__(self, mixin=False, bucket=None, private_fields=None,
                 public_fields=None):
        self.bucket = bucket
        self.private_fields = private_fields
        self.public_fields = public_fields


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
    options schematic.

    Defaults to `ModelOptions` but it's ideal to define `__optionsclass_`
    on the Model's metaclass.
    """
    ### Parse Meta
    options_class = ModelOptions
    if hasattr(klass, '__optionsclass__'):
        options_class = klass.__optionsclass__
    options = _parse_meta_config(attrs, options_class)
    return options


###
### Metaclass Design
###

class ModelMetaclass(type):
    """This metaclass is responsible for the core metadata collections on
    `Model` instances.

    It looks for a class called `Meta` and, if found, it parses the class into
    a `ModelOptions` instance. This class stores all the options that have
    values, meaning it also sets some defaults.

    The implementation of `__new__` aggregates instances of `BaseType` into a
    dict called `_fields`, which informs the serialization layers. The data is
    stored in a dict, attached to the model *instance* called `_data`, which
    maps field names to their values.
    """
    def __new__(cls, name, bases, attrs):
        """Processes a configuration of a Model type into a class.
        """
        ### Gen a class instance
        klass = type.__new__(cls, name, bases, attrs)

        metaclass = attrs.get('__metaclass__')
        if metaclass and issubclass(metaclass, ModelMetaclass):
            return klass

        ### Parse metaclass config into options schematic
        options = _gen_options(klass, attrs)
        setattr(klass, '_options', options)
        if hasattr(klass, 'Meta'):
            delattr(klass, 'Meta')

        ### fieldss for collecting schematic information
        model_fields = {}
        class_name = [name]
        superclasses = {}

        ###
        ### Handle Base Classes
        ###

        for base in bases:
            ### Configure `_fields` list
            if hasattr(base, '_fields'):
                model_fields.update(base._fields)
                class_name.append(base._class_name)
                superclasses[base._class_name] = base
                superclasses.update(base._superclasses)

        ###
        ### Construct The Class Instance
        ###

        ### Collect field info
        for attr_name, attr_value in attrs.items():
            has_class = hasattr(attr_value, "__class__")
            if has_class and issubclass(attr_value.__class__, BaseType):
                attr_value.field_name = attr_name
                model_fields[attr_name] = attr_value

        ### Attach collected data to klass
        setattr(klass, '_fields', model_fields)
        setattr(klass, '_class_name', '.'.join(reversed(class_name)))
        setattr(klass, '_superclasses', superclasses)

        ### Set owner in field instances to klass
        for field in klass._fields.values():
            field.owner_model = klass

        ### Fin.
        return klass

    def __str__(self):
        if hasattr(self, '__unicode__'):
            return unicode(self).encode('utf-8')
        return '%s object' % self.__class__.__name__


class MixinMetaclass(ModelMetaclass):
    """Mixins behave differently from regular models. They serve to simply add
    fields to a Model and have no effect on object schematic information.
    """
    def __new__(cls, name, bases, attrs):
        """Adds fields to the existing `_fields` map.
        """
        klass = super(MixinMetaclass, cls).__new__(cls, name, bases, attrs)

        #print klass._fields
        ### Fin.
        return klass

    def __str__(self):
        if hasattr(self, '__unicode__'):
            return unicode(self).encode('utf-8')
        return '%s object' % self.__class__.__name__


###
### Model schematics
###

class BaseModel(object):

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

    def validate(self, validate_all=False):
        """Ensure that all fields' values are valid and that required fields
        are present.

        Throws a ModelException if Model is invalid
        """
        # Get a list of tuples of field names and their current values
        fields = [(field, getattr(self, name))
                  for name, field in self._fields.items()]

        # Ensure that each field is matched to a valid value
        errs = []
        for field, value in fields:
            err = None
            # treat empty strings as nonexistent
            if value is not None and value != '':
                try:
                    field._validate(value)
                except TypeException, e:
                    err = e
                except (ValueError, AttributeError, AssertionError):
                    err = TypeException('Invalid value', field.field_name,
                                        value)
            elif field.required:
                err = TypeException('Required field missing',
                                    field.field_name,
                                    value)
            # If validate_all, save errors to a list
            # Otherwise, throw the first error
            if err:
                errs.append(err)
            if err and not validate_all:
                # NB: raising a ModelException in this case would be more
                # consistent, but existing code might expect TypeException
                raise err

        if errs:
            raise ModelException(self._class_name, errs)
        return True

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
        """Returns a representation of this Structures class as a JSON schema,
        but not yet serialized to JSON. If certain fields are marked public,
        only those fields will be represented in the schema.

        Certain Structures fields do not map precisely to JSON schema types or
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
        """Returns a representation of this Structures class as a JSON schema.
        If certain fields are marked public, only those fields will be
        represented in the schema.

        Certain Structures fields do not map precisely to JSON schema types or
        formats.
        """
        return json.dumps(cls.for_jsonschema())

    ###
    ### Instance Serialization
    ###

    def _to_fields(self, field_converter):
        """Returns a Python dictionary representing the Model's
        metaschematic and values.
        """
        data = {}

        # First map the subclasses of BaseType
        for field_name, field in self._fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
                data[field_name] = field_converter(field, value)

        return data

    def to_python(self):
        """Returns a Python dictionary representing the Model's
        metaschematic and values.
        """
        fun = lambda f, v: f.for_python(v)
        data = self._to_fields(fun)
        return data

    def to_json(self, encode=True, sort_keys=False):
        """Return data prepared for JSON. By default, it returns a JSON encoded
        string, but disabling the encoding to prevent double encoding with
        embedded models.
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
        """Generate a Schematics Model class from a JSON schema.  The JSON
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
            raise AttributeError('JSON Schema missing Model title')

        if 'description' in schema:
            # TODO figure out way to put this in to resulting obj
            model = schema['description']

        if 'properties' in schema:
            dictfields = {}
            for field_name, schema_field in schema['properties'].iteritems():
                if field_name == "_id":
                    field_name = "id"
                field = cls.map_jsonschema_field_to_schematics(schema_field)
                dictfields[field_name] = field
            return type(class_name, (cls,), dictfields)
        else:
            raise AttributeError('JSON schema missing one or more properties')

    @classmethod
    def map_jsonschema_field_to_schematics(cls, schema_field, field_name=None):
        # get the kind of field this is
        if not 'type' in schema_field:
            return  # not data, so ignore
        tipe = schema_field.pop('type')
        fmt = schema_field.pop('format', None)

        schematics_field_type = schematics_fields.get((tipe, fmt,), None)
        if not schematics_field_type:
            raise DictFieldNotFound

        kwargs = {}
        if tipe == 'array':  # list types
            items = schema_field.pop('items', None)
            if items == None:  # any possible item isn't allowed by listfield
                raise NotImplementedError
            elif isinstance(items, dict):  # list of a single type
                items = [items]
            kwargs['fields'] = [cls.map_jsonschema_field_to_schematics(item)
                                for item in items]

        if tipe == "object":  # embedded objects
            #schema_field['title'] = field_name
            model_type = Model.from_jsonschema(schema_field)
            kwargs['model_type'] = model_type
            schema_field.pop('properties')

        schema_field.pop('title', None)  # make sure this isn't in here

        for kwarg_name, v in schema_field.items():
            if kwarg_name in schema_kwargs_to_schematics:
                kwarg_name = schema_kwargs_to_schematics[kwarg_name]
            kwargs[kwarg_name] = v

        return schematics_field_type(**kwargs)


###
### Model Manipulation Functions
###

def swap_field(klass, new_field, fields):
    """This function takes an existing class definition `klass` and create a
    new version of the schematic with the fields in `fields` converted to
    `field` instances.

    Effectively doing this:

        class.field_name = id_field()  # like ObjectIdType, perhaps

    Returns the class for compatibility, making it compatible with a decorator.
    """
    ### The metaclass attributes will fake not having inheritance
    cn = klass._class_name
    sc = klass._superclasses
    klass_name = klass.__name__
    new_klass = type(klass_name, (klass,), {})

    ### Generate the id_fields for each field we're updating. Mark the actual
    ### id_field as the uniq_field named '_id'
    fields_dict = dict()
    for f in fields:
        if f is 'id':
            new_klass._fields[f] = new_field(uniq_field='_id')
        else:
            new_klass._fields[f] = new_field()

    new_klass.id = new_klass._fields['id']
    return new_klass


def diff_id_field(id_field, field_list, *arg):
    """This function is a decorator that takes an id field, like ObjectIdType,
    and replaces the fields in `field_list` to use `id_field` instead.

    Wrap a class definition and it will apply the field swap in an simply and
    expressive way.

    The function can be used as a decorator OR the adjusted class can be passed
    as an optional third argument.
    """
    if len(arg) == 1:
        return swap_field(arg[0], id_field, field_list)

    def wrap(klass):
        klass = swap_field(klass, id_field, field_list)
        return klass
    return wrap


###
### Models Models
###

class SafeableMixin:
    """A `SafeableMixin` is used to add unix style permissions to fields in a
    `Model`. It creates this by using a black list and a white list in the
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
    create a schematic made of only the fields in this list, making it our
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
    def make_safe(cls, model_dict_or_dicts, field_converter, model_converter,
                  model_encoder, field_list=None, white_list=True):
        """This function is the building block of the safe mechanism. This
        class method takes a model, dict or dicts and converts them into the
        equivalent schematic with three basic rules applied.

          1. The fields must be converted from the model into a type. This is
             currently scene as calling `for_python()` or `for_json()` on
             fields.

          2. A function that knows how to handle `Model` instances, using the
             same security parameters as the caller; this function.

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

        if isinstance(model_dict_or_dicts, BaseModel):
            model_dict = dict((f, model_dict_or_dicts[f])
                            for f in model_dict_or_dicts)
        else:
            model_dict = model_dict_or_dicts

        ### Transform each field
        for k, v in model_dict.items():
            if gottago(k, v):
                del model_dict[k]
            elif isinstance(v, Model):
                model_dict[k] = model_converter(v)
            elif isinstance(v, list) and len(v) > 0:
                if isinstance(v[0], Model):
                    model_dict[k] = [model_converter(vi) for vi in v]
            else:
                model_dict[k] = field_converter(k, v)

            if k in model_dict and \
                   k in cls._fields and \
                   cls._fields[k].minimized_field_name:
                model_dict[cls._fields[k].minimized_field_name] = model_dict[k]
                del model_dict[k]

        return model_dict

    @classmethod
    def make_ownersafe(cls, model_dict_or_dicts):
        field_converter = lambda f, v: v
        model_encoder = lambda m: m.to_python()
        model_converter = lambda m: m.make_ownersafe(m)
        field_list = cls._get_internal_fields()
        white_list = False

        return cls.make_safe(model_dict_or_dicts, field_converter,
                             model_converter, model_encoder,
                             field_list=field_list, white_list=white_list)

    @classmethod
    def make_json_ownersafe(cls, model_dict_or_dicts, encode=True,
                            sort_keys=False):
        field_converter = lambda f, v: cls._fields[f].for_json(v)
        model_encoder = lambda m: m.to_json(encode=False)
        model_converter = lambda m: m.make_json_ownersafe(m, encode=False,
                                                          sort_keys=sort_keys)
        field_list = cls._get_internal_fields()
        white_list = False

        safed = cls.make_safe(model_dict_or_dicts, field_converter,
                              model_converter, model_encoder,
                              field_list=field_list, white_list=white_list)
        if encode:
            return json.dumps(safed, sort_keys=sort_keys)
        else:
            return safed

    @classmethod
    def make_publicsafe(cls, model_dict_or_dicts):
        field_converter = lambda f, v: v
        model_encoder = lambda m: m.to_python()
        model_converter = lambda m: m.make_publicsafe(m)
        field_list = cls._public_fields
        white_list = True

        return cls.make_safe(model_dict_or_dicts, field_converter,
                             model_converter, model_encoder,
                             field_list=cls._public_fields,
                             white_list=white_list)

    @classmethod
    def make_json_publicsafe(cls, model_dict_or_dicts, encode=True,
                             sort_keys=False):
        field_converter = lambda f, v: cls._fields[f].for_json(v)
        model_encoder = lambda m: m.to_json(encode=False)
        model_converter = lambda m: m.make_json_publicsafe(m, encode=False,
                                                           sort_keys=sort_keys)
        field_list = cls._public_fields
        white_list = True

        safed = cls.make_safe(model_dict_or_dicts, field_converter,
                              model_converter, model_encoder,
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
        schematics unnecessarily.
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
        validates the data in values and does not guarantee a complete model
        is present.

        'not present' is defined as not having a value OR having '' (or u'')
        as a value.
        """
        if not hasattr(cls, '_fields'):
            raise ValueError('cls is not a Model instance')

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
                    e = TypeException(error_msg, k, v)
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
                except TypeException, e:
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
        only, meaning the values given and does not check if the model
        is complete.
        """
        fun = lambda k, v: k in values
        return cls._validate_helper(fun, values, validate_all=validate_all)


class Model(BaseModel, SafeableMixin):
    """Model YEAH
    """
    __metaclass__ = ModelMetaclass
    __optionsclass__ = ModelOptions

class Mixin(object):
    """Mixin YEAH
    """
    __metaclass__ = MixinMetaclass
