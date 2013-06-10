
import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.exceptions import ModelValidationError, ValidationError


class TestDataIntegrity(unittest.TestCase):

    def test_dont_serialize_invalid_data(self):
        """
        Serialization must always contain just the subset of valid
        data from the model.

        """
        class Player(Model):
            code = StringType(max_length=4)

        p1 = Player({'code': 'invalid1'})
        self.assertEqual(p1.serialize(), {'code': None})
        self.assertRaises(ModelValidationError, p1.validate)
        self.assertEqual(p1.serialize(), {'code': None})

    def test_dont_overwrite_with_invalid_data(self):
        """
        Model-level validators are black-boxes and we should not assume
        that we can set the instance data at any time.

        """
        class Player(Model):
            id = IntType()

            def validate_id(self, context, value):
                if self._data.get('id'):
                    raise ValidationError('Cannot change id')

        p1 = Player({'id': 4})
        p1.validate()
        p1.id = 3
        self.assertRaises(ModelValidationError, p1.validate)
        self.assertEqual(p1.id, 4)

    def test_model_state_after_multiple_validation(self):
        """
        Validation must maintain a sane state after multiple operations.

        """
        class Player(Model):
            id = IntType()
            code = StringType(max_length=4)

        p1 = Player({'id': 4})
        p1.validate()
        self.assertEqual(p1.serialize(), {'id': 4, 'code': None})
        p1.code = 'AAA'
        p1.validate()
        self.assertEqual(p1.serialize(), {'id': 4, 'code': 'AAA'})
        p1.code = 'BBB'
        p1.validate()
        self.assertEqual(p1.serialize(), {'id': 4, 'code': 'BBB'})
        p1.code = 'CCCERR'
        self.assertRaises(ValidationError, p1.validate)
        self.assertEqual(p1.serialize(), {'id': 4, 'code': 'BBB'})
        p1.validate()
        self.assertEqual(p1.serialize(), {'id': 4, 'code': 'BBB'})

    def test_dont_forget_required_fields_after_multiple_validation(self):
        """
        Validation should not forget about required fields, even if invalid
        data is cleared from input, since it doesn't rely on actual input.

        """
        class Player(Model):
            code = StringType(required=True)

        p1 = Player()
        self.assertRaises(ModelValidationError, p1.validate)
        self.assertRaises(ModelValidationError, p1.validate)
