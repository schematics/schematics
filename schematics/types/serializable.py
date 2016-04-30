# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import copy
from functools import partial
from types import FunctionType

from ..common import *
from ..exceptions import *
from ..undefined import Undefined
from ..util import setdefault

from .base import BaseType, TypeMeta


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
        serialized_type._set_export_level(kwargs.pop('export_level', None),
                                          kwargs.pop("serialize_when_none", None))
        for name, value in kwargs.items():
            setattr(serialized_type, name, value)
    else:
        serialized_type = serialized_type(**kwargs)

    if decorator:
        return Serializable(func, serialized_type)
    else:
        return partial(Serializable, type=serialized_type)


class Serializable(object):

    def __init__(self, func, type):
        self.func = func
        self.type = type

    def __getattr__(self, name):
        return getattr(self.type, name)

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            if value is Undefined:
                raise UndefinedValueError(instance, self.name)
            else:
                return value

    def __deepcopy__(self, memo):
        return self.__class__(self.func, copy.deepcopy(self.type))


__all__ = module_exports(__name__)
