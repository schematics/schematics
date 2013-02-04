#!/usr/bin/env python

import unittest
from schematics.models import Model
from schematics.validation import validate_instance
from schematics.types import StringType
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
        result = validate_instance(self.doc_simple_valid)
        self.assertEqual(result.tag, 'OK')

    def test_validation_fails(self):
        result = validate_instance(self.doc_simple_invalid)
        self.assertNotEqual(result.tag, 'OK')

    def test_choices_validates_with_embedded(self):
        result = validate_instance(self.doc_embedded_valid)
        self.assertEqual(result.tag, 'OK')

    def test_validation_failes_with_embedded(self):
        result = validate_instance(self.doc_embedded_invalid)
        self.assertNotEqual(result.tag, 'OK')

def suite():
    suite = unittest.TestSuite()
    return suite

if __name__ == '__main__':
    unittest.main()
