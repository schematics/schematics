# pylint: skip-file

from collections.abc import Mapping, Sequence
from typing import List

__all__: List[str] = []


class DataObject:
    """
    An object for holding data as attributes.

    ``DataObject`` can be instantiated like ``dict``::

        >>> d = DataObject({'one': 1, 'two': 2}, three=3)
        >>> d.__dict__
        {'one': 1, 'two': 2, 'three': 3}

    Attributes are accessible via the regular dot notation (``d.x``) as well as
    the subscription syntax (``d['x']``)::

        >>> d.one == d['one'] == 1
        True

    To convert a ``DataObject`` into a dictionary, use ``d._to_dict()``.

    ``DataObject`` implements the following collection-like operations:

        * iteration through attributes as name-value pairs
        * ``'x' in d`` for membership tests
        * ``len(d)`` to get the number of attributes

    Additionally, the following methods are equivalent to their ``dict` counterparts:
    ``_clear``, ``_get``, ``_keys``, ``_items``, ``_pop``, ``_setdefault``, ``_update``.

    An advantage of ``DataObject`` over ``dict` subclasses is that every method name
    in ``DataObject`` begins with an underscore, so attributes like ``"update"`` or
    ``"values"`` are valid.
    """

    def __init__(self, *args, **kwargs):
        source = args[0] if args else {}
        self._update(source, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__!r})"

    def _copy(self):
        return self.__class__(self)

    __copy__ = _copy

    def __eq__(self, other):
        return isinstance(other, DataObject) and self.__dict__ == other.__dict__

    def __iter__(self):
        return iter(self.__dict__.items())

    def _update(self, source=None, **kwargs):
        if isinstance(source, DataObject):
            source = source.__dict__
        self.__dict__.update(source, **kwargs)

    def _setdefaults(self, source):
        if isinstance(source, dict):
            source = source.items()
        for name, value in source:
            self._setdefault(name, value)
        return self

    def _to_dict(self):
        d = dict(self.__dict__)
        for k, v in d.items():
            if isinstance(v, DataObject):
                d[k] = v._to_dict()
        return d

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __len__(self):
        return len(self.__dict__)

    def __contains__(self, key):
        return key in self.__dict__

    def _clear(self):
        return self.__dict__.clear()

    def _get(self, *args):
        return self.__dict__.get(*args)

    def _items(self):
        return self.__dict__.items()

    def _keys(self):
        return self.__dict__.keys()

    def _pop(self, *args):
        return self.__dict__.pop(*args)

    def _setdefault(self, *args):
        return self.__dict__.setdefault(*args)


class Context(DataObject):

    _fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._fields:
            unknowns = [name for name in self._keys() if name not in self._fields]
            if unknowns:
                raise ValueError(f"Unexpected field names: {unknowns!r}")

    @classmethod
    def _new(cls, *args, **kwargs):
        if len(args) > len(cls._fields):
            raise TypeError("Too many positional arguments")
        return cls(zip(cls._fields, args), **kwargs)

    @classmethod
    def _make(cls, obj):
        if obj is None:
            return cls()
        elif isinstance(obj, cls):
            return obj
        else:
            return cls(obj)

    def __setattr__(self, name, value):
        if name in self:
            raise TypeError(f"Field '{name}' already set")
        super().__setattr__(name, value)

    def _branch(self, **kwargs):
        if not kwargs:
            return self
        items = dict(((k, v) for k, v in kwargs.items() if v is not None and v != self[k]))
        if items:
            return self.__class__(self, **items)
        else:
            return self

    def _setdefaults(self, source):
        if not isinstance(source, dict):
            source = source.__dict__
        new_values = source.copy()
        new_values.update(self.__dict__)
        self.__dict__.update(new_values)
        return self

    def __bool__(self):
        return True

    __nonzero__ = __bool__


class FrozenDict(Mapping):
    def __init__(self, value):
        self._value = dict(value)

    def __getitem__(self, key):
        return self._value[key]

    def __iter__(self):
        return iter(self._value)

    def __len__(self):
        return len(self._value)

    def __hash__(self):
        try:
            return self._hash
        except AttributeError:
            self._hash = 0
            for k, v in self._value.items():
                self._hash ^= hash(k)
                self._hash ^= hash(v)

            return self._hash

    def __repr__(self):
        return repr(self._value)

    def __str__(self):
        return str(self._value)


class FrozenList(Sequence):
    def __init__(self, value):
        self._list = list(value)

    def __getitem__(self, index):
        return self._list[index]

    def __len__(self):
        return len(self._list)

    def __hash__(self):
        try:
            return self._hash
        except AttributeError:
            self._hash = 0
            for e in self._list:
                self._hash ^= hash(e)
            return self._hash

    def __repr__(self):
        return repr(self._list)

    def __str__(self):
        return str(self._list)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for i in range(len(self)):
            if self[i] != other[i]:
                return False
        return True
