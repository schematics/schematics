#!/usr/bin/env python

import copy
import unittest
import json

from schematics.models import Model
from schematics.types import  IntType, StringType
from schematics.types.compound import SortedListType, ModelType, ListType
from schematics.serialize import (to_python, wholelist, make_safe_json,
                                  make_safe_python)
from schematics.validation import validate
from schematics.exceptions import ValidationError


class TestSetGetSingleScalarData(unittest.TestCase):
    def setUp(self):
        self.listtype = ListType(IntType())
        
        class TestModel(Model):
            the_list = self.listtype
            class Options:
                roles = {
                    'owner': wholelist(),
                }
            
        self.Testmodel = TestModel
        self.testmodel = TestModel()

    def test_good_value_for_python(self):
        self.testmodel.the_list = [2]
        self.assertEqual(self.testmodel.the_list, [2])

    def test_single_bad_value_for_python(self):
        self.testmodel.the_list = 2
        # since no validation happens, nothing should yell at us        
        self.assertEqual(self.testmodel.the_list, 2) 

    def test_collection_good_values_for_python(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        self.assertEqual(self.testmodel.the_list, [2,2,2,2,2,2])

    def test_collection_bad_values_for_python(self):
        expected = self.testmodel.the_list = ["2","2","2","2","2","2"]
        actual = self.testmodel.the_list
        # since no validation happens, nothing should yell at us        
        self.assertEqual(actual, expected)  

    def test_good_value_for_json(self):
        expected = self.testmodel.the_list = [2]
        actual = self.listtype.for_json(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_for_json(self):
        expected = self.testmodel.the_list = [2,2,2,2,2,2]
        actual = self.listtype.for_json(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_into_json(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        actual = make_safe_json(self.Testmodel, self.testmodel, 'owner')
        expected = json.dumps({"the_list":[2,2,2,2,2,2]})
        self.assertEqual(actual, expected)

    def test_good_value_into_json(self):
        self.testmodel.the_list = [2]
        actual = make_safe_json(self.Testmodel, self.testmodel, 'owner')
        expected = json.dumps({"the_list":[2]})
        self.assertEqual(actual, expected)

    def test_good_value_validates(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        self.testmodel.validate()

    def test_coerceible_value_passes_validation(self):
        self.testmodel.the_list = ["2","2","2","2","2","2"]
        self.testmodel.validate()

    def test_uncoerceible_value_passes_validation(self):
        self.testmodel.the_list = ["2","2","2","2","horse","2"]
        fun = lambda: self.testmodel.validate()
        self.assertRaises(ValidationError, fun)
        
    def test_validation_converts_value(self):
        self.testmodel.the_list = ["2","2","2","2","2","2"]
        self.testmodel.validate()
        result = to_python(self.testmodel)
        new_list = result['the_list']
        self.assertEqual(new_list, [2,2,2,2,2,2])

        
class TestGetSingleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestmodel(Model):
            bandname = StringType()
            
        self.embedded_test_model = EmbeddedTestmodel
        self.embedded_type = ModelType(EmbeddedTestmodel)
        
        class Testmodel(Model):
            the_list = ListType(self.embedded_type)
            
        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_list = [{'bandname': 'fugazi'}]
        from_testmodel = self.testmodel.the_list[0]
        new_embedded_test = self.embedded_test_model()
        new_embedded_test['bandname'] = 'fugazi'
        self.assertEqual(from_testmodel, new_embedded_test)


class TestMultipleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class BandModel(Model):
            bandname = StringType()
            
        class FoodModel(Model):
            food = StringType()
            
        self.food_model = FoodModel
        self.band_model = BandModel
        self.the_list = ListType([ModelType(self.band_model),
                                  ModelType(self.food_model)])
        
        class Testmodel(Model):
            the_list = ListType([ModelType(self.band_model),
                                 ModelType(self.food_model)])

        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    #@unittest.expectedFailure #because the set shouldn't upcast until validation
    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_list = [{'bandname': 'fugazi'}, {'food':'cake'}]
        
        actual = self.testmodel.the_list
        
        band = self.band_model()
        band['bandname'] = 'fugazi'
        
        food = self.food_model()
        food['food'] = 'cake'
        
        expected = [band, food]
        self.assertEqual(actual, expected)
        

class TestSetGetSingleScalarDataSorted(unittest.TestCase):
    def setUp(self):
        self.listtype = SortedListType(IntType())
        
        class Testmodel(Model):
            the_list = self.listtype
            
        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    def test_collection_good_values_for_python(self):
        expected = self.testmodel.the_list = [1,2,3,4,5,6]
        self.assertEqual(self.testmodel.the_list, expected)

    def test_collection_good_values_for_python_gets_sorted(self):
        expected = self.testmodel.the_list = [6,5,4,3,2,1]
        expected = copy.copy(expected)
        expected.reverse()
        actual = to_python(self.testmodel)['the_list']
        self.assertEqual(actual, expected)
