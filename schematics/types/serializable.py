import copy
from functools import partial
from types import FunctionType

from ..exceptions import UndefinedValueError
from ..undefined import Undefined

__all__ = ["calculated", "serializable", "Serializable"]


def serializable(arg=None, **kwargs):
    """A serializable is a way to define dynamic serializable fields that are
    derived from other fields.

    >>> from schematics.models import serializable
    >>> class Location(Model):
    ...     country_code = StringType()
    ...     @serializable
    ...     def country_name(self):
    ...         return {'us': 'United States'}[self.country_code]
    ...
    >>> location = Location({'country_code': 'us'})
    >>> location.serialize()
    {'country_name': 'United States', 'country_code': 'us'}
    >>>
    :param type:
        A custom subclass of `BaseType` for enforcing a certain type
        on serialization.
    :param serialized_name:
        The name of this field in the serialized output.
    """
    from .base import BaseType, TypeMeta

    if isinstance(arg, FunctionType):
        decorator = True
        func = arg
        serialized_type = BaseType
    elif arg is None or isinstance(arg, (BaseType, TypeMeta)):
        decorator = False
        serialized_type = arg or kwargs.pop("type", BaseType)
    else:
        raise TypeError("The argument to 'serializable' must be a function or a type.")

    if isinstance(serialized_type, BaseType):
        # `serialized_type` is already a type instance,
        # so update it with the options found in `kwargs`.
        serialized_type._set_export_level(
            kwargs.pop("export_level", None), kwargs.pop("serialize_when_none", None)
        )
        for name, value in kwargs.items():
            setattr(serialized_type, name, value)
    else:
        serialized_type = serialized_type(**kwargs)

    if decorator:
        return Serializable(type=serialized_type, fget=func)
    return partial(Serializable, type=serialized_type)


def calculated(type, fget, fset=None):
    return Serializable(type=type, fget=fget, fset=fset)


class Serializable:
    def __init__(self, fget, type, fset=None):
        self.type = type
        self.fget = fget
        self.fset = fset

    def __getattr__(self, name):
        return getattr(self.type, name)

    def __get__(self, instance, cls):
        if instance is None:
            return self
        value = self.fget(instance)
        if value is Undefined:
            raise UndefinedValueError(instance, self.name)
        return value

    def __set__(self, instance, value):
        if self.fset is None:
            raise AttributeError(f"can't set attribute {self.name}")
        value = self.type.pre_setattr(value)
        self.fset(instance, value)

    def setter(self, fset):
        self.fset = fset
        return self

    def _repr_info(self):
        return self.type.__class__.__name__

    def __deepcopy__(self, memo):
        return self.__class__(self.fget, type=copy.deepcopy(self.type), fset=self.fset)

    def __repr__(self):
        type_ = f"{self.__class__.__name__}({self._repr_info() or ''}) instance"
        model = f" on {self.owner_model.__name__}" if self.owner_model else ""
        field = f" as '{self.name}'" if self.name else ""
        return f"<{type_}{model}{field}>"
