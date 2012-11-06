from schematics.base import json
from schematics.models import BaseModel, Model


###
### Instance Data Serialization
###

def _to_fields(model, field_converter):
    """Returns a Python dictionary with the model's data keyed by field
    name.  The `field_converter` argument is a function that receives the
    field and it's value and returns the field converted to the desired
    formed.

    In the `to_json` function below, the `field_converter` argument is
    function that called `field.for_json` to convert the fields value
    into a form safe passing to `json.dumps`.
    """
    data = {}

    # First map the subclasses of BaseType
    for field_name, field in model._fields.items():
        value = getattr(model, field_name, None)
        if value is not None:
            data[field_name] = field_converter(field, value)

    return data


def to_python(model):
    """Returns a Python dictionary representing the Model's
    metaschematic and values.
    """
    fun = lambda f, v: f.for_python(v)
    data = _to_fields(model, fun)
    return data


def to_json(model, encode=True, sort_keys=False):
    """Return data prepared for JSON. By default, it returns a JSON encoded
    string, but disabling the encoding to prevent double encoding with
    embedded models.
    """
    fun = lambda f, v: f.for_json(v)
    data = _to_fields(model, fun)
    if encode:
        return json.dumps(data, sort_keys=sort_keys)
    else:
        return data


###
### Serialization Shaping Functions
###

def apply_shape(cls, model_dict_or_dicts, field_converter, model_converter,
                model_encoder, field_list=None, white_list=True):
    """This function is the building block of the safe mechanism. This
    class method takes a model, dict or dicts and converts them into the
    equivalent schematic with three basic rules applied.

      1. The fields must be converted from the model into a type. This is
         currently scene as calling `for_python()` or `for_json()` on
         fields.

      2. A function that knows how to handle `Model` instances, using the
         same security parameters as the caller; this function.

      3. The field list that acts as either a white list or a black list. A
         white list preserves only the keys explicitly listed. A black list
         preserves any keys not explicitly listed.
    """
    ### Setup white or black list behavior as `gottago` function
    if field_list is None:
        gottago = lambda k,v: white_list
    else:
        gottago = lambda k, v: k not in field_list or v is None
        if not white_list:
            gottago = lambda k, v: k in field_list or v is None

    ### Reduce `model_dict_or_dicts` argument into a dict or dicts
    if isinstance(model_dict_or_dicts, BaseModel):
        model_dict = dict((f, model_dict_or_dicts[f])
                          for f in model_dict_or_dicts)
    else:
        model_dict = model_dict_or_dicts

    ### Transform each field
    for k, v in model_dict.items():
        if gottago(k, v):
            del model_dict[k]
        elif isinstance(v, Model):
            model_dict[k] = model_converter(v)
        elif isinstance(v, list) and len(v) > 0:
            if isinstance(v[0], Model):
                model_dict[k] = [model_converter(vi) for vi in v]
        else:
            model_dict[k] = field_converter(k, v)

        if k in model_dict and \
               k in cls._fields and \
               cls._fields[k].minimized_field_name:
            model_dict[cls._fields[k].minimized_field_name] = model_dict[k]
            del model_dict[k]

    return model_dict


def make_ownersafe(cls, model_dict_or_dicts):
    field_converter = lambda f, v: v
    model_encoder = lambda m: m.to_python()
    model_converter = lambda m: make_ownersafe(m.__class__, m)
    field_list = cls._options.private_fields
    white_list = False

    return apply_shape(cls, model_dict_or_dicts, field_converter,
                     model_converter, model_encoder,
                     field_list=field_list, white_list=white_list)


def make_json_ownersafe(cls, model_dict_or_dicts, encode=True,
                        sort_keys=False):
    field_converter = lambda f, v: cls._fields[f].for_json(v)
    model_encoder = lambda m: m.to_json(encode=False)
    model_converter = lambda m: make_json_ownersafe(m.__class__, m, encode=False,
                                                    sort_keys=sort_keys)
    field_list = cls._options.private_fields
    white_list = False

    safed = apply_shape(cls, model_dict_or_dicts, field_converter,
                      model_converter, model_encoder,
                      field_list=field_list, white_list=white_list)
    if encode:
        return json.dumps(safed, sort_keys=sort_keys)
    else:
        return safed


def make_publicsafe(cls, model_dict_or_dicts):
    field_converter = lambda f, v: v
    model_encoder = lambda m: m.to_python()
    model_converter = lambda m: make_publicsafe(m.__class__, m)
    field_list = cls._options.public_fields
    white_list = True

    return apply_shape(cls, model_dict_or_dicts, field_converter,
                     model_converter, model_encoder,
                     field_list=cls._options.public_fields,
                         white_list=white_list)


def make_json_publicsafe(cls, model_dict_or_dicts, encode=True,
                         sort_keys=False):
    field_converter = lambda f, v: cls._fields[f].for_json(v)
    model_encoder = lambda m: m.to_json(encode=False)
    model_converter = lambda m: make_json_publicsafe(m.__class__, m, encode=False,
                                                     sort_keys=sort_keys)
    field_list = cls._options.public_fields
    white_list = True

    safed = apply_shape(cls, model_dict_or_dicts, field_converter,
                      model_converter, model_encoder,
                      field_list=field_list, white_list=white_list)
    if encode:
        return json.dumps(safed, sort_keys=sort_keys)
    else:
        return safed
