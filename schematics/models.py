# encoding=utf-8

import inspect
import itertools

from .types import BaseType
from .types.compound import ModelType
from .types.serializable import Serializable
from .exceptions import (BaseError, ValidationError, ModelValidationError,
                         ConversionError, ModelConversionError)
from .transforms import allow_none, atoms, flatten, expand
from .transforms import to_primitive, to_native, convert
from .validate import validate
from .datastructures import OrderedDict as OrderedDictWithSort


class FieldDescriptor(object):
    """
    The FieldDescriptor serves as a wrapper for Types that converts them into
    fields.

    A field is then the merger of a Type and it's Model.
    """

    def __init__(self, name):
        """
        :param name:
            The field's name
        """
        self.name = name

    def __get__(self, instance, cls):
        """
        Checks the field name against the definition of the model and returns
        the corresponding data for valid fields or raises the appropriate error
        for fields missing from a class.
        """
        try:
            if instance is None:
                return cls._fields[self.name]
            return instance._data[self.name]
        except KeyError:
            raise AttributeError(self.name)

    def __set__(self, instance, value):
        """
        Checks the field name against a model and sets the value.
        """
        field = instance._fields[self.name]
        if not isinstance(value, Model) and isinstance(field, ModelType):
            value = field.model_class(value)
        instance._data[self.name] = value

    def __delete__(self, instance):
        """
        Checks the field name against a model and deletes the field.
        """
        if self.name not in instance._fields:
            raise AttributeError('%r has no attribute %r' %
                                 (type(instance).__name__, self.name))
        del instance._fields[self.name]


class ModelOptions(object):
    """
    This class is a container for all metaclass configuration options. Its
    primary purpose is to create an instance of a model's options for every
    instance of a model.
    """
    def __init__(self, klass, namespace=None, roles=None,
                 serialize_when_none=True):
        """
        :param klass:
            The class which this options instance belongs to.
        :param namespace:
            A namespace identifier that can be used with persistence layers.
        :param roles:
            Allows to specify certain subsets of the model's fields for
            serialization.
        :param serialize_when_none:
            When ``False``, serialization skips fields that are None.
            Default: ``True``
        """
        self.klass = klass
        self.namespace = namespace
        self.roles = roles or {}
        self.serialize_when_none = serialize_when_none


class ModelMeta(type):
    """
    Meta class for Models. 
    """

    def __new__(cls, name, bases, attrs):
        """
        This metaclass adds four attributes to host classes: cls._fields,
        cls._serializables, cls._validator_functions, and cls._options.
        
        This function creates those attributes like this:
        
        ``cls._fields`` is list of fields that are schematics types
        ``cls._serializables`` is a list of functions that are used to generate
        values during serialization
        ``cls._validator_functions`` are class level validation functions
        ``cls._options`` is the end result of parsing the ``Options`` class
        """

        ### Structures used to accumulate meta info
        fields = OrderedDictWithSort()
        serializables = {}
        validator_functions = {}  # Model level

        ### Accumulate metas info from parent classes
        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(base._fields)
            if hasattr(base, '_serializables'):
                serializables.update(base._serializables)
            if hasattr(base, '_validator_functions'):
                validator_functions.update(base._validator_functions)

        ### Parse this class's attributes into meta structures
        for key, value in attrs.iteritems():
            if key.startswith('validate_') and callable(value):
                validator_functions[key[9:]] = value
            if isinstance(value, BaseType):
                fields[key] = value
            if isinstance(value, Serializable):
                serializables[key] = value

        ### Parse meta options
        options = cls._read_options(name, bases, attrs)
            
        ### Convert list of types into fields for new klass
        fields.sort(key=lambda i: i[1]._position_hint)
        for key, field in fields.iteritems():
            attrs[key] = FieldDescriptor(key)

        ### Ready meta data to be klass attributes
        attrs['_fields'] = fields
        attrs['_serializables'] = serializables
        attrs['_validator_functions'] = validator_functions
        attrs['_options'] = options

        klass = type.__new__(cls, name, bases, attrs)

        ### Add reference to klass to each field instance
        for field in fields.values():
            field.owner_model = klass

        return klass

    @classmethod
    def _read_options(cls, name, bases, attrs):
        """
        Parses `ModelOptions` instance into the options value attached to
        `Model` instances.
        """
        options_members = {}

        for base in reversed(bases):
            if hasattr(base, "_options"):
                for k, v in inspect.getmembers(base._options):
                    if not k.startswith("_") and not k == "klass":
                        options_members[k] = v

        options_class = getattr(attrs, '__classoptions__', ModelOptions)
        if 'Options' in attrs:
            for k, v in inspect.getmembers(attrs['Options']):
                if not k.startswith("_"):
                    if k == "roles":
                        roles = options_members.get("roles", {}).copy()
                        roles.update(v)

                        options_members["roles"] = roles
                    else:
                        options_members[k] = v

        return options_class(cls, **options_members)

    @property
    def fields(cls):
        return cls._fields

    def __iter__(self):
        return itertools.chain(
            self._unbound_fields.iteritems(),
            self._unbound_serializables.iteritems()
        )


