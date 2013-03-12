#!/usr/bin/env python

import unittest
from schematics.models import Model
from schematics.validation import validate
from schematics.types import StringType
from schematics.types.compound import ModelType, ListType
from schematics.exceptions import ValidationError


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

    def test_missing_attrs_dont_error(self):
        class TestDoc(Model):
            language = StringType(choices=['en', 'de'])
        TestDoc().validate()

    def test_missing_required_errors(self):
        class TestDoc(Model):
            language = StringType(choices=['en', 'de'], required=True)
        fun = lambda: TestDoc().validate()
        self.assertRaises(ValidationError, fun)

    def test_choices_validates(self):
        self.doc_simple_valid.validate()

    def test_validation_fails(self):
        fun = lambda: self.doc_simple_invalid.validate()
        self.assertRaises(ValidationError, fun)

    def test_choices_validates_with_embedded(self):
        self.doc_embedded_valid.validate()

    def test_validation_failes_with_embedded(self):
        fun = lambda: self.doc_embedded_invalid.validate()
        self.assertRaises(ValidationError, fun)


class TestRequired(unittest.TestCase):
    def setUp(self):
        class TestDoc(Model):
            first_name = StringType(required=True, min_length=2)
            last_name = StringType()

        self.data_simple_valid = {'first_name': 'Alex', 'last_name': 'Fox'}
        self.data_simple_invalid = {}

        self.doc_simple_valid = TestDoc(**self.data_simple_valid)
        self.doc_simple_invalid = TestDoc(**self.data_simple_invalid)

    def test_required_validates(self):
        self.doc_simple_valid.validate()

    def test_validation_fails(self):
        fun = lambda: self.doc_simple_invalid.validate()
        self.assertRaises(ValidationError, fun)


if __name__ == '__main__':
    unittest.main()
