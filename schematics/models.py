import inspect
import copy


from schematics.base import (TypeException, ModelException, json)
from schematics.types import (DictFieldNotFound, schematic_types, BaseType,
                              UUIDType)


__all__ = ['ModelMetaclass', 'TopLevelModelMetaclass', 'BaseModel',
           'Model', 'TypeException']


###
### Parameters for serialization to JSONSchema
###

schema_kwargs_to_schematics = {
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'pattern': 'regex',
    'minimum': 'min_value',
    'maximum': 'max_value',
}


###
### Model Configuration
###

class ModelOptions(object):
    """This class is a container for all metaclass configuration options. It's
    primary purpose is to create an instance of a model's options for every
    instance of a model.

    It also creates errors in cases where unknown options parameters are found.
    """
    def __init__(self, klass, db_namespace=None, # permissions=None,
                 private_fields=None, public_fields=None):
        self.klass = klass
        self.db_namespace = db_namespace
        #self.permissions = permissions
        self.private_fields = private_fields
        self.public_fields = public_fields


def _parse_options_config(klass, attrs, options_class):
    """Parses the Options object on the class and translates it into an Option
    instance.
    """
    valid_attrs = dict()
    if 'Options' in attrs:
        options = attrs['Options']
        for attr_name, attr_value in inspect.getmembers(options):
            if not attr_name.startswith('_'):
                valid_attrs[attr_name] = attr_value
    oc = options_class(klass, **valid_attrs)
    return oc


def _gen_options(klass, attrs):
    """Processes the attributes and class parameters to generate the correct
    options schematic.

    Defaults to `ModelOptions` but it's ideal to define `__optionsclass_`
    on the Model's metaclass.
    """
    ### Parse Options
    options_class = ModelOptions
    if hasattr(klass, '__optionsclass__'):
        options_class = klass.__optionsclass__
    options = _parse_options_config(klass, attrs, options_class)
    return options


def _extract_fields(bases, attrs):
    ### Collect all fields in here
    model_fields = {}

    ### Aggregate fields found in base classes first
    for base in bases:
        ### Configure `_fields` list
        if hasattr(base, '_fields'):
            model_fields.update(base._fields)

    ### Collect field info from attrs
    for attr_name, attr_value in attrs.items():
        has_class = hasattr(attr_value, "__class__")
        if has_class and issubclass(attr_value.__class__, BaseType):
            ### attr_name = field name
            ### attr_value = field instance
            attr_value.field_name = attr_name  # fields know their name
            model_fields[attr_name] = attr_value
            
    return model_fields


###
### Metaclass Design
###

class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        """Processes a configuration of a Model type into a class.
        """
        ### Gen a class instance
        klass = type.__new__(cls, name, bases, attrs)

        ### Parse metaclass config into options schematic
        options = _gen_options(klass, attrs)
        if hasattr(klass, 'Options'):
            delattr(klass, 'Options')

        ### Extract fields and attach klass as owner
        fields =  _extract_fields(bases, attrs)
        for field in fields.values():
            field.owner_model = klass

        ### Attach collected data to klass
        setattr(klass, '_options', options)
        setattr(klass, '_fields', fields)
        setattr(klass, '_model_name', name)

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
                setattr(self, attr_name, attr_value)
                if attr_name in minimized_field_map:
                    setattr(self, minimized_field_map[attr_name], attr_value)
            # Put a diaper on the keys that don't belong and send 'em home
            except AttributeError:
                pass


    ###
    ### Validation functions
    ###

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
            raise ModelException(self._model_name, errs)
        return True


    ###
    ### Implement the dictionary interface
    ###

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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            keys = self._fields
            if not hasattr(other, 'id'):
                keys.pop("id", None)
            for key in keys:
                if self[key] != other[key]:
                    return False
            return True
        return False

    ###
    ### Representation Descriptors
    ###
    
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
    ### Model Definition Serialization
    ###

    @classmethod
    def for_jsonschema(cls):
        """Returns a representation of this Schematics class as a JSON schema,
        but not yet serialized to JSON. If certain fields are marked public,
        only those fields will be represented in the schema.

        Certain Schematics fields do not map precisely to JSON schema types or
        formats.
        """

        # Place all fields in the schema unless public ones are specified.
        if cls._options.public_fields is None:
            field_names = cls._fields.keys()
        else:
            field_names = copy.copy(cls._options.public_fields)

        properties = {}

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
    ### Instance Data Serialization
    ###

    def _to_fields(self, field_converter):
        """Returns a Python dictionary with the model's data keyed by field
        name.  The `field_converter` argument is a function that receives the
        field and it's value and returns the field converted to the desired
        formed.

        In the `to_json` function below, the `field_converter` argument is
        function that called `field.for_json` to convert the fields value
        into a form safe passing to `json.dumps`.
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
    cn = klass._model_name
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
### Validation functions
###

def _gen_handle_exception(validate_all, exception_list):
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


def _gen_handle_class_field(delete_rogues, field_list):
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

    # Create function for handling exceptions
    exceptions = list()
    handle_exception = _gen_handle_exception(validate_all, exceptions)

    # Create function for handling a flock of frakkin palins (rogue fields)
    data_fields = set(values.keys())
    class_fields = list()
    handle_class_field = _gen_handle_class_field(delete_rogues,
                                                 class_fields)

    # Loop across fields present in model
    for k, v in cls._fields.items():

        # handle common id name
        if k is 'id':
            k = '_id'

        handle_class_field(k)

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

def validate_class_fields(cls, values, validate_all=False):
    """This is a convenience function that loops over _fields in
    cls to validate them. If the field is not required AND not present,
    it is skipped.
    """
    fun = lambda k, v: v.required or k in values
    return _validate_helper(cls, fun, values, validate_all=validate_all)

def validate_class_partial(cls, values, validate_all=False):
    """This is a convenience function that loops over _fields in
    cls to validate them. This function is a partial validatation
    only, meaning the values given and does not check if the model
    is complete.
    """
    fun = lambda k, v: k in values
    return _validate_helper(cls, fun, values, validate_all=validate_all)


class Model(BaseModel):
    """Model YEAH
    """
    __metaclass__ = ModelMetaclass
    __optionsclass__ = ModelOptions
