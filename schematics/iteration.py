
from .common import * # pylint: disable=redefined-builtin
from .undefined import Undefined

from collections import namedtuple

atom = namedtuple('atom', ('name', 'field', 'value'))
atom.__new__.__defaults__ = (None,) * len(atom._fields)


def atoms(schema, instance_or_dict, keys=atom._fields, filter=None):
    """
    Iterator for the atomic components of a model definition and relevant
    data that creates a 3-tuple of the field's name, its type instance and
    its value.

    :param schema:
        The Schema definition.
    :param instance_or_dict:
        The structure where fields from cls are mapped to values. The only
        expectation for this structure is that it implements a ``Mapping``
        interface.
    :param keys:
        Tuple specifying the output of the iterator. Valid keys are:
            `name`: the field name
            `field`: the field descriptor object
            `value`: the current value set on the field
        Specifying invalid keys will raise an exception.
    """
    atom_dict = atom()._asdict()
    keys_set = set(keys)
    if not keys_set.issubset(atom_dict):
        raise TypeError('invalid key specified')

    has_value = (instance_or_dict is not None) and ('value' in keys_set)

    for field_name, field in iteritems(schema.fields):
        atom_dict['name'] = field_name
        atom_dict['field'] = field
        atom_dict['value'] = Undefined

        if has_value:
            try:
                value = getattr(instance_or_dict, field_name)
            except AttributeError:
                value = instance_or_dict.get(field_name, Undefined)
            except:
                value = Undefined
            atom_dict['value'] = value

        atom_tuple = atom(**dict((k, atom_dict.get(k)) for k in keys))
        if filter is None:
            yield atom_tuple
        elif filter(atom_tuple):
            yield atom_tuple
        else:
            continue
