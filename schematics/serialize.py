# encoding=utf-8

from .types.compound import (
    ModelType, ListType, EMPTY_LIST, DictType, EMPTY_DICT
)


def _reduce_loop(model):
    """Each field's name, the field MODEL and the field's value are
    collected in a truple and yielded, making this a generator.
    """
    for field_name, field_instance in model:
        field_value = model.get(field_name)
        yield (field_name, field_instance, field_value)


def apply_shape(model, model_converter, role, gottago):
    model_dict = {}

    Model = model.__class__

    # Loop over each field and either evict it or convert it
    for (field_name, field_instance, field_value) in _reduce_loop(model):
        # Evict field if it's gotta go
        if gottago(field_name, field_value):
            continue

        # Check for alternate field name
        serialized_name = field_name
        if field_instance.serialized_name:
            serialized_name = field_instance.serialized_name

        if field_value is None:
            model_dict[serialized_name] = None
        elif isinstance(field_instance, ModelType):
            model_dict[serialized_name] = model_converter(field_value)
        elif isinstance(field_instance, ListType):
            if field_value and isinstance(field_value[0], Model):
                model_dict[serialized_name] = [model_converter(vi)
                                               for vi in field_value]
            else:
                model_dict[serialized_name] = field_instance.to_primitive(field_value)
        elif hasattr(field_value, "serialize"):
            model_dict[serialized_name] = model_converter(field_value)
        else:
            model_dict[serialized_name] = field_instance.to_primitive(field_value)

    return model_dict


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


def serialize(instance, role, **kw):
    model = instance.__class__
    model_converter = lambda m: serialize(m, role)

    gottago = lambda k, v: False
    if role in model._options.roles:
        gottago = model._options.roles[role]
    elif role:
        raise ValueError(u'%s Model has no role "%s"' % (
            instance.__class__.__name__, role))

    return apply_shape(instance, model_converter, role, gottago, **kw)


def expand(data, context=None):
    expanded_dict = {}

    if context is None:
        context = expanded_dict

    for k, v in data.iteritems():
        try:
            key, remaining = k.split(".", 1)
        except ValueError:
            expanded_dict[k] = v
        else:
            current_context = context.setdefault(key, {})
            current_context.update(expand({remaining: v}, current_context))
    return expanded_dict


# TODO: Support lists within dicts and vice versa

def flatten_list_to_dict(l, role, prefix=None):
    flat_dict = {}
    for i, v in enumerate(l):
        key = ".".join((prefix, str(i)))

        if hasattr(v.__class__, "_options"):
            flat_dict.update(flatten(v, role, prefix=key))
        else:
            flat_dict[key] = v

    return flat_dict


def flatten_dict_to_dict(d, role, prefix=None):
    flat_dict = {}
    for k, v in d.iteritems():
        key = ".".join(map(unicode, (prefix, k)))

        if hasattr(v.__class__, "_options"):
            flat_dict.update(flatten(v, role, prefix=key))
        elif isinstance(v, dict):
            flat_dict.update(flatten_dict_to_dict(v, role, prefix=key))
        else:
            flat_dict[key] = v

    return flat_dict


def flatten(instance, role, ignore_none=True, prefix="", **kwargs):
    model = instance.__class__

    gottago = lambda k, v: False
    if role in model._options.roles:
        gottago = model._options.roles[role]
    elif role:
        raise ValueError(u'%s Model has no role "%s"' % (
            instance.__class__.__name__, role))

    flat_dict = {}

    # Loop over each field and either evict it or convert it
    for (field_name, field_instance, field_value) in _reduce_loop(instance):
        if gottago(field_name, field_value):
            continue

        # Check for alternate field name
        serialized_name = field_name
        if field_instance.serialized_name:
            serialized_name = field_instance.serialized_name

        if prefix:
            serialized_name = ".".join((prefix, serialized_name))

        if field_value is None:
            if not ignore_none:
                flat_dict[serialized_name] = None
        elif isinstance(field_instance, ModelType):
            flat_dict.update(flatten(field_value, role, prefix=serialized_name))
        elif isinstance(field_instance, ListType):
            if field_value:
                flat_dict.update(flatten_list_to_dict(field_value, role, prefix=serialized_name))
            else:
                flat_dict[serialized_name] = EMPTY_LIST
        elif isinstance(field_instance, DictType):
            if field_value:
                flat_dict.update(flatten_dict_to_dict(field_value, role, prefix=serialized_name))
            else:
                flat_dict[serialized_name] = EMPTY_DICT
        elif hasattr(field_value, "serialize"):
            continue
        else:
            flat_dict[serialized_name] = field_instance.to_primitive(field_value)

    return flat_dict
