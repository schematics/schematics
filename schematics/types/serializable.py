
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
    def wrapper(func):
        serialized_type = kwargs.pop("type", BaseType())  # pylint: disable=no-value-for-parameter
        serialized_name = kwargs.pop("serialized_name", None)
        serialize_when_none = kwargs.pop("serialize_when_none", True)
        return Serializable(func, type=serialized_type, serialized_name=serialized_name,
                            serialize_when_none=serialize_when_none)

    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        return wrapper(args[0])
    else:
        return wrapper


class Serializable(object):

    def __init__(self, func, type=None, serialized_name=None, serialize_when_none=True):
        self.func = func
        self.type = type
        self.typeclass = type.__class__
        self.serialized_name = serialized_name
        self.serialize_when_none = serialize_when_none
        self.is_compound = self.type.is_compound

    def __get__(self, instance, cls):
        if instance:
            return self.func(instance)
        else:
            return self

    def convert(self, value, context=None):
        return self.type.convert(value, context)

    def export(self, value, target, context=None):
        return self.type.export(value, target, context)