class Model(object):
    """
    Enclosure for fields and validation. Same pattern deployed by Django
    models, SQLAlchemy declarative extension and other developer friendly
    libraries.

    Initial field values can be passed in as keyword arguments to ``__init__``
    to initialize the object with. Can raise ``ConversionError`` if it is not
    possible to convert the raw data into richer Python constructs.
    """

    __metaclass__ = ModelMeta
    __optionsclass__ = ModelOptions

    def __init__(self, raw_data=None):  # TODO change back to keywords
        if raw_data is None:
            raw_data = {}
        self._initial = raw_data
        self._data = self.convert(raw_data, strict=True)

    def validate(self, partial=False, strict=False):
        """
        Validates the state of the model and adding additional untrusted data
        as well. If the models is invalid, raises ValidationError with error
        messages.

        :param partial:
            Allow partial data to validate; useful for PATCH requests.
            Essentially drops the ``required=True`` arguments from field
            definitions. Default: False
        :param strict:
            Complain about unrecognized keys. Default: False
        """
        try:
            data = validate(self.__class__, self._data, partial=partial,
                            strict=strict)
            self._data.update(**data)
        except BaseError as e:
            raise ModelValidationError(e.messages)

    def convert(self, raw_data, **kw):
        """
        Converts the raw data into richer Python constructs according to the
        fields on the model

        :param raw_data:
            The data to be converted
        """
        return convert(self.__class__, raw_data, **kw)

    def to_native(self, role=None):
        return to_native(self.__class__, self, role=role)

    def to_primitive(self, role=None):
        """Return data as it would be validated. No filtering of output unless
        role is defined.

        :param role:
            Filter output by a specific role

        """
        return to_primitive(self.__class__, self, role=role)

    def serialize(self, role=None):
        return self.to_primitive(role=role)

    def flatten(self, role=None, prefix=""):
        """
        Return data as a pure key-value dictionary, where the values are
        primitive types (string, bool, int, long).

        :param role:
            Filter output by a specific role
        :param prefix:
            A prefix to use for keynames during flattening.
        """
        return flatten(self.__class__, self, role=role, prefix=prefix)

    @classmethod
    def from_flat(cls, data):
        return cls(expand(data))

    def atoms(self):
        """
        Iterator for the atomic components of a model definition and relevant
        data that creates a threeple of the field's name, the instance of it's
        type, and it's value.
        """
        return atoms(self.__class__, self)

    @classmethod
    def allow_none(cls, field):
        """
        Inspects a field and class for ``serialize_when_none`` setting.

        The setting defaults to the value of the class.  A field can override
        the class setting with it's own ``serialize_when_none`` setting.
        """
        return allow_none(cls, field)

    def __iter__(self):
        return self.iter()

    def iter(self):
        return iter(self._fields)
    
    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, name, value):
        if name not in self._data:
            raise KeyError(name)
        return setattr(self, name, value)

    def __contains__(self, name):
        return name in self._data or name in self._serializables

    def __len__(self):
        return len(self._data)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            keys = self._fields

            for key in keys:
                if self[key] != other[key]:
                    return False
            return True
        return False

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return u"<%s: %s>" % (self.__class__.__name__, u)

    def __unicode__(self):
        return '%s object' % self.__class__.__name__
