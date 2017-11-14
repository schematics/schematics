from collections import OrderedDict

from typing import *
from .models import Model
from .types.base import BaseType
from .types.serializable import Serializable
from .util import Constant

FilterType = Callable[[str, Any], bool]


class Schema(object):
    fields = OrderedDict[str, Union[BaseType, Serializable]]
    options = 'SchemaOptions'
    validiators = Dict

    def __init__(self, name: str, *fields: Field, model: Optional[Model] = ..., options: 'SchemaOptions' = ..., validators: Dict = ...) -> None: ...
    @property
    def valid_input_keys(self) -> Set[str]: ...
    def append_field(self, field: Field) -> None: ...


class SchemaOptions:
    namespace : str
    roles : Dict[str, FilterType]
    export_level : Constant
    serialize_when_none : bool
    export_order : bool

    def __init__(self, namespace: Optional[str] = ..., roles: Optional[Dict[str, FilterType]] =..., export_level=...,
            serialize_when_none: Optional[bool] = ..., export_order: bool = ...) -> None: ...

    # def __iter__(self):
    #     for key, value in inspect.getmembers(self):
    #         if not key.startswith("_"):
    #             yield key, value


class Field:

    name : str
    type : Union[BaseType, Serializable]

    def __init__(self, name: str, field_type: Union[BaseType, Serializable]) -> None: ...
    def is_settable(self) -> bool: ...
