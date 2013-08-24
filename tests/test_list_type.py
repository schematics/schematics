#!/usr/bin/env python

import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.transforms import wholelist
from schematics.exceptions import ValidationError


class TestListTypeWithModelType(unittest.TestCase):

    def test_list_field(self):
        class User(Model):
            ids = ListType(StringType, required=True)

        c = User({
            "ids": []
        })

        c.validate({'ids': []})

        self.assertEqual(c.ids, [])

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
            categories = ListType(ModelType(CategoryStatsInfo),
                                  default=lambda: [],
                                  serialize_when_none=True)

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

        class Card(Model):
            users = ListType(ModelType(User), min_size=1, required=True)

        with self.assertRaises(ValidationError) as cm:
            c = Card({"users": None})
            c.validate()

        exception = cm.exception
        self.assertEqual(exception.messages['users'], [u'This field is required.'])

        print 'BEFORE'
        with self.assertRaises(ValidationError) as cm:
            c = Card({"users": []})
            c.validate()
        print 'AFTER'

        exception = cm.exception
        print 'EXC:', type(exception)
        self.assertEqual(exception.messages['users'], [u'Please provide at least 1 item.'])

    def test_list_field_required(self):
        class User(Model):
            ids = ListType(StringType(required=True))

        c = User({
            "ids": []
        })

        c.ids = [1]
        c.validate()

        c.ids = [None]
        with self.assertRaises(ValidationError):
            c.validate()

    def test_list_field_convert(self):
        class User(Model):
            ids = ListType(IntType)

        c = User({'ids': ["1", "2"]})

        self.assertEqual(c.ids, [1, 2])

    def test_list_model_field(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            users = ListType(ModelType(User), min_size=1, required=True)

        data = {'users': [{'name': u'Doggy'}]}
        c = Card(data)

        c.users = None
        with self.assertRaises(ValidationError) as context:
            c.validate()

        errors = context.exception.messages

        self.assertEqual(errors['users'], [u'This field is required.'])
