# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import collections
import sys

from .compat import *

if PY2:
    try:
        from thread import get_ident
    except ImportError:
        from dummy_thread import get_ident
else:
    try:
        from _thread import get_ident
    except ImportError:
        from _dummy_thread import get_ident


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
        int.__init__(self)

    def __repr__(self):
        return self.name

    __str__ = __repr__


def listify(value):
    if isinstance(value, list):
        return value
    elif value is None:
        return []
    elif isinstance(value, string_type):
        return [value]
    elif isinstance(value, collections.Sequence):
        return list(value)
    else:
        return [value]


def module_exports(module_name):
    module_globals = sys.modules[module_name].__dict__
    return [
        name for name, obj in module_globals.items()
        if name[0] != '_'
          and (getattr(obj, '__module__', None) == module_name
                or isinstance(obj, Constant))
    ]


def package_exports(package_name):
    package_globals = sys.modules[package_name].__dict__
    return [
        name for name, obj in package_globals.items()
        if name[0] != '_'
          and (getattr(obj, '__module__', '').startswith(package_name + '.')
                or isinstance(obj, Constant))
    ]


__all__ = module_exports(__name__)

