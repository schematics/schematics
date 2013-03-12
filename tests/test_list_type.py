#!/usr/bin/env python

import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.serialize import wholelist
from schematics.exceptions import ValidationError


# class TestSetGetSingleScalarData(unittest.TestCase):
#     def setUp(self):
#         self.listtype = ListType(IntType())

#         class TestModel(Model):
#             the_list = self.listtype
#             class Options:
#                 roles = {
#                     'owner': wholelist(),
#                 }

#         self.Testmodel = TestModel
#         self.testmodel = TestModel()


#     def test_good_value_for_python(self):
#         self.assertEqual(self.listtype([2]), [2])
#         self.assertEqual(self.listtype(["2"]), [2])

#     def test_single_bad_value_for_python(self):
#         self.testmodel.the_list = 2
#         # since no validation happens, nothing should yell at us
#         self.assertEqual(self.testmodel.the_list, 2)

#     def test_collection_good_values_for_python(self):
#         self.testmodel.the_list = [2, 2, 2, 2, 2, 2]
#         self.assertEqual(self.testmodel.the_list, [2,2,2,2,2,2])

#     def test_collection_bad_values_for_python(self):
#         expected = self.testmodel.the_list = ["2","2","2","2","2","2"]
#         actual = self.testmodel.the_list
#         # since no validation happens, nothing should yell at us
#         self.assertEqual(actual, expected)

#     def test_good_value_to_primitive(self):
#         expected = self.testmodel.the_list = [2]
#         actual = self.listtype.to_primitive(self.testmodel.the_list)
#         self.assertEqual(actual, expected)

#     def test_good_values_to_primitive(self):
#         expected = self.testmodel.the_list = [2,2,2,2,2,2]
#         actual = self.listtype.to_primitive(self.testmodel.the_list)
#         self.assertEqual(actual, expected)

#     def test_good_value_validates(self):
#         self.testmodel.validate({'the_list': [2, 2, 2, 2, 2, 2]})
#         self.assertEqual(self.testmodel.errors, {})

#     def test_coerceible_value_passes_validation(self):
#         self.testmodel.validate({'the_list': ["2","2","2","2","2","2"]})
#         self.assertEqual(self.testmodel.errors, {})

#     def test_uncoerceible_value_passes_validation(self):
#         self.testmodel.validate({'the_list': ["2","2","2","2","horse","2"]})
#         self.assertNotEqual(self.testmodel.errors, {})

#     def test_validation_converts_value(self):
#         self.testmodel.validate({'the_list': ["2","2","2","2","2","2"]})
#         self.assertEqual(self.testmodel.errors, {})
#         new_list = self.testmodel.the_list
#         self.assertEqual(new_list, [2,2,2,2,2,2])


class TestListTypeWithModelType(unittest.TestCase):

    def test_list_with_default_type(self):
        class CategoryStatsInfo(Model):
            slug = StringType()

        class PlayerInfo(Model):
            categories = ListType(ModelType(CategoryStatsInfo))

        math_stats = CategoryStatsInfo(dict(slug="math"))
        twilight_stats = CategoryStatsInfo(dict(slug="twilight"))
        info = PlayerInfo({
            "categories": [{"slug": "math"}, {"slug": "twilight"}]
        })

        self.assertEqual(info.categories, [math_stats, twilight_stats])

        d = info.serialize()
        self.assertEqual(d, {
            "categories": [{"slug": "math"}, {"slug": "twilight"}]
        })

    def test_set_default(self):
        class CategoryStatsInfo(Model):
            slug = StringType()

        class PlayerInfo(Model):
            categories = ListType(ModelType(CategoryStatsInfo), default=lambda: [])

        info = PlayerInfo()
        self.assertEqual(info.categories, [])

        d = info.serialize()
        self.assertEqual(d, {
            "categories": []
        })

    def test_list_defaults_to_none(self):
        class PlayerInfo(Model):
            following = ListType(StringType)

        info = PlayerInfo()

        self.assertIsNone(info.following)

        self.assertEqual(info.serialize(), {
            "following": None
        })

    def test_list_default_to_none_embedded_model(self):
        class QuestionResource(Model):
            url = StringType()

        class QuestionResources(Model):
            pictures = ListType(ModelType(QuestionResource))

        class Question(Model):
            id = StringType()
            resources = ModelType(QuestionResources)

        class QuestionPack(Model):
            id = StringType()
            questions = ListType(ModelType(Question))

        question_pack = QuestionPack({
            "id": "1",
            "questions": [
                {
                    "id": "1"
                },
                {
                    "id": "2",
                    "resources": {
                        "pictures": []
                    }
                },
                {
                    "id": "3",
                    "resources": {
                        "pictures": [{
                            "url": "http://www.mbl.is/djok"
                        }]
                    }
                },
            ]
        })

        self.assertIsNone(question_pack.questions[0].resources)
        self.assertEqual(question_pack.questions[1].resources["pictures"], [])

        resource = QuestionResource({"url": "http://www.mbl.is/djok"})
        self.assertEqual(question_pack.questions[2].resources["pictures"][0], resource)

    def test_validation_with_min_size(self):
        class User(Model):
            name = StringType()

        field = ListType(ModelType(User), min_size=1)

        with self.assertRaises(ValidationError):
            field.validate(None)

        class Card(Model):
            users = field

        with self.assertRaises(ValidationError) as cm:
            Card({"users": None})

        exception = cm.exception
        self.assertEqual(exception.messages['users'], [u'This field is required.'])

        with self.assertRaises(ValidationError) as cm:
            Card({"users": []})

        exception = cm.exception
        self.assertEqual(exception.messages['users'], [u'Please provide at least 1 item.'])


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
