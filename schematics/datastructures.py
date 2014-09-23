from copy import deepcopy
from six.moves import zip
from six import iteritems
from six import PY3

_missing = object()


class OrderedDict(dict):

    """Simple ordered dict implementation.

    It's a dict subclass and provides some list functions.  The implementation
    of this class is inspired by the implementation of Babel but incorporates
    some ideas from the `ordereddict`_ and Django's ordered dict.

    The constructor and `update()` both accept iterables of tuples as well as
    mappings:

    >>> d = OrderedDict([('a', 'b'), ('c', 'd')])
    >>> d.update({'foo': 'bar'})
    >>> d
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])

    Keep in mind that when updating from dict-literals the order is not
    preserved as these dicts are unsorted!

    You can copy an OrderedDict like a dict by using the constructor,
    `copy.copy` or the `copy` method and make deep copies with `copy.deepcopy`:

    >>> from copy import copy, deepcopy
    >>> copy(d)
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    >>> d.copy()
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    >>> OrderedDict(d)
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    >>> d['spam'] = []
    >>> d2 = deepcopy(d)
    >>> d2['spam'].append('eggs')
    >>> d
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])])
    >>> d2
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', ['eggs'])])

    All iteration methods as well as `keys`, `values` and `items` return
    the values ordered by the the time the key-value pair is inserted:

    >>> d.keys()
    ['a', 'c', 'foo', 'spam']
    >>> d.values()
    ['b', 'd', 'bar', []]
    >>> d.items()
    [('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])]
    >>> list(d.iterkeys())
    ['a', 'c', 'foo', 'spam']
    >>> list(d.itervalues())
    ['b', 'd', 'bar', []]
    >>> list(d.iteritems())
    [('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])]

    You can sort the OrderedDict like a list:

    >>> d.sort(key=lambda x: x[0].lower())
    >>> d
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])])

    For performance reasons the ordering is not taken into account when
    comparing two ordered dicts.

    .. _ordereddict: http://www.xs4all.nl/~anthon/Python/ordereddict/
    """

    def __init__(self, *args, **kwargs):
        super(OrderedDict, self).__init__()
        self._keys = []
        self.update(*args, **kwargs)

    def __delitem__(self, key):
        super(OrderedDict, self).__delitem__(key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        if key not in self:
            if hasattr(self, '_keys'):
                self._keys.append(key)
            else:
                self._keys = [key]
        super(OrderedDict, self).__setitem__(key, item)

    def __deepcopy__(self, memo):
        memo[id(self)] = new_od = self.__class__()
        new_od.__init__(deepcopy(self.items(), memo))
        return new_od

    def __reversed__(self):
        return reversed(self._keys)

    @classmethod
    def fromkeys(cls, iterable, default=None):
        return cls((key, default) for key in iterable)

    def clear(self):
        del self._keys[:]
        super(OrderedDict, self).clear()

    def copy(self):
        return self.__class__(self)

    def items(self):
        return list(zip(self._keys, self.values()))

    def iteritems(self):
        return list(zip(self._keys, self.itervalues()))

    def keys(self):
        return self._keys[:]

    def iterkeys(self):
        return iter(self._keys)

    def pop(self, key, default=_missing):
        if key not in self:
            if default is _missing:
                raise KeyError(key)
            return default
        self._keys.remove(key)
        return super(OrderedDict, self).pop(key, default)

    def popitem(self):
        if not self._keys:
            raise KeyError('popitem(): dictionary is empty')
        return self._keys[0], self.pop(self._keys[0])

    def setdefault(self, key, default=None):
        if key not in self:
            self._keys.append(key)
        return super(OrderedDict, self).setdefault(key, default)

    def update(self, *args, **kwargs):
        sources = []
        if len(args) == 1:
            if isinstance(args[0], dict):
                sources.append(iteritems(args[0]))
            # if hasattr(args[0], 'iteritems'):
            #     sources.append(args[0].iteritems())
            else:
                sources.append(iter(args[0]))
        elif args:
            raise TypeError('expected at most one positional argument')
        if kwargs:
            sources.append(iteritems(kwargs))
        for iterable in sources:
            for key, val in iterable:
                self[key] = val

    def values(self):
        return [self.get(key) for key in self._keys]

    def itervalues(self):
        return (self.get(key) for key in self._keys)

    def sort(self, cmp=None, key=None, reverse=False):
        if key is not None:
            self._keys.sort(key=lambda k: key((k, self[k])))
        elif cmp is not None:
            self._keys.sort(lambda a, b: cmp((a, self[a]), (b, self[b])))
        else:
            self._keys.sort()
        if reverse:
            self._keys.reverse()

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.items())

    __copy__ = copy
    __iter__ = iterkeys
