# encoding=utf-8

from .types.compound import (
    ModelType, ListType, EMPTY_LIST, DictType, EMPTY_DICT
)

#
# Field Access Functions
#


def wholelist(*field_list):
    """Returns a function that evicts nothing. Exists mainly to be an explicit
    allowance of all fields instead of a using an empty blacklist.
    """
    return lambda k, v: False


def whitelist(*field_list):
    """Returns a function that operates as a whitelist for the provided list of
    fields.

    A whitelist is a list of fields explicitly named that are allowed.
    """
    # Default to rejecting the value
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
    # Default to not rejecting the value
    _blacklist = lambda k, v: False

    if field_list is not None and len(field_list) > 0:
        def _blacklist(k, v):
            return k in field_list

    return _blacklist


def serialize(instance, role, raise_error_on_role=True):
    model_field = ModelType(instance.__class__)

    primitive_data = model_field.to_primitive(instance)

    model_field.filter_by_role(instance, primitive_data, role, raise_error_on_role)

    return primitive_data


def expand(data, context=None):
    expanded_dict = {}

    if context is None:
        context = expanded_dict

    for k, v in data.iteritems():
        try:
            key, remaining = k.split(".", 1)
        except ValueError:
            if not (v in (EMPTY_DICT, EMPTY_LIST) and k in expanded_dict):
                expanded_dict[k] = v
        else:
            current_context = context.setdefault(key, {})
            if current_context in (EMPTY_DICT, EMPTY_LIST):
                current_context = {}
                context[key] = current_context

            current_context.update(expand({remaining: v}, current_context))
    return expanded_dict


def flatten_to_dict(o, prefix=None, ignore_none=True):
    if hasattr(o, "iteritems"):
        iterator = o.iteritems()
    else:
        iterator = enumerate(o)

    flat_dict = {}
    for k, v in iterator:
        if prefix:
            key = ".".join(map(unicode, (prefix, k)))
        else:
            key = k

        if v == []:
            v = EMPTY_LIST
        elif v == {}:
            v = EMPTY_DICT

        if isinstance(v, (dict, list)):
            flat_dict.update(flatten_to_dict(v, prefix=key))
        elif v is not None:
            flat_dict[key] = v
        elif not ignore_none:
            flat_dict[key] = None

    return flat_dict


def flatten(instance, role, raise_error_on_role=True, ignore_none=True, prefix=None, **kwargs):
    model_field = ModelType(instance.__class__)

    primitive_data = model_field.to_primitive(instance, include_serializables=False)

    model_field.filter_by_role(instance, primitive_data, role, raise_error_on_role)

    return flatten_to_dict(primitive_data, prefix=prefix, ignore_none=ignore_none)
