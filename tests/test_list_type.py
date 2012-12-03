#!/usr/bin/env python

import copy
import unittest
import json

from schematics.models import Model
from schematics.types import  IntType, StringType
from schematics.types.compound import SortedListType, ModelType, ListType
from schematics.serialize import to_python


class TestSetGetSingleScalarData(unittest.TestCase):
    def setUp(self):
        self.listtype = ListType(IntType())
        
        class TestModel(Model):
            the_list = self.listtype
            
        self.TestModel = TestModel
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
        actual = self.Testmodel.make_json_ownersafe(self.testmodel)
        expected = json.dumps({"the_list":[2,2,2,2,2,2]})
        self.assertEqual(actual, expected)

    def test_good_value_into_json(self):
        self.testmodel.the_list = [2]
        actual = self.Testmodel.make_json_ownersafe(self.testmodel)
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
        self.assertRaises(ShieldException, self.testmodel.validate)        
        
    @unittest.expectedFailure
    def test_validation_converts_value(self):
        self.testmodel.the_list = ["2","2","2","2","2","2"]
        self.testmodel.validate()
        self.assertEqual(self.testmodel.the_list, [2,2,2,2,2,2])

        
class TestGetSingleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestmodel(Model):
            bandname = StringType()
            
        self.embedded_test_document = EmbeddedTestmodel
        self.embedded_type = ModelType(EmbeddedTestmodel)
        
        class Testmodel(Model):
            the_doc = ListType(self.embedded_field)
            
        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_doc = [{'bandname': 'fugazi'}]
        from_testmodel = self.testmodel.the_doc[0]
        new_embedded_test = self.embedded_test_document()
        new_embedded_test['bandname'] = 'fugazi'
        self.assertEqual(from_testmodel, new_embedded_test)


class TestMultipleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestmodel(Model):
            bandname = StringType()
            
        class SecondEmbeddedTestmodel(Model):
            food = StringType()
            
        self.embedded_test_document = EmbeddedTestmodel
        self.second_embedded_test_document = EmbeddedTestmodel
        
        self.embedded_type = ModelType(EmbeddedTestmodel)
        self.second_embedded_type = ModelType(SecondEmbeddedTestmodel)

        class Testmodel(Model):
            the_doc = ListType([self.embedded_type, self.second_embedded_type])

        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    @unittest.expectedFailure #because the set shouldn't upcast until validation
    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_doc = [{'bandname': 'fugazi'}, {'food':'cake'}]
        actual = self.testmodel.the_doc
        embedded_test_one = self.embedded_test_document()
        embedded_test_one['bandname'] = 'fugazi'
        embedded_test_two = self.second_embedded_test_document()
        embedded_test_two['food'] = 'cake'
        expected = [embedded_test_one, embedded_test_two]
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
