# -*- coding: utf-8 -*-

import pytest

from schematics.models import Model
from schematics.transforms import ExportConverter
from schematics.types import *
from schematics.types.compound import *
from schematics.types.serializable import serializable
from schematics.undefined import Undefined


params = [(None, None), (None, 4), (4, 4), (3, 3), (2, 2), (1, 1)]

@pytest.fixture(params=params)
def models(request):

    m_level, n_level = request.param

    class N(Model):
        subfield1 = StringType()
        subfield2 = StringType()
        subfield3 = StringType()
        subfield4 = StringType()

    class M(Model):
        field0 = StringType(export_level=0)
        field1 = StringType()
        field2 = StringType()
        field3 = StringType()
        field4 = StringType()
        field5 = StringType(export_level=2)
        field6 = StringType(export_level=4)
        listfield = ListType(StringType())
        modelfield1 = ModelType(N)
        modelfield2 = ModelType(N)

    if m_level:
        M._options.export_level = m_level

    if n_level:
        N._options.export_level = n_level

    return M, N


input = {
    'field0': 'foo',
    'field1': 'foo',
    'field2': '',
    'field3': None,
    'field5': None,
    'listfield': [],
    'modelfield1': {
        'subfield1': 'foo',
        'subfield2': '',
        'subfield3': None,
        },
    'modelfield2': {}
    }


def test_export_level(models):

    M, N = models
    m_level = M._options.export_level
    n_level = N._options.export_level

    output = M(input, init=False).to_primitive()

    if m_level == 1 and n_level == 1:
        assert output == {
            'field1': 'foo',
            'field2': '',
            'field6': None,
            'modelfield1': {
                'subfield1': 'foo',
                'subfield2': '',
                },
            }
    elif m_level == 2 and n_level == 2:
        assert output == {
            'field1': 'foo',
            'field2': '',
            'field6': None,
            'listfield': [],
            'modelfield1': {
                'subfield1': 'foo',
                'subfield2': '',
                },
            'modelfield2': {},
            }
    elif m_level == 3 and n_level == 3:
        assert output == {
            'field1': 'foo',
            'field2': '',
            'field3': None,
            'field6': None,
            'listfield': [],
            'modelfield1': {
                'subfield1': 'foo',
                'subfield2': '',
                'subfield3': None,
                },
            'modelfield2': {},
            }
    elif m_level == 4 and n_level == 4:
        assert output == {
            'field1': 'foo',
            'field2': '',
            'field3': None,
            'field4': None,
            'field6': None,
            'listfield': [],
            'modelfield1': {
                'subfield1': 'foo',
                'subfield2': '',
                'subfield3': None,
                'subfield4': None,
                },
            'modelfield2': {
                'subfield1': None,
                'subfield2': None,
                'subfield3': None,
                'subfield4': None,
                },
            }
    elif m_level == 3 and n_level == 4:
        assert output == {
            'field1': 'foo',
            'field2': '',
            'field3': None,
            'field6': None,
            'listfield': [],
            'modelfield1': {
                'subfield1': 'foo',
                'subfield2': '',
                'subfield3': None,
                'subfield4': None,
                },
            'modelfield2': {
                'subfield1': None,
                'subfield2': None,
                'subfield3': None,
                'subfield4': None,
                },
            }
    else:
        raise Exception("Assertions missing for testcase m_level={0}, n_level={1}".format(m_level, n_level))


def test_export_level_override(models):

    M, N = models
    m_level = M._options.export_level
    n_level = N._options.export_level

    m = M(input, init=False)

    assert m.to_primitive(export_level=0) == {}

    assert m.to_primitive(export_level=1) == {
        'field0': 'foo',
        'field1': 'foo',
        'field2': '',
        'modelfield1': {
            'subfield1': 'foo',
            'subfield2': '',
            },
        }

    assert m.to_primitive(export_level=2) == {
        'field0': 'foo',
        'field1': 'foo',
        'field2': '',
        'listfield': [],
        'modelfield1': {
            'subfield1': 'foo',
            'subfield2': '',
            },
        'modelfield2': {},
        }

    assert m.to_primitive(export_level=3) == {
        'field0': 'foo',
        'field1': 'foo',
        'field2': '',
        'field3': None,
        'field5': None,
        'listfield': [],
        'modelfield1': {
            'subfield1': 'foo',
            'subfield2': '',
            'subfield3': None,
            },
        'modelfield2': {},
        }

    assert m.to_primitive(export_level=4) == {
        'field0': 'foo',
        'field1': 'foo',
        'field2': '',
        'field3': None,
        'field4': None,
        'field5': None,
        'field6': None,
        'listfield': [],
        'modelfield1': {
            'subfield1': 'foo',
            'subfield2': '',
            'subfield3': None,
            'subfield4': None,
            },
        'modelfield2': {
            'subfield1': None,
            'subfield2': None,
            'subfield3': None,
            'subfield4': None,
            },
        }


def test_custom_converter():

    class M(Model):
        x = IntType()
        y = IntType()
        z = IntType()

    def converter(field, value, context):
        if field.name == 'z':
            return Undefined
        else:
            return field.export(value, PRIMITIVE, context)

    m = M(dict(x=1, y=None, z=3))

    assert m.export(PRIMITIVE, field_converter=converter, export_level=3) == {'x': 1, 'y': None}

