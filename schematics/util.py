from __future__ import absolute_import, division

import collections

try:
    basestring #PY2
    bytes = str
    range = xrange
except NameError:
    basestring = str #PY3
    unicode = str


def setdefault(obj, attr, value, search_mro=False, overwrite_none=False):
    if search_mro:
        exists = hasattr(obj, attr)
    else:
        exists = attr in obj.__dict__
    if exists and overwrite_none:
        if getattr(obj, attr) is None:
            exists = False
    if exists:
        value = getattr(obj, attr)
    else:
        setattr(obj, attr, value)
    return value


class Constant(int):

    def __new__(cls, name, value):
        return int.__new__(cls, value)

    def __init__(self, name, value):
        self.name = name

    def __repr__(self):
        return self.name

    __str__ = __repr__


def listify(value):
    if isinstance(value, list):
        return value
    elif value is None:
        return []
    elif isinstance(value, basestring):
        return [value]
    elif isinstance(value, collections.Sequence):
        return list(value)
    else:
        return [value]

