
from collections import OrderedDict

from .compat import itervalues
from .common import DEFAULT, NONEMPTY
from .types import BaseType
from .types.serializable import Serializable

import itertools
import inspect

if False:
    from typing import *
    from .models import Model


class Schema(object):

    def __init__(self, name, *fields, **kw):
        # type: (str, *Field, Any) -> None
        self.name = name
        self.model = kw.get('model', None)  # type: Optional[Model]
        self.options = kw.get('options', SchemaOptions())
        self.validators = kw.get('validators', {})
        self.fields = OrderedDict()  # type: OrderedDict[str, Union[BaseType, Serializable]]
        for field in fields:
            self.append_field(field)

    @property
    def valid_input_keys(self):
        # type: () -> Set[str]
        return set(itertools.chain(*(t.get_input_keys() for t in itervalues(self.fields))))

    def append_field(self, field):
        # type: (Field) -> None
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

    __slots__ = ('name', 'type')

    def __init__(self, name, field_type):
        # type: (str, Union[BaseType, Serializable]) -> None
        assert isinstance(field_type, (BaseType, Serializable))
        self.name = name
        self.type = field_type

    def is_settable(self):
        return getattr(self.type, 'fset', None) is not None
