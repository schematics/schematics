# encoding=utf-8

import inspect
import itertools

from .types import BaseType
from .types.bind import _bind
from .exceptions import ValidationError
from .serialize import serialize, flatten, expand


def serializable(*args, **kwargs):
    """A serializable is a way to define dynamic serializable fields that are
    derived from other fields.

    >>> from schematics.models import serializable
    >>> class Location(Model):
    ...     country_code = StringType()
    ...     @serializable
    ...     def country_name(self):
    ...         return {'us': u'United States'}[self.country_code]
    ...
    >>> location = Location({'country_code': 'us'})
    >>> location.serialize()
    {'country_name': u'United States', 'country_code': u'us'}
    >>>

    :param serialized_name:
        The name of this field in the serialized output.
    :param serialized_class:
        A custom subclass of `Serializable` if you want to override `to_primitive`

    """
    def wrapper(f):
        SerializableClass = kwargs.get("serialized_class", Serializable)
        return SerializableClass(f, serialized_name=kwargs.get("serialized_name", None))

    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        return wrapper(args[0])
    else:
        return wrapper


class Serializable(property):

    def __init__(self, *args, **kwargs):
        self.serialized_name = kwargs.pop("serialized_name", None)

        super(Serializable, self).__init__(*args, **kwargs)

    def to_primitive(self, value):
        return value


class ModelOptions(object):
    """This class is a container for all metaclass configuration options. It's
    primary purpose is to create an instance of a model's options for every
    instance of a model.

    It also creates errors in cases where unknown options parameters are found.
    """
    def __init__(self, klass, namespace=None, roles=None):
        self.klass = klass
        self.namespace = namespace
        self.roles = roles or {}


class ModelMeta(type):
    """Meta class for Models. Handles model inheritance and Options.
    """

    def __new__(cls, name, bases, attrs):
        fields = {}
        serializables = {}

        for base in reversed(bases):
            if hasattr(base, 'fields'):
                fields.update(base.fields)

            if hasattr(base, '_serializables'):
                serializables.update(base._serializables)

        for key, value in attrs.iteritems():
            if isinstance(value, BaseType):
                fields[key] = value
            if isinstance(value, Serializable):
                serializables[key] = value

        for key, field in fields.iteritems():
            attrs[key] = FieldDescriptor(key)  # For accessing internal data by field name attributes

        # Create a valid ModelOptions instance in `_options`
        _options_class = getattr(attrs, '__classoptions__', ModelOptions)
        _options_members = {}
        if 'Options' in attrs:
            for k, v in inspect.getmembers(attrs['Options']):
                if not k.startswith("_"):
                    _options_members[k] = v
        attrs['_options'] = _options_class(cls, **_options_members)

        attrs["_serializables"] = serializables
        attrs['_unbound_fields'] = fields

        klass = type.__new__(cls, name, bases, attrs)

        for field in fields.values():
            field.owner_model = klass

        return klass

    @property
    def fields(cls):
        return cls._unbound_fields


class FieldDescriptor(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, type=None):
        try:
            if obj is None:
                return type.fields[self.name]
            return obj._data[self.name]
        except KeyError:
            raise AttributeError(self.name)

    def init_model(self, field, value):
        """If raw values are assigned to a ModelType assign a model instance."""
        if isinstance(value, dict):  # But not an instance, make it one
            model = field.model_class(data=value)
            return model
        return value

    def __set__(self, obj, value):
        field = obj._fields[self.name]
        # if isinstance(field, MultiType):
        #     if isinstance(value, list):
        #         value = [self.init_model(field, item) for item in value]
        #     else:
        #         value = self.init_model(field, value)
        #     # Also init_model for things underneath
        obj._data[self.name] = field(value)

    def __delete__(self, obj):
        if self.name not in obj._fields:
            raise AttributeError('%r has no attribute %r' %
                                 (type(obj).__name__, self.name))
        del obj._fields[self.name]


