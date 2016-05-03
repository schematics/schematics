# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from copy import deepcopy
import inspect
import itertools
from types import FunctionType

from .common import * # pylint: disable=redefined-builtin
from .datastructures import OrderedDict, Context
from .exceptions import *
from .transforms import (
    atoms, export_loop,
    convert, to_native, to_primitive,
)
from .validate import validate, prepare_validator
from .types import BaseType
from .types.serializable import Serializable
from .undefined import Undefined
from .util import get_ident


class FieldDescriptor(object):
    """
    ``FieldDescriptor`` instances serve as field accessors on models.
    """

    def __init__(self, name):
        """
        :param name:
            The field's name
        """
        self.name = name

    def __get__(self, instance, cls):
        """
        For a model instance, returns the field's current value.
        For a model class, returns the field's type object.
        """
        if instance is None:
            return cls._fields[self.name]
        else:
            value = instance._data.get(self.name, Undefined)
            if value is Undefined:
                raise UndefinedValueError(instance, self.name)
            else:
                return value

    def __set__(self, instance, value):
        """
        Sets the field's value.
        """
        field = instance._fields[self.name]
        value = field.pre_setattr(value)
        instance._data[self.name] = value

    def __delete__(self, instance):
        """
        Deletes the field's value.
        """
        del instance._data[self.name]


