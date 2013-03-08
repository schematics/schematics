

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

    :param serialized_name:
        The name of this field in the serialized output.
    :param serialized_class:
        A custom subclass of `Serializable` if you want to override
        `to_primitive`.

    """
    def wrapper(f):
        SerializableClass = kwargs.get("serialized_class", Serializable)
        serialized_name = kwargs.get("serialized_name", None)
        return SerializableClass(f, serialized_name=serialized_name)

    if len(args) == 1 and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        return wrapper(args[0])
    else:
        return wrapper


class Serializable(property):

    def __init__(self, *args, **kwargs):
        self.serialized_name = kwargs.pop("serialized_name", None)

        super(Serializable, self).__init__(*args, **kwargs)

    def to_primitive(self, value):
        return value
