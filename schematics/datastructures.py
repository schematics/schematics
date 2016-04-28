# -*- coding: utf-8 -*-
# pylint: skip-file

from __future__ import unicode_literals, absolute_import

from collections import MutableMapping, KeysView, ValuesView, ItemsView
from copy import deepcopy
from operator import eq

from .common import *
from .util import get_ident



class OrderedDict(MutableMapping, dict):
    """
    An ordered dictionary.

    The implementation is based on ``collections.OrderedDict`` of the standard library.
    It preserves the original technique of storing the keys as a regular list, whereas
    the reference implementation now uses a linked list. The built-in list gives better
    performance in use cases that are typical with Schematics.
    """

    def __init__(*args, **kwargs):
        if not args:
            raise TypeError("OrderedDict.__init__() needs an instance as the first argument")
        self = args[0]
        args = args[1:]
        if len(args) > 1:
            raise TypeError("OrderedDict() takes at most 1 positional argument, got %d" % len(args))
        dict.__init__(self)
        if not self:
            self._keys = []
        MutableMapping.update(self, *args, **kwargs)

    __contains__ = dict.__contains__
    __getitem__ = dict.__getitem__
    __len__ = dict.__len__

    get = dict.get

    def __setitem__(self, key, item, setitem=dict.__setitem__):
        if key not in self:
            self._keys.append(key)
        setitem(self, key, item)

    def __delitem__(self, key, delitem=dict.__delitem__):
        delitem(self, key)
        self._keys.remove(key)

    def __iter__(self):
        return iter(self._keys)

    def __reversed__(self):
        return reversed(self._keys)

    def clear(self):
        del self._keys[:]
        dict.clear(self)

    def copy(self):
        return self.__class__(self)

    __copy__ = copy

    def move_to_end(self, key, last=True):
        if key not in self:
            raise KeyError(key)
        self._keys.remove(key)
        if last:
            self._keys.append(key)
        else:
            self._keys.insert(0, key)

    __token = object()

    def pop(self, key, default=__token):
        if key in self:
            self._keys.remove(key)
            return dict.pop(self, key)
        elif default is self.__token:
            raise KeyError(key)
        else:
            return default

    def popitem(self, last=True):
        if not self:
            raise KeyError('dictionary is empty')
        key = self._keys.pop(-1 if last else 0)
        value = dict.pop(self, key)
        return key, value

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]
        else:
            self[key] = default
            return default

    def sort(self, key=None, reverse=False):
        if key is not None:
            _key = lambda k: key((k, self[k]))
        else:
            _key = None
        self._keys.sort(key=_key, reverse=reverse)

    def reverse(self):
        self._keys.reverse()

    @classmethod
    def fromkeys(cls, iterable, value=None):
        return cls((key, value) for key in iterable)

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return dict.__eq__(self, other) and all(map(eq, self, other))
        else:
            return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

    def __reduce_ex__(self, protocol=0):
        attrs = vars(self).copy()
        for k in vars(self.__class__()):
            attrs.pop(k, None)
        if protocol <= 2:
            # Express tuples as lists to enable proper PyYAML serialization.
            items = [[k, self[k]] for k in self]
            return (self.__class__, (items,), attrs or None)
        else:
            # Provide items as an iterator. This variant can handle recursive dictionaries.
            return (self.__class__, (), attrs or None, None, iter(self.items()))

    __reduce__ = __reduce_ex__

    def __repr__(self, memo=set()):
        call_key = (id(self), get_ident())
        if call_key in memo:
            return '...'
        else:
            memo.add(call_key)
        try:
            return '%s(%s)' % (self.__class__.__name__, repr(list(self.items())) if self else '')
        finally:
            memo.remove(call_key)

    if PY3:

        def keys(self):
            return _ODKeysView(self)

        def values(self):
            return _ODValuesView(self)

        def items(self):
            return _ODItemsView(self)


class _ODKeysView(KeysView):
    def __reversed__(self):
        for key in reversed(self._mapping):
            yield key


class _ODValuesView(ValuesView):
    def __reversed__(self):
        for key in reversed(self._mapping):
            yield self._mapping[key]


class _ODItemsView(ItemsView):
    def __reversed__(self):
        for key in reversed(self._mapping):
            yield (key, self._mapping[key])



class DataObject(object):
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
        return self.__class__.__name__ + '(%s)' % repr(self.__dict__)

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

    def __setitem__(self, key, value): self.__dict__[key] = value
    def __getitem__(self, key): return self.__dict__[key]
    def __delitem__(self, key): del self.__dict__[key]
    def __len__(self): return len(self.__dict__)
    def __contains__(self, key): return key in self.__dict__

    def _clear(self): return self.__dict__.clear()
    def _get(self, *args): return self.__dict__.get(*args)
    def _items(self): return self.__dict__.items()
    def _keys(self): return self.__dict__.keys()
    def _pop(self, *args): return self.__dict__.pop(*args)
    def _setdefault(self, *args): return self.__dict__.setdefault(*args)



class Context(DataObject):

    _fields = ()

    def __init__(self, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        if self._fields:
            unknowns = [name for name in self._keys() if name not in self._fields]
            if unknowns:
                raise ValueError('Unexpected field names: %r' % unknowns)

    @classmethod
    def _new(cls, *args, **kwargs):
        if len(args) > len(cls._fields):
            raise TypeError('Too many positional arguments')
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
            raise TypeError("Field '{0}' already set".format(name))
        super(Context, self).__setattr__(name, value)

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



__all__ = module_exports(__name__)

