import inspect

from .types import BaseType
from .types.compound import MultiType


class ModelOptions(object):
    """This class is a container for all metaclass configuration options. It's
    primary purpose is to create an instance of a model's options for every
    instance of a model.

    It also creates errors in cases where unknown options parameters are found.
    """
    def __init__(self, klass, namespace=None, roles={}):
        self.klass = klass
        self.namespace = namespace
        self.roles = roles


class ModelMeta(type):
    """Meta class for Models. Handles model inheritance and Options.
    """

    def __new__(cls, name, bases, attrs):

        fields = {}

        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(base._fields)

        for key, value in attrs.iteritems():
            if isinstance(value, BaseType):
                fields[key] = value
                attrs[key] = FieldDescriptor(key)

        # Create a valid ModelOptions instance in `_options`
        _options_class = getattr(attrs, '__classoptions__', ModelOptions)
        _options_members = {}
        if 'Options' in attrs:
            for k, v in inspect.getmembers(attrs['Options']):
                if not k.startswith("_"):
                    _options_members[k] = v
        attrs['_options'] = _options_class(cls, **_options_members)

        attrs['_fields'] = fields
        klass = type.__new__(cls, name, bases, attrs)

        for field in fields.values():
            field.owner_model = klass

        return klass

    @property
    def fields(cls):
        return cls._fields


class FieldDescriptor(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, type=None):
        try:
            if obj is None:
                return type._fields[self.name]
            return obj.data[self.name]
        except KeyError:
            raise AttributeError(self.name)

    def init_model(self, obj, value):
        """If raw values are assigned to a ModelType assign a model instance."""
        if isinstance(value, dict):  # But not an instance, make it one
            value = obj.fields[self.name].model_class(**value)
        return value

    def __set__(self, obj, value):
        if isinstance(obj.fields[self.name], MultiType):
            # print "OBJ", obj.fields[self.name].__class__.__name__, value
            if isinstance(value, list):
                value = [self.init_model(obj, item) for item in value]
            else:
                value = self.init_model(obj, value)
        obj.data[self.name] = value

    def __delete__(self, obj):
        if self.name not in obj.fields:
            raise AttributeError('%r has no attribute %r' %
                                 (type(obj).__name__, self.name))
        del obj.fields[self.name]


class Model(object):

    __metaclass__ = ModelMeta
    __optionsclass__ = ModelOptions

    def __init__(self, **values):
        """Initiating a model with data is assumed to be safe. To trigger
        validation for unsafe input, use the `validate` classmethod.

        We expand data for fields that implement

        """

        self.initial = values
        self.reset()

        self._field_names = dict(self._primitive_field_names())

        for name, field in self.fields.iteritems():
            serialized_name = self._field_names[name]
            if hasattr(field, "default"):
                value = values.setdefault(serialized_name, field.default)
            setattr(self, name, value)

    def _primitive_field_names(self):
        for name in self.fields:
            yield (name, self.fields[name].serialized_name or name)

    def reset(self):
        self.data = self.initial.copy()
        self.errors = {}

    def serialize(self, role=None):
        """Return data as it would be validated. No filtering of output unless
        role is defined.
        """
        from .serialize import serialize
        return serialize(self, role)

    def _autodiscover_data(self):
        """Called by `validate` if no data is provided.  Finds the
        matching data from the request object by default depending
        on the default submit method of the form.
        """
        raise NotImplementedError(
            'No data passed to the validation and data auto discovery not '
            'implemented.  Override the `_autodiscover_data` method.')

    def validate(self, data=None, partial=False, strict=False):
        """Validates incoming untrusted data. If `partial` is set it will allow
        partial data to validate, useful for PATCH requests. Returns a clean
        instance.

        Loops across the fields in a Model definition, `cls`, and attempts
        validation on any fields that require a check, as signalled by the
        `needs_check` function.

        The basis for validation is `cls`, so fields are located in `cls` and
        mapped to an entry in `items`.  This entry is then validated against the
        field's validation function.

        A (data, errors) tuple is returned::

            >>> items, errors = _validate(MyModel, lambda: True, foreign_data)
            >>> if not errors:
            >>>     model = MyModel(**items)
            >>> else:
            >>>     abort(422, errors=errors)
            >>>

        """

        errors = {}

        if data is None:
            data = self._autodiscover_data()

        if partial:
            needs_check = lambda k, v: k in data
        else:
            needs_check = lambda k, v: v.required or k in data

        # Validate data based on cls's structure
        for field_name, field in self._fields.iteritems():
            # Rely on parameter for whether or not we should check value
            if needs_check(field_name, field):
                # Here we must ask what `Field.required` means. Does it merely
                # require presence or the value not be None? Here it means the
                # value must not be None. However! We require the presence even
                # though required is set to None. For this to validate the user
                # should pick a partial validate.

                field_value = data.setdefault(field_name)

                if field.required and field_value is None:
                    errors[field_name] = [u"This field is required"]
                    continue

                if field.validate(field_value):
                    data[field_name] = field.clean
                else:
                    errors[field_name] = field.errors

        # Report rogue fields as errors if `strict`
        if strict:
            # set takes iterables, iterating over keys in this instance
            rogues_found = set(data) - set(self._fields)
            if len(rogues_found) > 0:
                for field_name in rogues_found:
                    errors[field_name] = [u'%s is an illegal field' % field_name]

        if errors:
            self.errors = errors
            return False

        self.data.update(**data)
        return True

    def __iter__(self):
        return iter(self._fields)

    @property
    def fields(self):
        return self._fields

    def __getitem__(self, name):
        try:
            if name in self.data:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        # Ensure that the field exists before settings its value
        if name not in self.data:
            raise KeyError(name)
        return setattr(self, name, value)

    def __contains__(self, name):
        return name in self.data

    def __len__(self):
        return len(self.data)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            keys = self.fields
            for key in keys:
                if self[key] != other[key]:
                    return False
            return True
        return False

    # Representation Descriptors

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return u"<%s: %s>" % (self.__class__.__name__, u)

    def __unicode__(self):
        return '%s object' % self.__class__.__name__
