#!/usr/bin/env python

import unittest
import datetime
from schematics.models import Model
from schematics.validation import (
    validate_instance, validate_values, validate_partial,
    ValidationError)
from schematics.types import StringType, DateTimeType
from schematics.types.compound import ModelType, ListType

class TestChoices(unittest.TestCase):
    def setUp(self):
        class Other(Model):
            info = ListType(StringType())

        class TestDoc(Model):
            language = StringType(choices=['en', 'de'])
            other = ModelType(Other)

        self.data_simple_valid = {'language': 'de'}
        self.data_simple_invalid = {'language': 'fr'}
        self.data_embeded_valid = {
            'language': 'de',
            'other': {
                'info': ['somevalue', 'other']
            }
        }
        self.data_embeded_invalid = {
            'language': 'fr',
            'other': {
                'info': ['somevalue', 'other']
            }
        }

        self.doc_simple_valid = TestDoc(**self.data_simple_valid)
        self.doc_simple_invalid = TestDoc(**self.data_simple_invalid)
        self.doc_embedded_valid = TestDoc(**self.data_embeded_valid)
        self.doc_embedded_invalid = TestDoc(**self.data_embeded_invalid)

    def test_choices_validates(self):
        items, errors = validate_instance(self.doc_simple_valid)
        self.assertEqual(errors, {})

    def test_validation_fails(self):
        items, errors = validate_instance(self.doc_simple_invalid)
        self.assertNotEqual(errors, {})

    def test_choices_validates_with_embedded(self):
        items, errors = validate_instance(self.doc_embedded_valid)
        self.assertEqual(errors, {})

    def test_validation_failes_with_embedded(self):
        items, errors = validate_instance(self.doc_embedded_invalid)
        self.assertNotEqual(errors, {})


class TestRequired(unittest.TestCase):

    def test_validation_fails(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        t = TestDoc()
        items, errors = validate_instance(t)

        self.assertNotEqual(errors, {})
        self.assertEqual(len(errors), 1)  # Only one failure
        self.assertIn(u'This field is required', errors.items()[0][1])

    def test_validation_none_fails(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        t = TestDoc(first_name=None)
        items, errors = validate_instance(t)

        self.assertNotEqual(errors, {})
        self.assertEqual(len(errors), 1)  # Only one failure
        self.assertIn(u'This field is required', errors.items()[0][1])

    def test_validation_none_dirty_pass(self):
        class TestDoc(Model):
            first_name = StringType(required=True, dirty=True)

        t = TestDoc(first_name=None)
        items, errors = validate_instance(t)

        self.assertEqual(errors, {})

    def test_validation_notset_dirty_fails(self):
        class TestDoc(Model):
            first_name = StringType(required=True, dirty=True)

        t = TestDoc()
        items, errors = validate_instance(t)

        self.assertNotEqual(errors, {})
        self.assertEqual(len(errors), 1)  # Only one failure
        self.assertIn(u'This field is required', errors.items()[0][1])

    def test_validation_empty_string_pass(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        t = TestDoc(first_name='')
        items, errors = validate_instance(t)

        self.assertEqual(errors, {})

    def test_validation_empty_string_length_fail(self):
        class TestDoc(Model):
            first_name = StringType(required=True, min_length=1)

        t = TestDoc(first_name='')
        items, errors = validate_instance(t)

        self.assertNotEqual(errors, {})
        self.assertEqual(len(errors), 1)  # Only one failure
        # Length failure, not *FIELD_REQUIRED*
        self.assertIn('first_name', errors)
        self.assertEqual(len(errors['first_name']), 1)

    def test_validation_none_string_length_pass(self):
        class TestDoc(Model):
            first_name = StringType(min_length=1)

        t = TestDoc()
        items, errors = validate_instance(t)

        self.assertEqual(errors, {})



class TestCustomValidators(unittest.TestCase):

    def setUp(self):

        now = datetime.datetime(2012, 1, 1, 0, 0)
        self.future_error_msg = u'Future dates are not valid'

        def is_not_future(dt, *args):
            if dt > now:
                raise ValidationError, self.future_error_msg

        class TestDoc(Model):
            publish = DateTimeType(validators=[is_not_future])
            author = StringType(dirty=True, required=True)
            title = StringType(required=False)

        self.Doc = TestDoc

    def test_custom_validators(self):

        items, errors = validate_values(self.Doc, {
            'publish': datetime.datetime(2012, 2, 1, 0, 0),
            'author': u'Hemingway',
            'title': u'Old Man',
        })

        self.assertEqual(errors, {'publish': [self.future_error_msg]})



if __name__ == '__main__':
    unittest.main()
