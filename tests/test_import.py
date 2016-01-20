# -*- coding: utf-8 -*-

import pytest

from schematics.models import Model
from schematics.types import BaseType, IntType, StringType
from schematics.types.compound import ListType, DictType, ModelType
from schematics.exceptions import ModelConversionError, ModelValidationError
from schematics.undefined import Undefined


class M(Model):
    a, b, c, d = IntType(), IntType(), IntType(), IntType()


def test_import_data():

    m = M({
        'a': 1,
        'b': None,
        'c': 3
    })

    m.import_data({
        'a': None,
        'b': 2
    })
    assert m._data == {'a': None, 'b': 2, 'c': 3, 'd': None}

    m = M({
        'a': 1,
        'b': None,
        'c': 3
    }, init=False)

    m.import_data({
        'a': None,
        'b': 2
    })
    assert m._data == {'a': None, 'b': 2, 'c': 3, 'd': Undefined}

