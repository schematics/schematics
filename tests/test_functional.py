
import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.validate import validate


class TestFunctionalInterface(unittest.TestCase):

    def test_validate_simple_dict(self):
        class Player(Model):
            id = IntType()

        _, errors = validate(Player, {'id': 4})
        self.assertFalse(errors)

    def test_validate_keep_context_data(self):
        class Player(Model):
            id = IntType()
            name = StringType()

        p1 = Player({'id': 4})
        data, errors = validate(p1, {'name': 'Arthur'}, context=p1._data)

        self.assertFalse(errors)
        self.assertEqual(data, {'id': 4, 'name': 'Arthur'})
        self.assertNotEqual(data, p1._data)

    def test_validate_override_context_data(self):
        class Player(Model):
            id = IntType()

        p1 = Player({'id': 4})
        data, errors = validate(p1, {'id': 3}, context=p1._data)

        self.assertFalse(errors)
        self.assertEqual(data, {'id': 3})

    def test_validate_ignore_extra_context_data(self):
        class Player(Model):
            id = IntType()

        data, errors = validate(Player, {'id': 4}, context={'name': 'Arthur'})

        self.assertFalse(errors)
        self.assertEqual(data, {'id': 4, 'name': 'Arthur'})
