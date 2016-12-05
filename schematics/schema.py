
from .compat import iteritems, itervalues
from .common import DEFAULT, NONEMPTY
from .datastructures import OrderedDict
from .types import BaseType
from .types.serializable import Serializable

import itertools
import inspect


class SchemaCompatibilityMixin(object):
    """Compatibility layer for previous deprecated Schematics Model API."""

    @property  # deprecated
    def __name__(self):
        return self.name

    @property  # deprecated
    def _options(self):
        return self.options

    @property  # deprecated
    def _validator_functions(self):
        return self.validators

    @property  # deprecated
    def _fields(self):
        return self.fields

    @property  # deprecated
    def _valid_input_keys(self):
        return self.valid_input_keys

    @property  # deprecated
    def _serializables(self):
        return OrderedDict((k, t) for k, t in iteritems(self.fields) if isinstance(t, Serializable))


class Schema(SchemaCompatibilityMixin, object):

    def __init__(self, name, *fields, **kw):
        self.name = name
        self.model = kw.get('model', None)
        self.options = kw.get('options', SchemaOptions())
        self.validators = kw.get('validators', {})
        self.fields = OrderedDict()
        for field in fields:
            self.append_field(field)

    @property
    def valid_input_keys(self):
        return set(itertools.chain(*(t.get_input_keys() for t in itervalues(self.fields))))

    def append_field(self, field):
        self.fields[field.name] = field.type
        field.type._setup(field.name, self.model)  # TODO: remove model reference


class SchemaOptions(object):

    def __init__(self, namespace=None, roles=None, export_level=DEFAULT,
            serialize_when_none=None, export_order=False):
        self.namespace = namespace
        self.roles = roles or {}
        self.export_level = export_level
        if serialize_when_none is True:
            self.export_level = DEFAULT
        elif serialize_when_none is False:
            self.export_level = NONEMPTY
        self.export_order = export_order

    def __iter__(self):
        for key, value in inspect.getmembers(self):
            if not key.startswith("_"):
                yield key, value


class Field(object):

    def __init__(self, name, field_type):
        assert isinstance(field_type, (BaseType, Serializable))
        self.name = name
        self.type = field_type
