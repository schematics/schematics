# encoding=utf-8

import copy
import collections
import json

from .models import BaseModel


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


def apply_shape(model, instance_or_dict, field_converter, model_converter, gottago):

    model_dict = {}

    # Loop over each field and either evict it or convert it
    for truple in _reduce_loop(model, instance_or_dict, field_converter):
        # Break 3-tuple out
        (field_name, field_instance, field_value) = truple

        # Check for alternate field name
        serialized_name = field_name
        if field_instance.minimized_field_name:
            serialized_name = field_instance.minimized_field_name
        elif field_instance.print_name:
            serialized_name = field_instance.print_name

        # Evict field if it's gotta go
        if gottago(field_name, field_value):
            continue

        if field_value is None:
            model_dict[serialized_name] = None
            continue

        # Convert field as single model
        if isinstance(field_value, BaseModel):
            model_dict[serialized_name] = model_converter(field_value)
            continue

        # Convert field as list of models
        if isinstance(field_value, list):
            if field_value and isinstance(field_value[0], BaseModel):
                model_dict[serialized_name] = [model_converter(vi)
                                               for vi in field_value]
                continue

        # Convert field as single field
        model_dict[serialized_name] = field_converter(field_instance, field_value)

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


def to_json(model, gottago=wholelist(), encode=True, sort_keys=False, **kw):
    field_converter = lambda f, v: f.to_json(v)
    model_converter = lambda m: to_json(m)

    data = apply_shape(model.__class__, model, field_converter,
                       model_converter, gottago, **kw)

    return data


def make_safe_json(model, instance_or_dict, role, **kw):
    field_converter = lambda f, v: f.to_json(v)
    model_converter = lambda m: make_safe_json(m.__class__, m, role)

    gottago = lambda k, v: True
    if role in model._options.roles:
        gottago = model._options.roles[role]

    return apply_shape(model, instance_or_dict, field_converter, model_converter,
                       gottago, **kw)

