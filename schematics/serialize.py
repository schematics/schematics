# encoding=utf-8

from .types.compound import (
    ModelType, EMPTY_LIST, EMPTY_DICT
)

#
# Field Access Functions
#


class RoleFilter(object):

    def __init__(self, whitelist=None, blacklist=None):
        if whitelist and blacklist:
            raise ValueError("Can't combine whitelists and blacklists for the same role.")

        self.whitelist = whitelist
        self.blacklist = blacklist or {}

    def __eq__(self, other):
        return self.whitelist == other.whitelist and self.blacklist == other.blacklist

    def __neq__(self, other):
        return not self == other

    def __unicode__(self):
        if self.whitelist:
            return "whitelist({})".format(",".join("'{}'".format(k) for k in self.whitelist.keys()))
        else:
            return "blacklist({})".format(",".join("'{}'".format(k) for k in self.blacklist.keys()))

    def __repr__(self):
        return "<RoleFilter {}>".format(unicode(self))

    def __call__(self, k, v):
        if self.whitelist:
            return k not in self.whitelist
        else:
            return k in self.blacklist
        return False

    def __add__(self, other_role_filter):
        if not isinstance(other_role_filter, RoleFilter):
            raise ValueError("Invalid type {} for operator '+'. Must be a subclass of RoleFilter".format(type(other_role_filter)))

        if (self.whitelist and other_role_filter.blacklist) or (self.blacklist and other_role_filter.whitelist):
            raise ValueError("Can't combine whitelists and blacklists for the same role.")

        if self.whitelist:
            return RoleFilter(whitelist=dict(self.whitelist, **other_role_filter.whitelist))
        else:
            return RoleFilter(blacklist=dict(self.blacklist, **other_role_filter.blacklist))


def wholelist(*field_list):
    """Returns a function that evicts nothing. Exists mainly to be an explicit
    allowance of all fields instead of a using an empty blacklist.
    """
    return RoleFilter()


def whitelist(*field_list):
    """Returns a function that operates as a whitelist for the provided list of
    fields.

    A whitelist is a list of fields explicitly named that are allowed.
    """
    return RoleFilter(whitelist=dict((f, True) for f in field_list))


def blacklist(*field_list):
    """Returns a function that operates as a blacklist for the provided list of
    fields.

    A blacklist is a list of fields explicitly named that are not allowed.
    """
    return RoleFilter(blacklist=dict((f, True) for f in field_list))


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
