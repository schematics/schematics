import operator
import sys


__all__ = ['PY2', 'PY3', 'string_type', 'iteritems', 'metaclass']

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if PY2:
    # pylint: disable=redefined-builtin,invalid-name,unused-import,wrong-import-position
    __all__ += ['bytes', 'str', 'map', 'zip', 'range']
    bytes = str
    str = unicode
    string_type = basestring
    range = xrange
    from itertools import imap as map
    from itertools import izip as zip
    iteritems = operator.methodcaller('iteritems')
else:
    string_type = str
    iteritems = operator.methodcaller('items')


def metaclass(metaclass):
    def make_class(cls):
        attrs = cls.__dict__.copy()
        del attrs['__dict__']
        del attrs['__weakref__']
        return metaclass(cls.__name__, cls.__bases__, attrs)
    return make_class

