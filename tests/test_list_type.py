#!/usr/bin/env python

import copy
import unittest

from schematics import Model
from schematics.types import  IntType, StringType
from schematics.types.compound import SortedListType, ModelType, ListType
from schematics.serialize import wholelist, to_safe_dict
from schematics.validation import validate_instance


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

    def test_good_value_to_dict(self):
        expected = self.testmodel.the_list = [2]
        actual = self.listtype.to_dict(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_to_dict(self):
        expected = self.testmodel.the_list = [2,2,2,2,2,2]
        actual = self.listtype.to_dict(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_into_dict(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        actual = to_safe_dict(self.Testmodel, self.testmodel, 'owner')
        expected = {"the_list":[2,2,2,2,2,2]}
        self.assertEqual(actual, expected)

    def test_good_value_into_dict(self):
        self.testmodel.the_list = [2]
        actual = to_safe_dict(self.Testmodel, self.testmodel, 'owner')
        expected = {"the_list":[2]}
        self.assertEqual(actual, expected)

    def test_good_value_validates(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        items, errors = validate_instance(self.testmodel)
        self.assertEqual(errors, {})

    def test_coerceible_value_passes_validation(self):
        self.testmodel.the_list = ["2","2","2","2","2","2"]
        items, errors = validate_instance(self.testmodel)
        self.assertEqual(errors, {})

    def test_uncoerceible_value_passes_validation(self):
        self.testmodel.the_list = ["2","2","2","2","horse","2"]
        items, errors = validate_instance(self.testmodel)
        self.assertNotEqual(errors, {})

    def test_validation_converts_value(self):
        self.testmodel.the_list = ["2","2","2","2","2","2"]
        items, errors = validate_instance(self.testmodel)
        self.assertEqual(errors, {})
        new_list = items['the_list']
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
        actual = self.testmodel.to_dict()["the_list"]
        self.assertEqual(actual, expected)
