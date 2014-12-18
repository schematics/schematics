# -*- coding: utf-8 -*-
import pytest

from schematics.models import Model
from schematics.types import BaseType, IntType, StringType
from schematics.types.compound import ListType, DictType, ModelType
from schematics.exceptions import ModelConversionError, ModelValidationError

def test_nested_mapping():

    mapping = {
        'model_mapping': {
            'modelfield': {
                'subfield': 'importfield'
            }
        }
    }

    class SubModel(Model):
        subfield = StringType()

    class MainModel(Model):
        modelfield = ModelType(SubModel)

    m1 = MainModel({
        'modelfield': {'importfield':'qweasd'},
        }, deserialize_mapping=mapping)

    assert m1.modelfield.subfield == 'qweasd'

def test_nested_mapping_with_required():

    mapping = {
        'model_mapping': {
            'modelfield': {
                'subfield': 'importfield'
            }
        }
    }

    class SubModel(Model):
        subfield = StringType(required=True)

    class MainModel(Model):
        modelfield = ModelType(SubModel)

    m1 = MainModel({ # Note partial=False here!
        'modelfield': {'importfield':'qweasd'},
        }, partial=False, deserialize_mapping=mapping)

def test_submodel_required_field():

    class SubModel(Model):
        subfield1 = StringType(required=True)
        subfield2 = StringType()

    class MainModel(Model):
        intfield = IntType()
        stringfield = StringType()
        modelfield = ModelType(SubModel)

    # By default, model instantiation assumes partial=True
    m1 = MainModel({
        'modelfield': {'subfield2':'qweasd'}})

    with pytest.raises(ModelConversionError):
        m1 = MainModel({
            'modelfield': {'subfield2':'qweasd'}}, partial=False)

    # Validation implies partial=False
    with pytest.raises(ModelValidationError):
        m1.validate()

    m1.validate(partial=True)

