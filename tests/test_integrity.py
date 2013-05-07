
import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.exceptions import ValidationError


class TestDataIntegrity(unittest.TestCase):

    def test_dont_serialize_invalid_data(self):
        """
        Serialization must always contain just the subset of valid
        data from the model.

        """
        class Player(Model):
            code = StringType(max_length=4)

        p1 = Player({'code': 'invalid1'})
        self.assertRaises(ValidationError, p1.validate)
        self.assertEqual(p1.serialize(), {'code': None})
