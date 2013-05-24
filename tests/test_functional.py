
import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.validate import validate
from schematics.exceptions import ValidationError


class TestFunctionalInterface(unittest.TestCase):

    def test_validate_simple_dict(self):
        class Player(Model):
            id = IntType()

        validate(Player, {'id': 4})            

    def test_validate_keep_context_data(self):
        class Player(Model):
            id = IntType()
            name = StringType()

        p1 = Player({'id': 4})
        data = validate(Player, {'name': 'Arthur'}, context=p1._data)

        self.assertEqual(data, {'id': 4, 'name': 'Arthur'})
        self.assertNotEqual(data, p1._data)

    def test_validate_override_context_data(self):
        class Player(Model):
            id = IntType()

        p1 = Player({'id': 4})
        data = validate(Player, {'id': 3}, context=p1._data)

        self.assertEqual(data, {'id': 3})

    def test_validate_ignore_extra_context_data(self):
        class Player(Model):
            id = IntType()

        data = validate(Player, {'id': 4}, context={'name': 'Arthur'})

        self.assertEqual(data, {'id': 4, 'name': 'Arthur'})

    def test_validate_strict_with_context_data(self):
        class Player(Model):
            id = IntType()

        try:
            data = validate(Player, {'id': 4}, strict=True, context={'name': 'Arthur'})
        except ValidationError as e:
            self.assertIn('name', e.messages)

    def test_validate_partial_with_context_data(self):
        class Player(Model):
            id = IntType()
            name = StringType(required=True)

        data = validate(Player, {'id': 4}, partial=False, context={'name': 'Arthur'})

        self.assertEqual(data, {'id': 4, 'name': 'Arthur'})

    def test_validate_with_instance_level_validators(self):
        class Player(Model):
            id = IntType()

            def validate_id(self, context, value):
                if self.id:
                    raise ValidationError('Cannot change id')

        p1 = Player({'id': 4})

        try:
            data = validate(p1, {'id': 3})
        except ValidationError as e:
            self.assertIn('id', e.messages)
            self.assertIn('Cannot change id', e.messages['id'])
            self.assertEqual(p1.id, 4)
