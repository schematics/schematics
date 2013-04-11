# encoding=utf-8

from .types.compound import (
    ModelType, EMPTY_LIST, EMPTY_DICT
)
import collections

#
# Field Access Functions
#


class Role(collections.Set):
    """A Role object can be used to filter specific fields against a sequence.

    The Role has a set of names and one function that the specific field is
    filtered with.

    A Role can be operated on as a Set object representing its fields. It's
    important to note that when combining multiple roles using these operations
    only the function of the first role is kept on the resulting role.

    """
    def __init__(self, function, fields):
        self.function = function
        self.fields = set(fields)

    def _from_iterable(self, iterable):
        return Role(self.function, iterable)

    def __contains__(self, value):
        return value in self.fields

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def __eq__(self, other):
        return (self.function.func_name == other.function.func_name and
            self.fields == other.fields)

    def __str__(self):
        return '%s(%s)' % (self.function.func_name,
            ', '.join("'%s'" % f for f in self.fields))

    def __repr__(self):
        return '<Role %s>' % str(self)

    # edit role fields
    def __add__(self, other):
        fields = self.fields.union(other)
        return self._from_iterable(fields)

    def __sub__(self, other):
        fields = self.fields.difference(other)
        return self._from_iterable(fields)

    # apply role to field
    def __call__(self, k, v):
        return self.function(k, v, self.fields)

    # static filter functions
    @staticmethod
    def wholelist(k, v, seq):
        return False

    @staticmethod
    def whitelist(k, v, seq):
        if seq is not None and len(seq) > 0:
            return k not in seq
        # Default to rejecting the value
        return True

    @staticmethod
    def blacklist(k, v, seq):
        if seq is not None and len(seq) > 0:
            return k in seq
        # Default to not rejecting the value
        return False


def wholelist(*field_list):
    """Returns a function that evicts nothing. Exists mainly to be an explicit
    allowance of all fields instead of a using an empty blacklist.
    """
    return Role(Role.wholelist, field_list)


def whitelist(*field_list):
    """Returns a function that operates as a whitelist for the provided list of
    fields.

    A whitelist is a list of fields explicitly named that are allowed.
    """
    return Role(Role.whitelist, field_list)


def blacklist(*field_list):
    """Returns a function that operates as a blacklist for the provided list of
    fields.

    A blacklist is a list of fields explicitly named that are not allowed.
    """
    return Role(Role.blacklist, field_list)


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


def flatten(instance, role, raise_error_on_role=True, ignore_none=True, prefix=None, include_serializables=False, **kwargs):
    model_field = ModelType(instance.__class__)

    primitive_data = model_field.to_primitive(instance, include_serializables=include_serializables)

    model_field.filter_by_role(instance, primitive_data, role, raise_error_on_role, include_serializables=include_serializables)

    return flatten_to_dict(primitive_data, prefix=prefix, ignore_none=ignore_none)
