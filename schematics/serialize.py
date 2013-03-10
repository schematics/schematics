"""Serialize

Serialization is essentially the process of converting a model into some other
format.  The current formats supported are a Python dict and a JSON string. One
could use Python's cPickle module or a msgpack too.

The logic includes conversions from Schematics representation into formats
suitable for some serialization method.  For example, Python datetime's will
blow up json.dumps so we first convert the date into ISO8601 format.

Serializing a model instance then looks like this:

    a_dict = to_python(instance)

There is additional logic that allows user's to remove fields from
serialization based on the concept of configured roles.  The idea here is that
it's typical to not want to share every field for some reason.  A whilelist
and blacklist mechanism is provided for those fields.  The actual logic only
requires a function so the behavior of the system is fully customizable.

A class with role access specified looks like this:

    class SomeModel(Model):
        field_a = ...

        class Options:
            roles = {
                'owner': blacklist('field_a'),
                'public': whitelist('field_b', 'field_c'),
            }

Serializing data against a role then looks like this:

    a_dict = make_safe_python(SomeModel, my_data, 'public')

I can convert the data to JSON just as easily too.

    a_str = make_safe_json(SomeModel, my_data, 'public')

In addition to these mechanisms existing, they are fully recursive and will
expand models if they are used as fields.  They will also apply a role
recursively which allows users to embed models with unique role systems inside
container models.

That looks like this in code:

    class SomeModel(Model):
        name = StringType()
        email = EmailType()
        is_active = BooleanType()
        class Options:
            roles = {
                'owner': blacklist('is_active'),
                'public': whitelist('username', 'name'),
            }
    
    class BlogPost(Model):
        title = StringType()    
        content = StringType()
        author = ModelType(Author)
        post_date = DateTimeType(default=datetime.datetime.now)
        comments = ListType(ModelType(Comment))
        deleted = BooleanType()   
        class Options:
            roles = {
                'owner': whotelist(),
                'public': whitelist('author', 'content', 'comments'),
            }        
"""

import copy
import collections

from schematics.types import schematic_types
from schematics.base import json
from schematics.models import Model


###
### Serialization Shaping Functions
###

def _reduce_loop(model, instance_or_dict, field_converter):
    """Each field's name, the field instance and the field's value are
    collected in a truple and yielded, making this a generator.
    """
    for field_name in instance_or_dict:
        field_instance = model._fields[field_name]
        field_value = instance_or_dict[field_name]
        yield (field_name, field_instance, field_value)


def apply_shape(model, instance_or_dict, field_converter, model_converter,
                gottago, allow_none=False, convert_none=False):
    """
    """
    model_dict = {}

    ### Loop over each field and either evict it or convert it
    for truple in _reduce_loop(model, instance_or_dict, field_converter):
        ### Break 3-tuple out
        (field_name, field_instance, field_value) = truple

        ### Check for alternate field name
        serialized_name = field_name
        if field_instance.minimized_field_name:
            serialized_name = field_instance.minimized_field_name
        elif field_instance.print_name:
            serialized_name = field_instance.print_name

        ### Evict field if it's gotta go
        if gottago(field_name, field_value):
            continue

        ### Convert field as single model
        elif isinstance(field_value, Model):
            model_dict[serialized_name] = model_converter(field_value)
            
        ### Convert field as list of models
        elif isinstance(field_value, list): # and len(field_value) > 0:
            if field_value and len(field_value) > 0 and isinstance(field_value[0], Model):
                model_dict[serialized_name] = [model_converter(vi)
                                               for vi in field_value]
            else:
                model_dict[serialized_name] = field_converter(field_instance,
                                                              field_value)
                
        ### Convert field as single field
        else:
            if field_value is None and not allow_none:
                continue  # throw it away
            elif field_value is None and convert_none \
                       or field_value is not None:
                model_dict[serialized_name] = field_converter(field_instance,
                                                              field_value)
            elif field_value is None and allow_none:
                model_dict[serialized_name] = None

    return model_dict


###
### Field Access Functions 
###

def wholelist(*field_list):
    """Returns a function that evicts nothing. Exists mainly to be an explicit
    allowance of all fields instead of a using an empty blacklist.
    """
    def _wholelist(k, v):
        return False
    return _wholelist

    
def whitelist(*field_list):
    """Returns a function that operates as a whitelist for the provided list of
    fields.

    A whitelist is a list of fields explicitly named that are allowed.
    """
    ### Default to rejecting the value
    _whitelist = lambda k, v: True

    if field_list is not None and len(field_list) > 0:
        def _whitelist(k, v):
            return k not in field_list

    return _whitelist


def blacklist(*field_list):
    """Returns a function that operates as a blacklist for the provided list of
    fields.

    A blacklist is a list of fields explicitly named that are not allowed.
    """
    ### Default to not rejecting the value
    _blacklist = lambda k, v: False
    
    if field_list is not None and len(field_list) > 0:
        def _blacklist(k, v):
            return k in field_list
            
    return _blacklist


