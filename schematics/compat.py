# pylint: skip-file

from __future__ import absolute_import

import functools
import operator
import sys


__all__ = ['PY3', 'string_type', 'iteritems', 'metaclass', 'py_native_string', 'reraise', 'str_compat']


PY3 = sys.version_info[0] == 3

string_type = str
iteritems = operator.methodcaller('items')
itervalues = operator.methodcaller('values')

# reraise code taken from werzeug BSD license at https://github.com/pallets/werkzeug/blob/master/LICENSE
def reraise(tp, value, tb=None):
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value


def metaclass(metaclass):
    def make_class(cls):
        attrs = cls.__dict__.copy()
        if attrs.get('__dict__'):
            del attrs['__dict__']
            del attrs['__weakref__']
        return metaclass(cls.__name__, cls.__bases__, attrs)
    return make_class


def py_native_string(source):
    """
    Converts Unicode strings to bytestrings on Python 2. The intended usage is to
    wrap a function or a string in cases where Python 2 expects a native string.
    """
    return source


def str_compat(class_):
    """
    On Python 2, patches the ``__str__`` and ``__repr__`` methods on the given class
    so that the class can be written for Python 3 and Unicode.
    """
    return class_


def repr_compat(class_):
    return class_


def _dict(mapping):
    return dict((key, mapping[key]) for key in mapping)
