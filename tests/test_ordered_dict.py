# Most of these tests have been adapted from the stdlib OrderedDict tests.

from collections import MutableMapping
import copy
from operator import itemgetter
import pickle
from random import shuffle
import sys
from test import mapping_tests

import pytest

from schematics.common import PY2, PY3
from schematics.datastructures import OrderedDict


class GeneralMappingTests(mapping_tests.BasicTestMappingProtocol):

    type2test = OrderedDict

    def test_popitem(self):
        d = self._empty_mapping()
        with pytest.raises(KeyError):
            d.popitem()


class MyOrderedDict(OrderedDict):
    pass


class SubclassMappingTests(mapping_tests.BasicTestMappingProtocol):

    type2test = MyOrderedDict

    def test_popitem(self):
        d = self._empty_mapping()
        with pytest.raises(KeyError):
            d.popitem()


def test_init():

    with pytest.raises(TypeError):
        OrderedDict([('a', 1), ('b', 2)], None)                                # too many args
    pairs = [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5)]
    assert sorted(OrderedDict(dict(pairs)).items()) == pairs                   # dict input
    assert sorted(OrderedDict(**dict(pairs)).items()) == pairs                 # kwds input
    assert list(OrderedDict(pairs).items()) == pairs                           # pairs input
    assert list(OrderedDict(
        [('a', 1), ('b', 2), ('c', 9), ('d', 4)], c=3, e=5).items()) == pairs  # mixed input

    # make sure no positional args conflict with possible kwdargs
    if PY2 and sys.version_info >= (2, 7, 1) or PY3 and sys.version_info >= (3, 2):
        assert list(OrderedDict(self=42).items()) == [('self', 42)]
        assert list(OrderedDict(other=42).items()) == [('other', 42)]

    with pytest.raises(TypeError):
        OrderedDict(42)
    with pytest.raises(TypeError):
        OrderedDict((), ())
    with pytest.raises(TypeError):
        OrderedDict.__init__()

    # Make sure that direct calls to __init__ do not clear previous contents
    d = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('d', 44), ('e', 55)])
    d.__init__([('e', 5), ('f', 6)], g=7, d=4)
    assert (list(d.items()) ==
                    [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5), ('f', 6), ('g', 7)])


def test_update():

    with pytest.raises(TypeError):
        OrderedDict().update([('a', 1), ('b', 2)], None)               # too many args
    pairs = [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5)]
    od = OrderedDict()
    od.update(dict(pairs))
    assert sorted(od.items()) == pairs                                 # dict input
    od = OrderedDict()
    od.update(**dict(pairs))
    assert sorted(od.items()) == pairs                                 # kwds input
    od = OrderedDict()
    od.update(pairs)
    assert list(od.items()) == pairs                                   # pairs input
    od = OrderedDict()
    od.update([('a', 1), ('b', 2), ('c', 9), ('d', 4)], c=3, e=5)
    assert list(od.items()) == pairs                                   # mixed input

    # Issue 9137: Named argument called 'other' or 'self'
    # shouldn't be treated specially.
    if PY2 and sys.version_info >= (2, 7, 1) or PY3 and sys.version_info >= (3, 2):
        od = OrderedDict()
        od.update(self=23)
        assert list(od.items()) == [('self', 23)]
        od = OrderedDict()
        od.update(other={})
        assert list(od.items()) == [('other', {})]
        od = OrderedDict()
        od.update(red=5, blue=6, other=7, self=8)
        assert sorted(list(od.items())) == [('blue', 6), ('other', 7), ('red', 5), ('self', 8)]

    # Make sure that direct calls to update do not clear previous contents
    # add that updates items are not moved to the end
    d = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('d', 44), ('e', 55)])
    d.update([('e', 5), ('f', 6)], g=7, d=4)
    assert (list(d.items()) ==
                    [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5), ('f', 6), ('g', 7)])

    with pytest.raises(TypeError):
        OrderedDict().update(42)
    with pytest.raises(TypeError):
        OrderedDict().update((), ())
    with pytest.raises(TypeError):
        OrderedDict.update()


def test_abc():
    assert isinstance(OrderedDict(), MutableMapping)
    assert issubclass(OrderedDict, MutableMapping)


def test_clear():
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    shuffle(pairs)
    od = OrderedDict(pairs)
    assert len(od) == len(pairs)
    od.clear()
    assert len(od) == 0


def test_delitem():
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    od = OrderedDict(pairs)
    del od['a']
    assert 'a' not in od
    with pytest.raises(KeyError):
        del od['a']
    assert list(od.items()) == pairs[:2] + pairs[3:]


def test_setitem():
    od = OrderedDict([('d', 1), ('b', 2), ('c', 3), ('a', 4), ('e', 5)])
    od['c'] = 10           # existing element
    od['f'] = 20           # new element
    assert (list(od.items()) ==
                     [('d', 1), ('b', 2), ('c', 10), ('a', 4), ('e', 5), ('f', 20)])


@pytest.mark.parametrize('f', [lambda x: x, reversed])
def test_iterators(f):
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    shuffle(pairs)
    od = OrderedDict(pairs)
    assert list(f(od)) == [t[0] for t in f(pairs)]
    assert list(f(od.keys())) == [t[0] for t in f(pairs)]
    assert list(f(od.values())) == [t[1] for t in f(pairs)]
    assert list(f(od.items())) == list(f(pairs))


def test_popitem():
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    shuffle(pairs)
    od = OrderedDict(pairs)
    while pairs:
        assert od.popitem() == pairs.pop()
    with pytest.raises(KeyError):
        od.popitem()
    assert len(od) == 0


