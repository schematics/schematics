import inspect
import copy


#from schematics.base import (TypeException, ModelException, json)
from schematics.base import json
from schematics.types import (DictFieldNotFound, schematic_types)
from schematics.types.base import BaseType


###
### Model Configuration
###

class ModelOptions(object):
    """This class is a container for all metaclass configuration options. It's
    primary purpose is to create an instance of a model's options for every
    instance of a model.

    It also creates errors in cases where unknown options parameters are found.
    """
    def __init__(self, klass, db_namespace=None, roles=None):
        self.klass = klass
        self.db_namespace = db_namespace

        ### Default roles to an empty dict
        self.roles = {}
        if roles is not None:
            self.roles = roles


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


###
### Metaclass Design
###

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


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        """Processes a configuration of a Model type into a class.
        """
        ### Gen a class instance
        klass = super(ModelMetaclass, cls).__new__(cls, name, bases, attrs)

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

        ### Loop over fields in model
        for attr_name, attr_value in self._fields.items():
            # Use default value if present
            value = getattr(self, attr_name, None)
            setattr(self, attr_name, value)

            field_name = attr_name
            if attr_value.minimized_field_name:
                field_name = attr_value.minimized_field_name
            elif attr_value.print_name:
                field_name = attr_value.print_name

            if attr_value.form_name is None:
               attr_value.form_name = field_name.title().replace('_',' ')

            if field_name in values:
                field_value = values[field_name]
                setattr(self, attr_name, field_value)
                    

    ###
    ### dict Interface
    ###

    def __iter__(self):
        return iter(self._fields)

    def __getitem__(self, name):
        try:
            if name in self._fields:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
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

    ### Representation Descriptors
    
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


class Model(BaseModel):
    """Model YEAH
    """
    __metaclass__ = ModelMetaclass
    __optionsclass__ = ModelOptions