###
### Data Serialization
###

def to_python(model, gottago=wholelist(), **kw):
    field_converter = lambda f, v: f.for_python(v)
    model_converter = lambda m: to_python(m)

    return apply_shape(model.__class__, model, field_converter,
                       model_converter, gottago, **kw)


def to_json(model, gottago=wholelist(), encode=True, sort_keys=False, **kw):
    field_converter = lambda f, v: f.for_json(v)
    model_converter = lambda m: to_json(m, encode=False, sort_keys=sort_keys)

    data = apply_shape(model.__class__, model, field_converter,
                       model_converter, gottago, **kw)

    if encode:
        return json.dumps(data, sort_keys=sort_keys)
    else:
        return data


def make_safe_python(model, instance_or_dict, role, **kw):
    field_converter = lambda f, v: f.for_python(v)
    model_converter = lambda m: make_safe_python(m.__class__, m, role, **kw)

    gottago = lambda k,v: True
    if role in model._options.roles:
        gottago = model._options.roles[role]

    return apply_shape(model, instance_or_dict, field_converter, model_converter,
                       gottago, **kw)
    

def make_safe_json(model, instance_or_dict, role, encode=True, sort_keys=False,
                   **kw):
    field_converter = lambda f, v: f.for_json(v)
    model_converter = lambda m: make_safe_json(m.__class__, m, role,
                                               encode=False,
                                               sort_keys=sort_keys)

    gottago = lambda k,v: True
    if role in model._options.roles:
        gottago = model._options.roles[role]

    data = apply_shape(model, instance_or_dict, field_converter, model_converter,
                       gottago, **kw)

    if encode:
        return json.dumps(data, sort_keys=sort_keys)
    else:
        return data


###
### Schema Serialization
###

### Parameters for serialization to JSONSchema
schema_kwargs_to_schematics = {
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'pattern': 'regex',
    'minimum': 'min_value',
    'maximum': 'max_value',
}


def for_jsonschema(model):
    """Returns a representation of this Schematics class as a JSON schema,
    but not yet serialized to JSON. If certain fields are marked public,
    only those fields will be represented in the schema.

    Certain Schematics fields do not map precisely to JSON schema types or
    formats.
    """
    field_converter = lambda f, v: f.for_jsonschema()
    model_converter = lambda m: for_jsonschema(m)
    gottago = blacklist([])

    if callable(model):
        properties = apply_shape(model, model(), field_converter,
                                 model_converter, gottago, allow_none=True,
                                 convert_none=True)
    else:
        properties = apply_shape(model.__class__, model, field_converter,
                                 model_converter, gottago, allow_none=True,
                                 convert_none=True)
        

    return {
        'type': 'object',
        'title': model._model_name,
        'properties': properties
    }


def to_jsonschema(model):
    """Returns a representation of this Structures class as a JSON schema.
    If certain fields are marked public, only those fields will be
    represented in the schema.

    Certain Structures fields do not map precisely to JSON schema types or
    formats.
    """
    return json.dumps(for_jsonschema(model))


def from_jsonschema(schema, model=Model):
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
        clss = type(str(class_name), (model,), model_fields)
        return clss
    else:
        raise AttributeError('JSON schema missing one or more properties')


def map_jsonschema_field_to_schematics(schema_field, base_class,
                                       field_name=None):
    
    # get the kind of field this is
    if not 'type' in schema_field:
        return  # not data, so ignore
    
    tipe = schema_field.pop('type')
    fmt = schema_field.pop('format', None)

    schematic_field_type = schematic_types.get((tipe, fmt,), None)
    if not schematic_field_type:
        raise DictFieldNotFound

    kwargs = {}

    # List types
    if tipe == 'array':
        items = schema_field.pop('items', None)
        
        # any possible item isn't allowed by listfield        
        if items == None:  
            raise NotImplementedError
        # list of a single type
        elif isinstance(items, dict):
            items = [items]
            
        kwargs['fields'] = [map_jsonschema_field_to_schematics(item, base_class)
                            for item in items]

    # Embedded objects        
    if tipe == 'object': 
        #schema_field['title'] = field_name
        model_type = from_jsonschema(base_class, schema_field)
        kwargs['model_type'] = model_type
        x = schema_field.pop('properties')

    # Remove, in case it's present
    schema_field.pop('title', None)  

    # Map jsonschema names to schematics names
    for kwarg_name, v in schema_field.items():
        if kwarg_name in schema_kwargs_to_schematics:
            kwarg_name = schema_kwargs_to_schematics[kwarg_name]
        kwargs[kwarg_name] = v

    return schematic_field_type(**kwargs)

