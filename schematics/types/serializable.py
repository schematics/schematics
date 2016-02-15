# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import copy

from ..common import * # pylint: disable=redefined-builtin
from ..util import setdefault

from .base import BaseType


def serializable(*args, **kwargs):
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
    def wrapper(func):

        serialized_type = kwargs.pop("type", BaseType)

        if isinstance(serialized_type, BaseType):
            # If `serialized_type` is already an instance, update it with the options
            # found in `kwargs`. This is necessary because historically certain options
            # were stored on the `Serializable` itself instead of the underlying field.
            serialized_type._set_export_level(
                kwargs.pop('export_level', None), kwargs.pop("serialize_when_none", None))
            for name, value in kwargs.items():
                setdefault(serialized_type, name, value, overwrite_none=True)
        else:
            serialized_type = serialized_type(**kwargs)

        return Serializable(func, serialized_type)

    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        return wrapper(args[0])
    else:
        return wrapper


class Serializable(object):

    def __init__(self, func, type):
        self.func = func
        self.type = type

    def __getattr__(self, name):
        return getattr(self.type, name)

    def __get__(self, instance, cls):
        if instance:
            return self.func(instance)
        else:
            return self

    def __deepcopy__(self, memo):
        return self.__class__(self.func, copy.deepcopy(self.type))


__all__ = module_exports(__name__)

