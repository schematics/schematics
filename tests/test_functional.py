
import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.validate import validate
from schematics.exceptions import ValidationError, ModelConversionError


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

        with self.assertRaises(ValidationError) as e:
            data = validate(Player, {'id': 4}, strict=True, context={'name': 'Arthur'})
        self.assertIn('name', e.exception.messages)

        with self.assertRaises(ModelConversionError) as e:
            Player({'id': 4, 'name': 'Arthur'}).validate(strict=True)
        self.assertIn('name', e.exception.messages)

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
                if p1._initial['id'] != value:
                    p1._data['id'] = p1._initial['id']
                    raise ValidationError('Cannot change id')

        p1 = Player({'id': 4})
        p1.id = 3

        try:
            data = validate(Player, p1)
        except ValidationError as e:
            self.assertIn('id', e.messages)
            self.assertIn('Cannot change id', e.messages['id'])
            self.assertEqual(p1.id, 4)
