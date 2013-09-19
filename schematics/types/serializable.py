
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

def for_jsonschema(model):
    """Returns a representation of this Schematics class as a JSON schema,
    but not yet serialized to JSON. If certain fields are marked public,
    only those fields will be represented in the schema.

    Certain Schematics fields do not map precisely to JSON schema types or
    formats.
    """
    field_converter = lambda f, v: f.for_jsonschema()
    model_converter = lambda m: for_jsonschema(m)
    gottago = blacklist([], allow_none=True)

    properties = apply_shape(model.__class__, model, field_converter,
                             model_converter, gottago)

    return {
        'type': 'object',
        'title': model.__class__.__name__,
        'properties': properties
    }

def from_jsonschema(schema, model):
    """Generate a Schematics Model class from a JSON schema.  The JSON
    schema's title field will be the name of the class.  You must specify a
    title and at least one property or there will be an AttributeError.
    """
    os = schema
    # this is a desctructive op. This should be only strings/dicts, so this
    # should be cheap
    schema = copy.deepcopy(schema)
    if schema.get('title', False):
        class_name = schema['title']
    else:
        raise AttributeError('JSON Schema missing Model title')

    if 'description' in schema:
        # TODO figure out way to put this in to resulting obj
        description = schema['description']

    if 'properties' in schema:
        model_fields = {}
        for field_name, schema_field in schema['properties'].iteritems():
            field = map_jsonschema_field_to_schematics(schema_field, model)
            model_fields[field_name] = field
        return type(class_name, (model,), model_fields)
    else:
        raise AttributeError('JSON schema missing one or more properties')