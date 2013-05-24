#!/usr/bin/env python

import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.exceptions import ValidationError


class TestModelType(unittest.TestCase):

    def test_simple_embedded_models(self):
        class Location(Model):
            country_code = StringType()

        class Player(Model):
            id = IntType()
            location = ModelType(Location)

        p = Player(dict(id=1, location={"country_code": "US"}))

        self.assertEqual(p.id, 1)
        self.assertEqual(p.location.country_code, "US")

        p.location = Location({"country_code": "IS"})

        self.assertIsInstance(p.location, Location)
        self.assertEqual(p.location.country_code, "IS")

    def test_simple_embedded_models_is_none(self):
        class Location(Model):
            country_code = StringType()

        class Player(Model):
            id = IntType()
            location = ModelType(Location)

        p = Player(dict(id=1))

        self.assertEqual(p.id, 1)
        self.assertIsNone(p.location)

    def test_simple_embedded_model_is_none_within_listtype(self):
        class QuestionResources(Model):
            type = StringType()

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
            ]
        })

        self.assertIsNone(question_pack.questions[0].resources)

    def test_raises_validation_error_on_init_with_partial_submodel(self):
        class User(Model):
            name = StringType(required=True)
            age = IntType(required=True)

        class Card(Model):
            user = ModelType(User)

        u = User({'name': 'Arthur'})
        c = Card({'user': u})

        with self.assertRaises(ValidationError):
            c.validate()

    def test_model_type(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        c = Card({"user": {'name': u'Doggy'}})
        self.assertIsInstance(c.user, User)
        self.assertEqual(c.user.name, "Doggy")

    def test_equality_with_embedded_models(self):
        class Location(Model):
            country_code = StringType()

        class Player(Model):
            id = IntType()
            location = ModelType(Location)

        p1 = Player(dict(id=1, location={"country_code": "US"}))
        p2 = Player(dict(id=1, location={"country_code": "US"}))

        self.assertNotEqual(id(p1.location), id(p2.location))
        self.assertEqual(p1.location, p2.location)

        self.assertEqual(p1, p2)

    def test_default_value_when_embedded_model(self):
        class Question(Model):
            question_id = StringType(required=True)

            type = StringType(default="text")

        class QuestionPack(Model):

            question = ModelType(Question)

        pack = QuestionPack({
            "question": {
                "question_id": 1
            }
        })

        self.assertEqual(pack.question.question_id, "1")
        self.assertEqual(pack.question.type, "text")