def test_pop():

    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    shuffle(pairs)
    od = OrderedDict(pairs)
    shuffle(pairs)
    while pairs:
        k, v = pairs.pop()
        assert od.pop(k) == v
    with pytest.raises(KeyError):
        od.pop('xyz')
    assert len(od) == 0
    assert od.pop(k, 12345) == 12345

    # make sure pop still works when __missing__ is defined
    class Missing(OrderedDict):
        def __missing__(self, key):
            return 0
    m = Missing(a=1)
    assert m.pop('b', 5) == 5
    assert m.pop('a', 6) == 1
    assert m.pop('a', 6) == 6
    with pytest.raises(KeyError):
        m.pop('a')


def test_equality():
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    shuffle(pairs)
    od1 = OrderedDict(pairs)
    od2 = OrderedDict(pairs)
    assert od1 == od2          # same order implies equality
    pairs = pairs[2:] + pairs[:2]
    od2 = OrderedDict(pairs)
    assert od1 != od2          # different order implies inequality
    # comparison to regular dict is not order sensitive
    assert od1 == dict(od2)
    assert dict(od2) == od1
    # different length implied inequality
    assert od1 != OrderedDict(pairs[:-1])


def test_copying():
    # Check that ordered dicts are copyable, deepcopyable, picklable,
    # and have a repr/eval round-trip
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    od = OrderedDict(pairs)
    def check(dup):
        assert dup is not od
        assert dup == od
    check(od.copy())
    check(copy.copy(od))
    check(copy.deepcopy(od))
    for proto in range(pickle.HIGHEST_PROTOCOL + 1):
        check(pickle.loads(pickle.dumps(od, proto)))
    check(eval(repr(od)))
    update_test = OrderedDict()
    update_test.update(od)
    check(update_test)
    check(OrderedDict(od))


def test_yaml_linkage():
    # Verify that __reduce__ is setup in a way that supports PyYAML's dump() feature.
    # In yaml, lists are native but tuples are not.
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    od = OrderedDict(pairs)
    # yaml.dump(od) -->
    # '!!python/object/apply:__main__.OrderedDict\n- - [a, 1]\n  - [b, 2]\n'
    assert all(type(pair)==list for pair in od.__reduce__()[1][0])


def test_reduce_not_too_fat():
    # do not save instance dictionary if not needed
    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    od = OrderedDict(pairs)
    assert od.__reduce__()[2] is None
    od.x = 10
    assert od.__reduce__()[2] is not None


@pytest.mark.skipif(PY2, reason='CPython issue #17900')
def test_pickle_recursive():
    od = OrderedDict()
    od['x'] = od
    rec = pickle.loads(pickle.dumps(od))
    assert list(od.keys()) == list(rec.keys())
    assert od is not rec
    assert rec['x'] is rec


def test_repr():
    od = OrderedDict([('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)])
    assert (repr(od) ==
        "OrderedDict([('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)])")
    assert eval(repr(od)) == od
    assert repr(OrderedDict()) == "OrderedDict()"


def test_repr_recursive():
    # See issue #9826
    od = OrderedDict.fromkeys('abc')
    od['x'] = od
    assert repr(od) == "OrderedDict([('a', None), ('b', None), ('c', None), ('x', ...)])"


def test_setdefault():

    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    shuffle(pairs)
    od = OrderedDict(pairs)
    pair_order = list(od.items())
    assert od.setdefault('a', 10) == 3
    # make sure order didn't change
    assert list(od.items()) == pair_order
    assert od.setdefault('x', 10) == 10
    # make sure 'x' is added to the end
    assert list(od.items())[-1] == ('x', 10)

    # make sure setdefault still works when __missing__ is defined
    class Missing(OrderedDict):
        def __missing__(self, key):
            return 0
    assert Missing().setdefault(5, 9) == 9


def test_reinsert():
    # Given insert a, insert b, delete a, re-insert a,
    # verify that a is now later than b.
    od = OrderedDict()
    od['a'] = 1
    od['b'] = 2
    del od['a']
    od['a'] = 1
    assert list(od.items()) == [('b', 2), ('a', 1)]


def test_move_to_end():
    od = OrderedDict.fromkeys('abcde')
    assert list(od) == list('abcde')
    od.move_to_end('c')
    assert list(od) == list('abdec')
    od.move_to_end('c', 0)
    assert list(od) == list('cabde')
    od.move_to_end('c', 0)
    assert list(od) == list('cabde')
    od.move_to_end('e')
    assert list(od) == list('cabde')
    with pytest.raises(KeyError):
        od.move_to_end('x')


def test_override_update():
    # Verify that subclasses can override update() without breaking __init__()
    class MyOD(OrderedDict):
        def update(self, *args, **kwds):
            raise Exception()
    items = [('a', 1), ('c', 3), ('b', 2)]
    assert list(MyOD(items).items()) == items


def test_sort():

    pairs = [('c', 1), ('b', 2), ('a', 3), ('d', 4), ('e', 5), ('f', 6)]
    shuffled = pairs[:]

    shuffle(shuffled)
    od = OrderedDict(shuffled)
    od.sort(key=itemgetter(1))
    assert list(od.items()) == pairs

    shuffle(shuffled)
    od = OrderedDict(shuffled)
    od.sort()
    assert list(od.items()) == list(sorted(pairs))

    shuffle(shuffled)
    od = OrderedDict(shuffled)
    od.sort(reverse=True)
    assert list(od.items()) == list(reversed(sorted(pairs)))

