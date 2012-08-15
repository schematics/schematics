"""Here we load the stuff that has no external dependencies.  For now we load
the contents of `base.py` but it's possible the fields will be broken out into
more specific modules as they grow.
"""

structure_types = {}


class DictFieldNotFound(Exception):
    pass


from structures.types.base import *
