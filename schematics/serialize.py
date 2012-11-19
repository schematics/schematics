import copy

from schematics.types import schematic_types
from schematics.base import json
from schematics.models import BaseModel, Model


###
### Serialization Shaping Functions
###

def _reduce_loop(cls, model_or_dict, field_converter):
    """Each field's name, the field instance and the field's value are
    collected in a truple and yielded, making this a generator.
    """
    for field_name in model_or_dict:
        field_instance = cls._fields[field_name]
        field_value = model_or_dict[field_name]
        yield (field_name, field_instance, field_value)


def _gen_gottago(field_list, is_white_list, allow_none=False):
    """This function generates a function that handles evicting fields from the
    serialization output based on white list / black list parameters.

    The generated function is referred to as `gottago`.
    """
    ### Setup white or black list behavior as `gottago` function
    gottago = lambda k,v: is_white_list
    
    if field_list is not None:
        def gottago(k, v):
            return k not in field_list or (not allow_none and v is None)
        if not is_white_list:
            def gottago(k, v):
                return k in field_list or (not allow_none and v is None)
            
    return gottago


def apply_shape(cls, model_or_dict, field_converter, model_converter,
                model_encoder, field_list, white_list,
                allow_none=False):
    ### Setup white or black list behavior as `gottago` function
    gottago = _gen_gottago(field_list, white_list, allow_none)

    model_dict = {}

    ### Loop over each field and either evict it or convert it
    for truple in _reduce_loop(cls, model_or_dict, field_converter):
        ### Break 3-tuple out
        (k, field_instance, v) = truple
        
        ### Evict field if it's gotta go
        if gottago(k, v):
            continue
        
        ### Convert field as single model
        elif isinstance(v, Model):
            model_dict[k] = model_converter(v)
            
        ### Convert field as list of models
        elif isinstance(v, list) and len(v) > 0:
            if isinstance(v[0], Model):
                model_dict[k] = [model_converter(vi) for vi in v]
                
        ### Convert field as single field
        else:
            if v is None:
                model_dict[k] = None
            else:
                model_dict[k] = field_converter(field_instance, v)

        ### TODO - embed this cleaner
        if k in model_dict and \
               k in cls._fields and \
               cls._fields[k].minimized_field_name:
            model_dict[cls._fields[k].minimized_field_name] = model_dict[k]
            del model_dict[k]

    return model_dict


###
### Instance Data Serialization
###

def to_python(model, **kw):
    """Returns a Python dictionary representing the Model's
    metaschematic and values.
    """
    field_converter = lambda f, v: f.for_python(v)
    model_encoder = lambda m: to_python(m)
    model_converter = lambda m: to_python(m)
    field_list = []
    white_list = False

    return apply_shape(model.__class__, model, field_converter,
                       model_converter, model_encoder,
                       field_list, white_list, **kw)


def to_json(model, encode=True, sort_keys=False, **kw):
    """Return data prepared for JSON. By default, it returns a JSON encoded
    string, but disabling the encoding to prevent double encoding with
    embedded models.
    """
    field_converter = lambda f, v: f.for_json(v)
    model_encoder = lambda m: to_json(m, encode=False, sort_keys=sort_keys)
    model_converter = lambda m: to_json(m, encode=False, sort_keys=sort_keys)
    field_list = []
    white_list = False

    data = apply_shape(model.__class__, model, field_converter,
                       model_converter, model_encoder,
                       field_list, white_list, **kw)

    if encode:
        return json.dumps(data, sort_keys=sort_keys)
    else:
        return data


def make_ownersafe(cls, model_dict_or_dicts, **kw):
    field_converter = lambda f, v: f.for_python(v)
    model_encoder = lambda m: to_python(m)
    model_converter = lambda m: make_ownersafe(m.__class__, m)
    field_list = cls._options.private_fields
    white_list = False

    return apply_shape(cls, model_dict_or_dicts, field_converter,
                       model_converter, model_encoder,
                       field_list, white_list, **kw)


def make_json_ownersafe(cls, model_dict_or_dicts, encode=True,
                        sort_keys=False, **kw):
    field_converter = lambda f, v: f.for_json(v)
    model_encoder = lambda m: to_json(m, encode=False)
    model_converter = lambda m: make_json_ownersafe(m.__class__, m, encode=False,
                                                    sort_keys=sort_keys)
    field_list = cls._options.private_fields
    white_list = False

    safed = apply_shape(cls, model_dict_or_dicts, field_converter,
                        model_converter, model_encoder,
                        field_list, white_list, **kw)
    
    if encode:
        return json.dumps(safed, sort_keys=sort_keys)
    else:
        return safed


def make_publicsafe(cls, model_dict_or_dicts, **kw):
    field_converter = lambda f, v: f.for_python(v)
    model_encoder = lambda m: to_python(m)
    model_converter = lambda m: make_publicsafe(m.__class__, m)
    field_list = cls._options.public_fields
    white_list = True

    return apply_shape(cls, model_dict_or_dicts, field_converter,
                       model_converter, model_encoder,
                       cls._options.public_fields, white_list, **kw)


def make_json_publicsafe(cls, model_dict_or_dicts, encode=True,
                         sort_keys=False, **kw):
    field_converter = lambda f, v: f.for_json(v)
    model_encoder = lambda m: to_json(m, encode=False)
    model_converter = lambda m: make_json_publicsafe(m.__class__, m, encode=False,
                                                     sort_keys=sort_keys)
    field_list = cls._options.public_fields
    white_list = True

    safed = apply_shape(cls, model_dict_or_dicts, field_converter,
                        model_converter, model_encoder, field_list, white_list,
                        **kw)
    if encode:
        return json.dumps(safed, sort_keys=sort_keys)
    else:
        return safed

###
### Model Definition Serialization
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
    model_encoder = lambda m: for_jsonschema(m)
    model_converter = lambda m: for_jsonschema(m)
    field_list = []
    white_list = False

    properties = apply_shape(model.__class__, model, field_converter,
                             model_converter, model_encoder,
                             field_list=field_list, white_list=white_list,
                             allow_none=True)

    return {
        'type': 'object',
        'title': model.__class__.__name__,
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
        return type(class_name, (model,), model_fields)
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

