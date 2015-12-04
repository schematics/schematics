from __future__ import absolute_import, division

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