class ModelOptions(object):
    """
    This class is a container for all model configuration options. Its
    primary purpose is to create an independent instance of a model's
    options for every class.
    """

    def __init__(self, klass, namespace=None, roles=None, export_level=DEFAULT,
                 serialize_when_none=None, export_order=False):
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
        :param export_order:
            Specifies whether to maintain the original field order when exporting
            the model. This entails returning an ``OrderedDictionary`` instead of
            a regular dictionary.
            Default: ``False``
        """
        self.klass = klass
        self.namespace = namespace
        self.roles = roles or {}
        self.export_level = export_level
        if serialize_when_none is True:
            self.export_level = DEFAULT
        elif serialize_when_none is False:
            self.export_level = NONEMPTY
        self.export_order = export_order


class ModelMeta(type):
    """
    Metaclass for Models.
    """

    def __new__(mcs, name, bases, attrs):
        """
        This metaclass adds four attributes to host classes: mcs._fields,
        mcs._serializables, mcs._validator_functions, and mcs._options.

        This function creates those attributes like this:

        ``mcs._fields`` is list of fields that are Schematics types
        ``mcs._serializables`` is a list of ``Serializable`` objects
        ``mcs._validator_functions`` are class-level validation functions
        ``mcs._options`` is the end result of parsing the ``Options`` class
        """

        # Structures used to accumulate meta info
        fields = OrderedDict()
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
            if key.startswith('validate_') and isinstance(value, (FunctionType, classmethod)):
                validator_functions[key[9:]] = prepare_validator(value, 4)
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
        attrs['_field_list'] = list(fields.items())
        attrs['_serializables'] = serializables
        attrs['_validator_functions'] = validator_functions
        attrs['_options'] = options

        klass = type.__new__(mcs, name, bases, attrs)
        klass = str_compat(klass)

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

        klass._valid_input_keys = (
            set(itertools.chain(*(field.get_input_keys() for field in fields.values())))
          | set(serializables))

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


@metaclass(ModelMeta)
class Model(object):

    """
    Enclosure for fields and validation. Same pattern deployed by Django
    models, SQLAlchemy declarative extension and other developer friendly
    libraries.

    :param Mapping raw_data:
        The data to be imported into the model instance.
    :param Mapping deserialize_mapping:
        Can be used to provide alternative input names for fields. Values may be
        strings or lists of strings, keyed by the actual field name.
    :param bool partial:
        Allow partial data to validate. Essentially drops the ``required=True``
        settings from field definitions. Default: True
    :param bool strict:
        Complain about unrecognized keys. Default: True
    """

    __optionsclass__ = ModelOptions

    def __init__(self, raw_data=None, trusted_data=None, deserialize_mapping=None,
                 init=True, partial=True, strict=True, validate=False, app_data=None,
                 **kwargs):

        self._initial = raw_data or {}

        kwargs.setdefault('init_values', init)
        kwargs.setdefault('apply_defaults', init)

        self._data = self.convert(raw_data,
                                  trusted_data=trusted_data, mapping=deserialize_mapping,
                                  partial=partial, strict=strict, validate=validate, new=True,
                                  app_data=app_data, **kwargs)

    def validate(self, partial=False, convert=True, app_data=None, **kwargs):
        """
        Validates the state of the model. If the data is invalid, raises a ``DataError``
        with error messages.

        :param bool partial:
            Allow partial data to validate. Essentially drops the ``required=True``
            settings from field definitions. Default: False
        :param convert:
            Controls whether to perform import conversion before validating.
            Can be turned off to skip an unnecessary conversion step if all values
            are known to have the right datatypes (e.g., when validating immediately
            after the initial import). Default: True
        """
        data = self.convert(self, validate=True, partial=partial, convert=convert,
                            app_data=app_data, **kwargs)

        if convert:
            self._data.update(**data)

    def import_data(self, raw_data, recursive=False, **kwargs):
        """
        Converts and imports the raw data into an existing model instance.

        :param raw_data:
            The data to be imported.
        """
        self._data = self.convert(raw_data, trusted_data=self, recursive=recursive, **kwargs)
        return self

    @classmethod
    def convert(cls, raw_data, context=None, **kw):
        """
        Converts the raw data into richer Python constructs according to the
        fields on the model

        :param raw_data:
            The data to be converted
        """
        _validate = getattr(context, 'validate', None) or kw.get('validate', False)
        if _validate:
            return validate(cls, raw_data, oo=True, context=context, **kw)
        else:
            return convert(cls, raw_data, oo=True, context=context, **kw)

    def export(self, field_converter=None, role=None, app_data=None, **kwargs):
        return export_loop(self.__class__, self, field_converter=field_converter,
                           role=role, app_data=app_data, **kwargs)

    def to_native(self, role=None, app_data=None, **kwargs):
        return to_native(self.__class__, self, role=role, app_data=app_data, **kwargs)

    def to_primitive(self, role=None, app_data=None, **kwargs):
        return to_primitive(self.__class__, self, role=role, app_data=app_data, **kwargs)

    def serialize(self, *args, **kwargs):
        return self.to_primitive(*args, **kwargs)

    def atoms(self):
        """
        Iterator for the atomic components of a model definition and relevant
        data that creates a 3-tuple of the field's name, its type instance and
        its value.
        """
        return atoms(self.__class__, self)

    def __iter__(self):
        return (k for k in self._fields if k in self._data)

    def keys(self):
        return list(iter(self))

    def items(self):
        return [(k, self._data[k]) for k in self]

    def values(self):
        return [self._data[k] for k in self]

    def get(self, key, default=None):
        return getattr(self, key, default)

    @classmethod
    def get_mock_object(cls, context=None, overrides={}):
        """Get a mock object.

        :param dict context:
        :param dict overrides: overrides for the model
        """
        context = Context._make(context)
        context._setdefault('memo', set())
        context.memo.add(cls)
        values = {}
        for name, field in cls.fields.items():
            if name in overrides:
                continue
            if getattr(field, 'model_class', None) in context.memo:
                continue
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
            raise UnknownFieldError(self, name)

    def __setitem__(self, name, value):
        if name in self._fields:
            return setattr(self, name, value)
        else:
            raise UnknownFieldError(self, name)

    def __delitem__(self, name):
        if name in self._fields:
            return delattr(self, name)
        else:
            raise UnknownFieldError(self, name)

    def __contains__(self, name):
        return name in self._data \
            or name in self._serializables and getattr(self, name, Undefined) is not Undefined

    def __len__(self):
        return len(self._data)

    def __eq__(self, other, memo=set()):
        if self is other:
            return True
        if type(self) is not type(other):
            return NotImplemented
        key = (id(self), id(other), get_ident())
        if key in memo:
            return True
        else:
            memo.add(key)
        try:
            return self._data == other._data
        finally:
            memo.remove(key)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        model = self.__class__.__name__
        info = self._repr_info()
        if info:
            return '<%s: %s>' % (model, info)
        else:
            return '<%s instance>' % model

    def _repr_info(self):
        """
        Subclasses may implement this method to augment the ``__repr__()`` output for the instance::

            class Person(Model):
                ...
                def _repr_info(self):
                    return self.name

            >>> Person({'name': 'Mr. Pink'})
            <Person: Mr. Pink>
        """
        return None


__all__ = module_exports(__name__)

