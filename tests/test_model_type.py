#!/usr/bin/env python

import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.serialize import wholelist
from schematics.exceptions import ValidationError


class TestSetGetSingleScalarData(unittest.TestCase):

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

