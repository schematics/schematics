#!/usr/bin/env python

import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.serialize import wholelist


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
        self.listtype([2])
        self.assertEqual(self.listtype.clean, [2])
        self.listtype(["2"])
        self.assertEqual(self.listtype.clean, [2])

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

    def test_good_value_to_primitive(self):
        expected = self.testmodel.the_list = [2]
        actual = self.listtype.to_primitive(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_to_primitive(self):
        expected = self.testmodel.the_list = [2,2,2,2,2,2]
        actual = self.listtype.to_primitive(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_value_validates(self):
        self.testmodel.validate({'the_list': [2,2,2,2,2,2]})
        self.assertEqual(self.testmodel.errors, {})

    def test_coerceible_value_passes_validation(self):
        self.testmodel.validate({'the_list': ["2","2","2","2","2","2"]})
        self.assertEqual(self.testmodel.errors, {})

    def test_uncoerceible_value_passes_validation(self):
        self.testmodel.validate({'the_list': ["2","2","2","2","horse","2"]})
        self.assertNotEqual(self.testmodel.errors, {})

    def test_validation_converts_value(self):
        self.testmodel.validate({'the_list': ["2","2","2","2","2","2"]})
        self.assertEqual(self.testmodel.errors, {})
        new_list = self.testmodel.the_list
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
