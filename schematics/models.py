# encoding=utf-8

import inspect
import itertools

from .types import BaseType
from .types.compound import ModelType
from .types.serializable import Serializable
from .exceptions import BaseError, ValidationError, ModelValidationError, ConversionError, ModelConversionError
from .serialize import atoms, serialize, flatten, expand
from .validate import validate
from .datastructures import OrderedDict as OrderedDictWithSort


class FieldDescriptor(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, model, type=None):
        try:
            if model is None:
                return type.fields[self.name]
            return model._data[self.name]
        except KeyError:
            raise AttributeError(self.name)

    def __set__(self, model, value):
        field = model._fields[self.name]
        # TODO: read Options class for strict type checking flag
        #model._data[self.name] = field(value)
        if not isinstance(value, Model) and isinstance(field, ModelType):
            value = field.model_class(value)
        model._data[self.name] = value

    def __delete__(self, model):
        if self.name not in model._fields:
            raise AttributeError('%r has no attribute %r' %
                                 (type(model).__name__, self.name))
        del model._fields[self.name]


class ModelOptions(object):
    """
    This class is a container for all metaclass configuration options. Its
    primary purpose is to create an instance of a model's options for every
    instance of a model.

    It also creates errors in cases where unknown options parameters are found.

    :param roles:
        Allows to specify certain subsets of the model's fields for
        serialization.
    :param serialize_when_none:
        When ``False``, serialization skips fields that are None. Default: ``True``
    """
    def __init__(self, klass, namespace=None, roles=None, serialize_when_none=True):
        self.klass = klass
        self.namespace = namespace
        self.roles = roles or {}
        self.serialize_when_none = serialize_when_none


class ModelMeta(type):
    """Meta class for Models. Handles model inheritance and Options.
    """

    def __new__(cls, name, bases, attrs):
        fields = OrderedDictWithSort()
        serializables = {}
        validator_functions = {}  # Model level

        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(base._fields)
            if hasattr(base, '_serializables'):
                serializables.update(base._serializables)
            if hasattr(base, '_validator_functions'):
                validator_functions.update(base._validator_functions)

        for key, value in attrs.iteritems():
            if key.startswith('validate_') and callable(value):
                validator_functions[key[9:]] = value
            if isinstance(value, BaseType):
                fields[key] = value
            if isinstance(value, Serializable):
                serializables[key] = value

        fields.sort(key=lambda i: i[1]._position_hint)

        for key, field in fields.iteritems():
            # For accessing internal data by field name attributes
            attrs[key] = FieldDescriptor(key)

        attrs['_options'] = cls._read_options(name, bases, attrs)

        attrs['_validator_functions'] = validator_functions
        attrs['_serializables'] = serializables
        attrs['_fields'] = fields

        klass = type.__new__(cls, name, bases, attrs)

        for field in fields.values():
            field.owner_model = klass

        return klass

    @classmethod
    def _read_options(cls, name, bases, attrs):
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
    """Enclosure for fields and validation. Same pattern deployed by Django
    models, SQLAlchemy declarative extension and other developer friendly
    libraries.

    :param raw_data:
        Raw data to initialize the object with. Can raise ``ConversionError`` if
        it is not possible to convert the raw data into richer Python constructs.

    """

    __metaclass__ = ModelMeta
    __optionsclass__ = ModelOptions

    @classmethod
    def from_flat(cls, data):
        return cls(expand(data))

    def __init__(self, raw_data=None):
        if raw_data is None:
            raw_data = {}
        self._initial = raw_data
        self._data = self.convert(raw_data)

    def validate(self, partial=False, strict=False):
        """
        Validates the state of the model and adding additional untrusted data
        as well. If the models is invalid, raises ValidationError with error messages.

        :param partial:
            Allow partial data to validate; useful for PATCH requests.
            Essentially drops the ``required=True`` arguments from field
            definitions. Default: False
        :param strict:
            Complain about unrecognized keys. Default: False
        """
        try:
            data = validate(self, self._data, partial=partial, strict=strict)
            # Set internal data and touch the TypeDescriptors by setattr
            self._data.update(**data)
        except BaseError as e:
            raise ModelValidationError(e.messages)

    def serialize(self, role=None):
        """Return data as it would be validated. No filtering of output unless
        role is defined.

        :param role:
            Filter output by a specific role

        """
        return serialize(self, role)

    def flatten(self, role=None, prefix=""):
        """
        Return data as a pure key-value dictionary, where the values are
        primitive types (string, bool, int, long).

        :param role:
            Filter output by a specific role

        """
        return flatten(self, role, prefix=prefix)

    def convert(self, raw_data):
        """
        Converts the raw data into richer Python constructs according to the
        fields on the model
        """
        data = {}
        errors = {}

        is_class = isinstance(raw_data, self.__class__)
        is_dict = isinstance(raw_data, dict)

        if not is_class and not is_dict:
            error_msg = 'Model conversion requires a model or dict'
            raise ModelConversionError(error_msg)

        for field_name, field in self._fields.iteritems():
            serialized_field_name = field.serialized_name or field_name

            try:
                if serialized_field_name in raw_data:
                    raw_value = raw_data[serialized_field_name]
                else:
                    raw_value = raw_data[field_name]

                if raw_value is not None:
                    raw_value = field.convert(raw_value)
                data[field_name] = raw_value
                
            except KeyError:
                data[field_name] = field.default
            except ConversionError, e:
                errors[serialized_field_name] = e.messages

        if errors:
            raise ModelConversionError(errors)

        return data

    def __iter__(self):
        return self.iter()

    def iter(self):
        return iter(self._fields)
    
    def atoms(self, include_serializables=True):
        return atoms(self.__class__, self, include_serializables)

    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        # Ensure that the field exists before settings its value
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

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return u"<%s: %s>" % (self.__class__.__name__, u)

    def __unicode__(self):
        return '%s object' % self.__class__.__name__
