#!/usr/bin/env python

import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType


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

        p.location = {"country_code": "IS"}

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

    def test_simple_embedded_model_is_none_within_listtypw(self):
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


