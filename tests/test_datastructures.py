import pickle
from copy import deepcopy
from six import PY3
import pytest

from schematics.datastructures import OrderedDict


def test_od_create():
    od = OrderedDict()
    assert od.keys() == []

    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    assert od.keys() == ['a', 'c', 'foo']

    od = OrderedDict(a='b', c='d', foo='bar')
    assert set(od.keys()) == set(['a', 'c', 'foo'])


def test_od_delete_key():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    del od['c']
    assert od.keys() == ['a', 'foo']


def test_od_deepcopy():
    lst = [1, 2, 3]
    od = OrderedDict(a=lst)
    new_od = deepcopy(od)
    new_od['a'].append(4)

    assert od['a'] is lst
    assert lst == [1, 2, 3]
    assert new_od['a'] == [1, 2, 3, 4]
    assert od.keys() == new_od.keys()


def test_od_reduce():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    serialized = pickle.dumps(od)
    new_od = pickle.loads(serialized)

    assert od == new_od
    assert isinstance(new_od, OrderedDict)


def test_od_reversed():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])

    assert list(reversed(od)) == ['foo', 'c', 'a']


def test_od_fromkeys():
    od = OrderedDict.fromkeys(['a', 'b', 'c'], 'foo')

    assert od == {'a': 'foo', 'b': 'foo', 'c': 'foo'}


def test_od_clear():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    od.clear()

    assert od == {}


def test_od_copy():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', object())])
    new_od = od.copy()

    assert od == new_od
    assert od['foo'] is new_od['foo']


def test_od_pop():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])

    assert od.pop('a') == 'b'
    assert 'a' not in od
    assert od.keys() == ['c', 'foo']

    assert od.pop('bar', 1) == 1

    with pytest.raises(KeyError):
        od.pop('bar')


def test_od_popitem():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])

    assert od.popitem() == ('a', 'b')
    assert 'a' not in od
    assert od.keys() == ['c', 'foo']

    assert od.popitem() == ('c', 'd')
    assert 'c' not in od
    assert od.keys() == ['foo']

    assert od.popitem() == ('foo', 'bar')
    assert 'foo' not in od
    assert od.keys() == []

    with pytest.raises(KeyError):
        od.popitem()


def test_od_setdefault():
    od = OrderedDict([('a', 'b')])

    assert od.setdefault('foo') is None
    assert od.keys() == ['a', 'foo']

    assert od.setdefault('bar', 'baz') == 'baz'
    assert od.keys() == ['a', 'foo', 'bar']

    assert od.setdefault('a') == 'b'
    assert od == {'a': 'b', 'foo': None, 'bar': 'baz'}


def test_od_update():
    od = OrderedDict()
    with pytest.raises(TypeError):
        od.update([], [])


def test_sort():
    items = []
    for i in range(10):
        items.append((i, 9 - i))

    od = OrderedDict(items)
    od.sort(key=lambda x: x[1])

    assert od.keys() == list(range(9, -1, -1))

    items = []
    for i in range(10):
        items.append((9 - i, 9 - i))

    od = OrderedDict(items)
    od.sort()

    assert od.keys() == list(range(10))

    od = OrderedDict(items)
    od.sort(reverse=True)

    assert od.keys() == list(range(9, -1, -1))


def test_repr():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])

    assert repr(od) == "OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])"
