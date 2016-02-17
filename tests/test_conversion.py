# -*- coding: utf-8 -*-

import pytest

from schematics.models import Model
from schematics.types import *
from schematics.types.compound import *
from schematics.exceptions import *
from schematics.undefined import Undefined


def autofail(value, context):
    raise ValidationError("Fubar!", info=99)

class M(Model):
    intfield = IntType(max_value=2)
    reqfield = StringType(required=True)
    matrixfield = ListType(ListType(IntType(max_value=2)))
    listfield = ListType(IntType(), max_size=3, validators=[autofail])
    modelfield = ModelType('M')


def get_input_dict():

    inputdict = {
        'intfield': '1',
        'reqfield': 'foo',
        'listfield': [],
        'modelfield': {
            'reqfield': 'bar',
            'listfield': [1, 2, 3, 4],
            'modelfield': {
                'intfield': '3',
                'matrixfield': [[0, 1, 0, 1], [1, 2, 3, 4], ['1', '0', '1', '0']],
                'listfield': None,
                'modelfield': {
                    'intfield': '0',
                    'reqfield': 'foo',
                    'listfield': None}}}}

    return inputdict


def get_input_instance(input_init):

    inputinstance = M(init=input_init)
    inputinstance.intfield = '1'
    inputinstance.reqfield = 'foo'
    inputinstance.listfield = []
    inputinstance.modelfield = M(init=input_init)
    inputinstance.modelfield.reqfield = 'bar'
    inputinstance.modelfield.listfield = [1, 2, 3, 4]
    inputinstance.modelfield.modelfield = M(init=input_init)
    inputinstance.modelfield.modelfield.intfield = '3'
    inputinstance.modelfield.modelfield.matrixfield = [[0, 1, 0, 1], [1, 2, 3, 4], ['1', '0', '1', '0']]
    inputinstance.modelfield.modelfield.listfield = None
    inputinstance.modelfield.modelfield.modelfield = M(init=input_init)
    inputinstance.modelfield.modelfield.modelfield.intfield = '0'
    inputinstance.modelfield.modelfield.modelfield.reqfield = 'foo'
    inputinstance.modelfield.modelfield.modelfield.listfield = None

    return inputinstance


@pytest.fixture
def input(input_instance, input_init):
    if input_instance:
        return get_input_instance(input_init)
    else:
        return get_input_dict()


@pytest.mark.parametrize('input_instance, input_init, init,  missing_obj',
                       [( False,          None,       True,  None),
                        ( False,          None,       False, Undefined),
                        ( True,           False,      True,  None),
                        ( True,           False,      False, Undefined),
                        ( True,           True,       True,  None),
                        ( True,           True,       False, None)])
def test_conversion(input, init, missing_obj):

    m = M(input, init=init)

    assert type(m.intfield) is int
    assert type(m.modelfield.modelfield.intfield) is int
    assert type(m.modelfield.modelfield.matrixfield[2][3]) is int

    assert type(m.listfield) is list
    assert type(m.modelfield) is M
    assert type(m.modelfield.modelfield) is M
    assert type(m.modelfield.modelfield.modelfield) is M
    assert type(m.modelfield.listfield) is list
    assert type(m.modelfield.modelfield.matrixfield) is list
    assert type(m.modelfield.modelfield.matrixfield[2]) is list

    assert m._data['listfield'] == []
    assert m.modelfield._data['intfield'] is missing_obj
    assert m.modelfield.modelfield._data['listfield'] is None
    assert m.modelfield.modelfield._data['reqfield'] is missing_obj


@pytest.mark.parametrize('partial', (True, False))
@pytest.mark.parametrize('import_, two_pass, input_instance, input_init, init,  missing_obj',
                       [( True,    False,    False,          None,       True,  None),
                        ( True,    False,    False,          None,       False, Undefined),
                        ( True,    False,    True,           False,      True,  None),
                        ( True,    False,    True,           False,      False, Undefined),
                        ( True,    False,    True,           True,       True,  None),
                        ( True,    False,    True,           True,       False, None),
                        ( True,    True,     False,          None,       True,  None),
                        ( True,    True,     False,          None,       False, Undefined),
                        ( True,    True,     True,           False,      True,  None),
                        ( True,    True,     True,           False,      False, Undefined),
                        ( True,    True,     True,           True,       True,  None),
                        ( True,    True,     True,           True,       False, None),
                        ( False,   None,     True,           False,      True,  None),
                        ( False,   None,     True,           False,      False, Undefined),
                        ( False,   None,     True,           True,       True,  None),
                        ( False,   None,     True,           True,       False, None)])
def test_conversion_with_validation(input, init, missing_obj, import_, two_pass, partial):

    if missing_obj is None:
        partial_data = {
            'intfield': 1,
            'reqfield': u'foo',
            'matrixfield': None,
            'modelfield': {
                'intfield': None,
                'reqfield': u'bar',
                'matrixfield': None,
                'modelfield': {
                    'reqfield': None,
                    'listfield': None,
                    'modelfield': M({
                        'intfield': 0,
                        'reqfield': u'foo',
                        'listfield': None})}}}
    else:
        partial_data = {
            'intfield': 1,
            'reqfield': u'foo',
            'modelfield': {
                'reqfield': u'bar',
                'modelfield': {
                    'listfield': None,
                    'modelfield': M({
                        'intfield': 0,
                        'reqfield': u'foo',
                        'listfield': None}, init=False)}}}

    with pytest.raises(DataError) as excinfo:
        if import_:
            if two_pass:
                m = M(input, init=init)
                m.validate(partial=partial)
            else:
                M(input, init=init, partial=partial, validate=True)
        else:
            input.validate(init_values=init, partial=partial)

    messages = excinfo.value.messages

    err_list = messages.pop('listfield')
    assert err_list.pop().type == ValidationError
    assert err_list == []

    err_list = messages['modelfield'].pop('listfield')
    assert err_list.pop().type == ValidationError
    assert err_list.pop().type == ValidationError
    assert err_list == []

    err_list = messages['modelfield']['modelfield'].pop('intfield')
    err_msg = err_list.pop()
    assert err_list == []
    assert err_msg.type == ValidationError

    if not partial:
        err_list = messages['modelfield']['modelfield'].pop('reqfield')
        err_msg = err_list.pop()
        assert err_list == []
        assert err_msg.type == ConversionError
        if missing_obj is None:
            partial_data['modelfield']['modelfield'].pop('reqfield')

    err_dict = messages['modelfield']['modelfield'].pop('matrixfield')
    sub_err_dict = err_dict.pop(1)
    err_list_1 = sub_err_dict.pop(2)
    err_list_2 = sub_err_dict.pop(3)
    assert err_list_1.pop().type == ValidationError
    assert err_list_2.pop().type == ValidationError
    assert err_list_1 == err_list_2 == []
    assert err_dict == sub_err_dict == {}

    assert messages['modelfield'].pop('modelfield') == {}
    assert messages.pop('modelfield') == {}
    assert messages == {}

    assert excinfo.value.partial_data == partial_data

