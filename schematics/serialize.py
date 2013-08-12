# encoding=utf-8

import collections
import itertools

from .types.serializable import Serializable
from .exceptions import ConversionError, ModelConversionError



###
### Field ACL's
###

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


###
### Serialization
###

def atoms(cls, instance_or_dict):
    """
    Iterator for the atomic components of a model definition and relevant data
    that creates a threeple of the field's name, the instance of it's type, and
    it's value.
    """

    all_fields = itertools.chain(cls._fields.iteritems(),
                                 cls._serializables.iteritems())

    return ((field_name, field, instance_or_dict[field_name])
            for field_name, field in all_fields)


def allow_none(cls, field):
    """
    Inspects a field and class for ``serialize_when_none`` setting.

    The setting defaults to the value of the class.  A field can override the
    class setting with it's own ``serialize_when_none`` setting.
    """
    allowed = cls._options.serialize_when_none
    if field.serialize_when_none != None:
        allowed = field.serialize_when_none
    return allowed


###
### Transform Loop
###

def apply_shape(cls, instance_or_dict, role, field_converter, shape_converter,
                raise_error_on_role=False, print_none=False):
    """
    The apply shape function is intended to be a general loop definition that
    can be used for any form of data shaping, such as application of roles or
    how a field is transformed.
    """

    data = {}

    ### Translate `role` into `gottago` function
    gottago = wholelist()
    if hasattr(cls, '_options') and role in cls._options.roles:
        gottago = cls._options.roles[role]
    elif role and raise_error_on_role:
        error_msg = u'%s Model has no role "%s"'
        raise ValueError(error_msg % (cls.__name__, role))

    ### Transformation loop
    for field_name, field, value in atoms(cls, instance_or_dict):
        serialized_name = field.serialized_name or field_name

        ### Skipping this field was requested
        if gottago(field_name, value):
            continue

        ### Value found, apply transformation and store it
        elif value is not None:
            if hasattr(field, 'apply_shape'):
                shaped = field.apply_shape(value, role,
                                           field_converter, shape_converter,
                                           print_none=print_none)
            else:
                shaped = field_converter(field, value)

            if (shaped is None and allow_none(cls, field)):
                data[serialized_name] = shaped
            elif shaped is not None:
                data[serialized_name] = shaped
            elif print_none:
                data[serialized_name] = shaped

        ### Store None if reqeusted
        elif value is None and allow_none(cls, field):
            data[serialized_name] = value
        elif print_none:
            data[serialized_name] = value

    if len(data) > 0:
        return data
    elif print_none:
        return data


def convert(cls, raw_data):
    """
    Converts the raw data into richer Python constructs according to the
    fields on the model
    """
    data = {}
    errors = {}

    is_class = isinstance(raw_data, cls)
    is_dict = isinstance(raw_data, dict)

    if not is_class and not is_dict:
        error_msg = 'Model conversion requires a model or dict'
        raise ModelConversionError(error_msg)

    for field_name, field in cls._fields.iteritems():
        serialized_field_name = field.serialized_name or field_name

        try:
            if serialized_field_name in raw_data:
                raw_value = raw_data[serialized_field_name]
            else:
                raw_value = raw_data[field_name]

            if raw_value is not None:
                raw_value = field.convert(raw_value)
            data[field_name] = raw_value
            
        except KeyError:
            data[field_name] = field.default
        except ConversionError, e:
            errors[serialized_field_name] = e.messages

    if errors:
        raise ModelConversionError(errors)

    return data


###
### Serialization
###

def serialize(instance, role, raise_error_on_role=True):
    """
    Implements serialization as a mechanism to convert ``Model`` instances into
    dictionaries that represent the field_names => converted data.

    The conversion is done by calling ``to_primitive`` on both model and field
    instances.
    """
    field_converter = lambda field, value: field.to_primitive(value)
    shape_converter = lambda field, value: True
    
    data = apply_shape(instance.__class__, instance, role, field_converter,
                       shape_converter, raise_error_on_role)
    return data


###
### Flattening
###

EMPTY_LIST = "[]"
EMPTY_DICT = "{}"

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


def flatten(instance, role, raise_error_on_role=True, ignore_none=True,
            prefix=None, **kwargs):

    field_converter = lambda field, value: field.to_primitive(value)
    shape_converter = lambda field, value: value.flatten()
    
    data = apply_shape(instance.__class__, instance, role, field_converter,
                       shape_converter, print_none=True)

    return flatten_to_dict(data, prefix=prefix, ignore_none=ignore_none)
