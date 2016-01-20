# encoding=utf-8

from copy import deepcopy
import inspect
import sys

from six import iteritems
from six import iterkeys
from six import add_metaclass

from .common import NATIVE, PRIMITIVE
from .datastructures import OrderedDict as OrderedDictWithSort
from .exceptions import (
    BaseError, ModelValidationError, MockCreationError,
    MissingValueError, UnknownFieldError
)
from .types import BaseType
from .types.serializable import Serializable
from .undefined import Undefined

try:
    unicode #PY2
except:
    import codecs
    unicode = str #PY3


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
        if instance is None:
            return cls._fields[self.name]
        else:
            value = instance._data[self.name]
            if value is Undefined:
                raise MissingValueError
            else:
                return value

    def __set__(self, instance, value):
        """
        Checks the field name against a model and sets the value.
        """
        field = instance._fields[self.name]
        if all((
                value is not None,
                not isinstance(value, Model),
                isinstance(field, ModelType))):
            value = field.model_class(value)
        instance._data[self.name] = value

    def __delete__(self, instance):
        """
        Checks the field name against a model and deletes the value.
        """
        instance._data[self.name] = Undefined


class ModelOptions(object):

    """
    This class is a container for all metaclass configuration options. Its
    primary purpose is to create an instance of a model's options for every
    instance of a model.
    """

    def __init__(self, klass, namespace=None, roles=None, export_level=3,
                 serialize_when_none=None, fields_order=None):
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
        :param fields_order:
            List of field names that dictates in which order will keys
            appear in serialized dictionary.
        """
        self.klass = klass
        self.namespace = namespace
        self.roles = roles or {}
        self.export_level = export_level
        if serialize_when_none is True:
            self.export_level = 3
        elif serialize_when_none is False:
            self.export_level = 1
        self.fields_order = fields_order


class ModelMeta(type):

    """
    Meta class for Models.
    """

    def __new__(mcs, name, bases, attrs):
        """
        This metaclass adds four attributes to host classes: mcs._fields,
        mcs._serializables, mcs._validator_functions, and mcs._options.

        This function creates those attributes like this:

        ``mcs._fields`` is list of fields that are schematics types
        ``mcs._serializables`` is a list of functions that are used to generate
        values during serialization
        ``mcs._validator_functions`` are class level validation functions
        ``mcs._options`` is the end result of parsing the ``Options`` class
        """

        # Structures used to accumulate meta info
        fields = OrderedDictWithSort()
        serializables = {}
        validator_functions = {}  # Model level

        # Accumulate metas info from parent classes
        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(deepcopy(base._fields))
            if hasattr(base, '_serializables'):
                serializables.update(deepcopy(base._serializables))
            if hasattr(base, '_validator_functions'):
                validator_functions.update(base._validator_functions)

        # Parse this class's attributes into meta structures
        for key, value in iteritems(attrs):
            if key.startswith('validate_') and callable(value):
                validator_functions[key[9:]] = value
            if isinstance(value, BaseType):
                fields[key] = value
            if isinstance(value, Serializable):
                serializables[key] = value

        # Parse meta options
        options = mcs._read_options(name, bases, attrs)

        # Convert list of types into fields for new klass
        fields.sort(key=lambda i: i[1]._position_hint)
        for key, field in iteritems(fields):
            attrs[key] = FieldDescriptor(key)
        for key, serializable in iteritems(serializables):
            attrs[key] = serializable

        # Ready meta data to be klass attributes
        attrs['_fields'] = fields
        attrs['_serializables'] = serializables
        attrs['_validator_functions'] = validator_functions
        attrs['_options'] = options

        klass = type.__new__(mcs, name, bases, attrs)

        # Register class on ancestor models
        klass._subclasses = []
        for base in klass.__mro__[1:]:
            if isinstance(base, ModelMeta):
                base._subclasses.append(klass)

        # Finalize fields
        for field_name, field in fields.items():
            field._setup(field_name, klass)
        for field_name, field in serializables.items():
            field._setup(field_name, klass)

        return klass

    @classmethod
    def _read_options(mcs, name, bases, attrs):
        """
        Parses `ModelOptions` instance into the options value attached to
        `Model` instances.
        """
        options_members = {}

        for base in reversed(bases):
            if hasattr(base, "_options"):
                for key, value in inspect.getmembers(base._options):
                    if not key.startswith("_") and not key == "klass":
                        options_members[key] = value

        options_class = attrs.get('__optionsclass__', ModelOptions)
        if 'Options' in attrs:
            for key, value in inspect.getmembers(attrs['Options']):
                if not key.startswith("_"):
                    if key == "roles":
                        roles = options_members.get("roles", {}).copy()
                        roles.update(value)

                        options_members["roles"] = roles
                    else:
                        options_members[key] = value

        return options_class(mcs, **options_members)

    @property
    def fields(cls):
        return cls._fields


@add_metaclass(ModelMeta)
class Model(object):

    """
    Enclosure for fields and validation. Same pattern deployed by Django
    models, SQLAlchemy declarative extension and other developer friendly
    libraries.

    Initial field values can be passed in as keyword arguments to ``__init__``
    to initialize the object with. Can raise ``ConversionError`` if it is not
    possible to convert the raw data into richer Python constructs.
    """

    __optionsclass__ = ModelOptions

    def __init__(self, raw_data=None, trusted_data=None, deserialize_mapping=None,
                 partial=True, strict=True, init_values=True, app_data=None, **kwargs):

        self._initial = raw_data = raw_data or {}
        self._data = self.convert(raw_data,
                                  trusted_data=trusted_data, mapping=deserialize_mapping,
                                  partial=partial, strict=strict, init_values=init_values,
                                  app_data=app_data, **kwargs)

    def validate(self, partial=False, strict=False, convert=True, app_data=None, **kwargs):
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
        :param convert:
            Controls whether to perform import conversion before validating.
            Can be turned off to skip an unnecessary conversion step if all values
            are known to have the right datatypes (e.g., when validating immediately
            after the initial import). Default: True
        """
        try:
            data = validate(self.__class__, self._data, partial=partial, strict=strict,
                            convert=convert, app_data=app_data, **kwargs)
            self._data.update(**data)
        except BaseError as exc:
            raise ModelValidationError(exc.messages)

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.

        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if data[k] is Undefined]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self

    def convert(self, raw_data, **kw):
        """
        Converts the raw data into richer Python constructs according to the
        fields on the model

        :param raw_data:
            The data to be converted
        """
        return convert(self.__class__, raw_data, **kw)

    def export(self, format, field_converter=None, role=None, app_data=None, **kwargs):
        data = export_loop(self.__class__, self, field_converter=field_converter,
                           role=role, app_data=app_data, **kwargs)
        if format == NATIVE:
            return self.__class__(trusted_data=data)
        else:
            return data

    def to_native(self, role=None, app_data=None, **kwargs):
        data = to_native(self.__class__, self, role=role, app_data=app_data, **kwargs)
        return self.__class__(trusted_data=data)

    def to_dict(self, role=None, app_data=None, **kwargs):
        return to_dict(self.__class__, self, role=role, app_data=app_data, **kwargs)

    def to_primitive(self, role=None, app_data=None, **kwargs):
        return to_primitive(self.__class__, self, role=role, app_data=app_data, **kwargs)

    def serialize(self, role=None, app_data=None, **kwargs):
        return self.to_primitive(role=role, app_data=app_data, **kwargs)

    def flatten(self, role=None, prefix="", app_data=None, context=None):
        """
        Return data as a pure key-value dictionary, where the values are
        primitive types (string, bool, int, long).

        :param role:
            Filter output by a specific role
        :param prefix:
            A prefix to use for keynames during flattening.
        """
        return flatten(self.__class__, self, role=role, prefix=prefix,
                       app_data=app_data, context=context)

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

    def __iter__(self):
        return self.iter()

    def iter(self):
        return iter(self.keys())

    def keys(self):
        return [k for k in self._fields if self._data[k] is not Undefined]

    def items(self):
        return [(k, self._data[k]) for k in self.keys()]

    def values(self):
        return [self._data[k] for k in self.keys()]

    def get(self, key, default=None):
        return getattr(self, key, default)

    @classmethod
    def get_mock_object(cls, context=None, overrides=None):
        """Get a mock object.

        :param dict context:
        :param dict overrides: overrides for the model
        """
        if overrides is None:
            overrides = {}
        values = {}
        for name, field in cls.fields.items():
            if name not in overrides:
                try:
                    values[name] = field.mock(context)
                except MockCreationError as exc:
                    raise MockCreationError('%s: %s' % (name, exc.message))
        values.update(overrides)
        return cls(values)

    def __getitem__(self, name):
        if name in self._fields or name in self._serializables:
            return getattr(self, name)
        else:
            raise UnknownFieldError

    def __setitem__(self, name, value):
        if name in self._fields:
            return setattr(self, name, value)
        else:
            raise UnknownFieldError

    def __delitem__(self, name):
        if name in self._fields:
            return delattr(self, name)
        else:
            raise UnknownFieldError

    def __contains__(self, name):
        return name in self.keys() or name in self._serializables

    def __len__(self):
        return len(self.keys())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for k in self._fields:
                if self._data[k] != other._data[k]:
                    return False
            return True
        return NotImplemented

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        try:
            obj = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            obj = '[Bad Unicode data]'

        try:
            class_name = unicode(self.__class__.__name__)
        except (UnicodeEncodeError, UnicodeDecodeError):
            class_name = '[Bad Unicode class name]'

        return u"<%s: %s>" % (class_name, obj)

    def __str__(self):
        return '%s object' % self.__class__.__name__

    def __unicode__(self):
        return '%s object' % self.__class__.__name__


from .transforms import atoms, flatten, expand
from .transforms import convert, to_native, to_dict, to_primitive, export_loop
from .types.compound import ModelType
from .validate import validate
