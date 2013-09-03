
from schematics.types.base import BaseType


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
    :param type:
        A custom subclass of `BaseType` for enforcing a certain type
        on serialization.
    :param serialized_name:
        The name of this field in the serialized output.
    """
    def wrapper(f):
        serialized_type = kwargs.pop("type", BaseType())
        serialized_name = kwargs.pop("serialized_name", None)
        serialize_when_none = kwargs.pop("serialize_when_none", True)
        return Serializable(f, type=serialized_type, serialized_name=serialized_name,
            serialize_when_none=serialize_when_none)

    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        return wrapper(args[0])
    else:
        return wrapper


class Serializable(object):

    def __init__(self, f, type=None, serialized_name=None, serialize_when_none=True):
        self.f = f
        self.type = type
        self.serialized_name = serialized_name
        self.serialize_when_none = serialize_when_none

    def __get__(self, object, owner):
        return self.f(object)

    def to_native(self, value):
        return self.type.to_native(value)

    def to_primitive(self, value):
        return self.type.to_primitive(value)
