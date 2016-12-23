
from .compat import iteritems
from .undefined import Undefined
from collections import namedtuple

Atom = namedtuple('Atom', ('name', 'field', 'value'))
Atom.__new__.__defaults__ = (None,) * len(Atom._fields)


def atoms(schema, mapping, keys=Atom._fields, filter=None):
    """
    Iterator for the atomic components of a model definition and relevant
    data that creates a 3-tuple of the field's name, its type instance and
    its value.

    :type schema: schematics.schema.Schema
    :param schema:
        The Schema definition.
    :param mapping:
        The structure where fields from schema are mapped to values. The only
        expectation for this structure is that it implements a ``Mapping``
        interface.
    :type keys: Tuple[str, str, str]
    :param keys:
        Tuple specifying the output of the iterator. Valid keys are:
            `name`: the field name
            `field`: the field descriptor object
            `value`: the current value set on the field
        Specifying invalid keys will raise an exception.
    :type filter: Callable[[Atom], bool]
    :param filter:
        Function to filter out atoms from the iteration.
    """
    atom_dict = dict.fromkeys(Atom._fields)
    keys_set = set(keys)
    if not keys_set.issubset(atom_dict):
        raise TypeError('invalid key specified')

    has_value = (mapping is not None) and ('value' in keys_set)

    for field_name, field in iteritems(schema.fields):
        atom_dict['name'] = field_name
        atom_dict['field'] = field
        atom_dict['value'] = Undefined

        if has_value:
            try:
                value = getattr(mapping, field_name)
            except AttributeError:
                value = mapping.get(field_name, Undefined)
            except Exception:
                value = Undefined
            atom_dict['value'] = value

        atom_tuple = Atom(**dict((k, atom_dict.get(k)) for k in keys))
        if filter is None:
            yield atom_tuple
        elif filter(atom_tuple):
            yield atom_tuple


class atom_filter:

    @staticmethod
    def has_setter(atom):
        return getattr(atom.field, 'fset', None) is not None

    @staticmethod
    def not_setter(atom):
        return not atom_filter.has_setter(atom)
