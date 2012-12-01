#!/usr/bin/env python

import copy
import unittest
import json

from schematics.models import Model
from .fields import  IntField, StringField
from dictshield.fields.compound import SortedListField, EmbeddedDocumentField, ListField
from dictshield.base import ShieldException


class TestSetGetSingleScalarData(unittest.TestCase):
    def setUp(self):
        self.listfield = ListField(IntField())
        class TestModel(Model):
            the_list = self.listfield
        self.TestModel = TestModel
        self.testmodel = TestModel()

    def test_good_value_for_python(self):
        self.testmodel.the_list = [2]
        self.assertEqual(self.testmodel.the_list, [2])

    def test_single_bad_value_for_python(self):
        self.testmodel.the_list = 2
        self.assertEqual(self.testmodel.the_list, 2) #since no validation happens, nothing should yell at us

    def test_collection_good_values_for_python(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        self.assertEqual(self.testmodel.the_list, [2,2,2,2,2,2])

    def test_collection_bad_values_for_python(self):
        expected = self.testmodel.the_list = ["2","2","2","2","2","2"]
        actual = self.testmodel.the_list
        self.assertEqual(actual, expected)  #since no validation happens, nothing should yell at us

    def test_good_value_for_json(self):
        expected = self.testmodel.the_list = [2]
        actual = self.listfield.for_json(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_for_json(self):
        expected = self.testmodel.the_list = [2,2,2,2,2,2]
        actual = self.listfield.for_json(self.testmodel.the_list)
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
        class EmbeddedTestmodel(EmbeddedDocument):
            bandname = StringField()
        self.embeded_test_document = EmbeddedTestmodel
        self.embedded_field = EmbeddedDocumentField(EmbeddedTestmodel)
        class Testmodel(Document):
            the_doc = ListField(self.embedded_field)
        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_doc = [{'bandname': 'fugazi'}]
        from_testmodel = self.testmodel.the_doc[0]
        new_embedded_test = self.embeded_test_document()
        new_embedded_test['bandname'] = 'fugazi'
        self.assertEqual(from_testmodel, new_embedded_test)


class TestMultipleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestmodel(EmbeddedDocument):
            bandname = StringField()
        class SecondEmbeddedTestmodel(EmbeddedDocument):
            food = StringField()
        self.embeded_test_document = EmbeddedTestmodel
        self.second_embeded_test_document = EmbeddedTestmodel
        
        self.embedded_field = EmbeddedDocumentField(EmbeddedTestmodel)
        self.second_embedded_field = EmbeddedDocumentField(SecondEmbeddedTestmodel)

        class Testmodel(Document):
            the_doc = ListField([self.embedded_field, self.second_embedded_field])

        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    @unittest.expectedFailure #because the set shouldn't upcast until validation
    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_doc = [{'bandname': 'fugazi'}, {'food':'cake'}]
        actual = self.testmodel.the_doc
        embeded_test_one = self.embeded_test_document()
        embeded_test_one['bandname'] = 'fugazi'
        embeded_test_two = self.second_embeded_test_document()
        embeded_test_two['food'] = 'cake'
        expected = [embeded_test_one, embeded_test_two]
        self.assertEqual(actual, expected)
        

class TestSetGetSingleScalarDataSorted(unittest.TestCase):
    def setUp(self):
        self.listfield = SortedListField(IntField())
        class Testmodel(Document):
            the_list = self.listfield
        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    def test_collection_good_values_for_python(self):
        expected = self.testmodel.the_list = [1,2,3,4,5,6]
        self.assertEqual(self.testmodel.the_list, expected)

    def test_collection_good_values_for_python_gets_sorted(self):
        expected = self.testmodel.the_list = [6,5,4,3,2,1]
        expected = copy.copy(expected)
        expected.reverse()
        actual = self.testmodel.to_python()['the_list']
        self.assertEqual(actual, expected)
