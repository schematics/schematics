import pickle
from copy import copy, deepcopy
from six import PY3
import pytest

from schematics.datastructures import OrderedDict, DataObject, ConfigObject


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


def test_od_sort():
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


def test_od_repr():
    od = OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])

    assert repr(od) == "OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])"


def test_data_object_basics():

    d = DataObject({'x': 1, 'y': 2})

    assert d == DataObject(x=1, y=2)

    assert hasattr(d, 'x')
    assert 'x' in d
    assert not hasattr(d, 'z')
    assert 'z' not in d

    assert d.x == 1
    with pytest.raises(AttributeError):
        d.z

    assert d['x'] == 1
    with pytest.raises(KeyError):
        d['z']

    assert d._get('z') is None
    assert d._get('z', 0) == 0

    d.z = 3
    assert d.z == 3
    assert d['z'] == 3

    assert len(d) == 3

    assert set(((k, v) for k, v in d)) \
        == set(d._items()) \
        == set((('x', 1), ('y', 2), ('z', 3)))

    x = d._pop('x')
    assert x == 1 and 'x' not in d

    d._clear()
    assert d.__dict__ == {}


def test_data_object_dict_conversions():

    config = {
        'db': {
            'mysql': {
                'host': 'localhost',
                'database': 'test',
            },
            'mongo': {
                'host': 'localhost',
                'database': 'test',
            }
        }
    }

    d = DataObject()
    d.config = config

    assert d.config.db.mysql.host == 'localhost'

    assert d.config == DataObject({'db': DataObject(
        {'mongo': DataObject({'host': 'localhost', 'database': 'test'}),
         'mysql': DataObject({'host': 'localhost', 'database': 'test'})})})

    assert d.config == DataObject({'db':
        {'mongo': {'host': 'localhost', 'database': 'test'},
         'mysql': {'host': 'localhost', 'database': 'test'}}})

    assert config == d.config._to_dict()

    d_copy = copy(d)
    assert d_copy == d
    assert id(d_copy) != id(d)
    assert id(d_copy.config) == id(d.config)

    d_deepcopy = deepcopy(d)
    assert d_deepcopy == d
    assert id(d_deepcopy) != id(d)
    assert id(d_deepcopy.config) != id(d.config)


def test_data_object_methods():

    d = DataObject({'x': 1})
    d._update({'y': 2})
    d._update(DataObject({'z': 3}, q=0))
    assert d == DataObject({'x': 1, 'y': 2, 'z': 3, 'q': 0})

    a = d._setdefault('a')
    assert a is None and d.a is None

    b = d._setdefault('b', 99)
    assert b == 99 and d.b == 99

    d._setdefaults({'i': 12, 'j': 23})
    assert d.i == 12 and d.j == 23


def test_config_object():

    d = ConfigObject(x=1, y=2)
    assert 'x' in d
    assert d.x == 1
    assert d['x'] == 1
    assert 'z' not in d
    assert d.z is None
    assert d['z'] is None

