# encoding=utf-8

import inspect
import itertools

from .types import BaseType
from .types.bind import _bind
from .types.serializable import Serializable
from .exceptions import ValidationError
from .serialize import serialize, flatten, expand
from .datastructures import OrderedDict


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
        model._data[self.name] = field(value)

    def __delete__(self, model):
        if self.name not in model._fields:
            raise AttributeError('%r has no attribute %r' %
                                 (type(model).__name__, self.name))
        del model._fields[self.name]


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
        fields = OrderedDict()
        serializables = {}
        validator_functions = {}  # Model level

        for base in reversed(bases):
            if hasattr(base, 'fields'):
                fields.update(base.fields)
            if hasattr(base, '_unbound_serializables'):
                serializables.update(base._unbound_serializables)
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
        attrs['_unbound_serializables'] = serializables
        attrs['_unbound_fields'] = fields

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
        return cls._unbound_fields

    def __iter__(self):
        return itertools.chain(
            self._unbound_fields.iteritems(),
            self._unbound_serializables.iteritems()
        )


class Model(object):
    """Enclosure for fields and validation. Same pattern deployed by Django
    models, SQLAlchemy declarative extension and other developer friendly
    libraries.

    :param data:
        Data to validate and apply to the object.
    :param partial:
        Allow partial data; useful for PATCH requests. Essentilly drops the
        ``required=True`` arguments from field definitions. Default: ``True``
    :param raises:
        When ``True``, raise ``ValidationError`` at the end if errors were
        found. Default: ``True``

    """

    __metaclass__ = ModelMeta
    __optionsclass__ = ModelOptions

    def __init__(self, data=None, partial=True, raises=True):
        if data is None:
            data = {}

        self._initial = data

        self._fields = OrderedDict()
        self._serializables = {}
        self._memo = {}
        for name, field in self._unbound_fields.iteritems():
            self._fields[name] = _bind(field, self, self._memo)

        for name, field in self._unbound_serializables.iteritems():
            self._serializables[name] = _bind(field, self, self._memo)

        self.reset()
        self.validate(data, partial=partial, raises=raises)

    def reset(self):
        self._data = {}
        self.errors = {}

    @classmethod
    def from_flat(cls, data):
        return cls(expand(data))

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

    def validate(self, input_data=None, partial=False, strict=False, raises=True):
        """Validates incoming untrusted data. If ``partial`` is set it will. If
        data is valid, update the object state and return ``True``, else set
        ``self.errors`` and return ``False``.

        The internal state of data and errors are kept in ``self._data`` and
        ``self.errors``, respectively.

        :param input_data:
            A ``dict`` or ``dict``-like structure for incoming data.
        :param partial:
            Allow partial data to validate; useful for PATCH requests.
            Essentilly drops the ``required=True`` arguments from field
            definitions. Default: False
        :param strict:
            Complain about unrecognized keys. Default: False
        :param raises:
            When ``True``, raise ``ValidationError`` at the end if errors were
            found. Default: True

        """

        errors = {}
        data = {}

        if input_data is None:
            input_data = {}

        if partial:
            needs_check = lambda field_name, field: field_name in input_data
        else:
            needs_check = lambda field_name, field: field.required or field_name in input_data

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

                # Fallback to the internal value
                if serialized_field_name in input_data:
                    field_value = input_data.get(serialized_field_name)
                else:
                    field_value = self._data.get(serialized_field_name)

                try:
                    value = field.validate(field_value)

                    if field_name in self._validator_functions:
                        context = dict(self._data, **data)
                        value = self._validator_functions[field_name](self, context, value)

                    data[field_name] = value
                except ValidationError, e:
                    errors[serialized_field_name] = e.messages

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
        return self.iter()

    def iter(self, include_serializables=True):
        if include_serializables:
            all_fields = itertools.chain(
                self._fields.iteritems(),
                self._serializables.iteritems()
            )
        else:
            all_fields = self._fields.iteritems()

        return ((field_name, field, self[field_name]) for field_name, field in all_fields)

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