class Model(object):
    """Enclosure for fields and validation. Same pattern deployed by Django
    models, SQLAlchemy declarative extension and other developer friendly
    libraries.

    >>> from schematics.models import Model
    >>> from schematics.types import StringType
    >>> class Person(Model):
    ...     name = StringType(required=True)
    ...
    >>> person = Person({'name': u'Joey Bada$$'})
    >>>

    Let’s see some validation

    >>> person = Person(raises=False)
    >>> person.errors
    {'name': [u'This field is required.']}
    >>>

    """

    __metaclass__ = ModelMeta
    __optionsclass__ = ModelOptions

    def __init__(self, data=None, partial=False, raises=True):
        """

        :param partial:
            Allow partial data; useful for PATCH requests. Essentilly drops the
            `required=True` arguments from field definitions. Default: False
        :param raises:
            When `True`, raise `ValidationError` at the end if errors were
            found. Default: True

        """
        if data is None:
            data = {}

        self._initial = data

        self._fields = {}
        self._memo = {}
        for name, field in self._unbound_fields.iteritems():
            self._fields[name] = _bind(field, self, self._memo)

        self.reset()
        self.validate(data, partial=partial, raises=raises)

    def reset(self):
        self.errors = {}
        self._data = {}

    @classmethod
    def from_flat(cls, data):
        return cls(expand(data))

    def serialize(self, role=None, flat=False):
        """Return data as it would be validated. No filtering of output unless
        role is defined.
        """
        if flat:
            return flatten(self, role)
        else:
            return serialize(self, role)

    def validate(self, input_data, partial=False, strict=False, raises=False):
        """Validates incoming untrusted data. If `partial` is set it will.
        If data is valid, update the object state and return `True`, else set
        `self.errors` and return `False`.

        The internal state of data and errors are kept in `self._data` and
        `self.errors`, respectively.

        :param input_data:
            A `dict` or `dict`-like structure for incoming data.
        :param partial:
            Allow partial data to validate; useful for PATCH requests.
            Essentilly drops the `required=True` arguments from field
            definitions. Default: False
        :param strict:
            Complain about unrecognized keys. Default: False
        :param raises:
            When `True`, raise `ValidationError` at the end if errors were
            found. Default: False

        """

        errors = {}
        data = {}

        if partial:
            needs_check = lambda k, v: k in input_data
        else:
            needs_check = lambda k, v: v.required or k in input_data

        # Validate data based on cls's structure
        for field_name, field in self._fields.iteritems():
            # Rely on parameter for whether or not we should check value
            serialized_field_name = field.serialized_name or field_name
            if needs_check(serialized_field_name, field):
                # What does `Field.required` mean? Does it merely
                # require presence or the value not be None? Here it means the
                # value must not be None. However! We require the presence even
                # though required is set to None if this is not a partial update.
                # For this to validate the user should pick a partial validate.

                field_value = input_data.get(serialized_field_name)

                if field.required and field_value is None:
                    errors[field_name] = [u"This field is required."]
                    continue

                try:
                    data[field_name] = field.validate(field_value)
                except ValidationError, e:
                    errors[field_name] = e.messages

        # Report rogue fields as errors if `strict`
        if strict:
            # set takes iterables, iterating over keys in this instance
            rogues_found = set(data) - set(self._fields)
            if len(rogues_found) > 0:
                for field_name in rogues_found:
                    errors[field_name] = [u'%s is an illegal field.' % field_name]

        if errors:
            self.errors = errors
            if raises:
                raise ValidationError(errors)
            return False

        # Set internal data and touch the TypeDescriptors by setattr
        self._data.update(**data)

        for field_name, field in self._fields.iteritems():
            default = field.default
            if callable(field.default):
                default = field.default()
            data.setdefault(field_name, default)

            self._data[field_name] = data.get(field_name)

        return True

    def __iter__(self):
        return itertools.chain(
            self._fields.iteritems(),
            self._serializables.iteritems()
        )

    def __getitem__(self, name):
        try:
            if name in self._data or name in self._serializables:
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
        if key in self:
            return self[key]
        return default

    # Representation Descriptors

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return u"<%s: %s>" % (self.__class__.__name__, u)

    def __unicode__(self):
        return '%s object' % self.__class__.__name__
