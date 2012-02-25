import unittest
from dictshield import fields
from dictshield.document import Document, ShieldException, EmbeddedDocument
from dictshield.fields.compound import EmbeddedDocumentField, ListField


class TestChoices(unittest.TestCase):

    def setUp(self):

        class Other(EmbeddedDocument):
            info = ListField(fields.StringField())

        class TestDoc(Document):
            language = fields.StringField(choices=['en', 'de'])
            other = EmbeddedDocumentField(Other)

        self.data_simple_valid = {'language': 'de'}
        self.data_simple_invalid = {'language': 'fr'}
        self.data_embeded_valid = {'language': 'de',
                                   'other':
                                           {'info': ['somevalue', 'other']}}
        self.data_embeded_invalid = {'language': 'fr',
                                    'other':
                                            {'info': ['somevalue', 'other']}}
        self.doc_simple_valid = TestDoc(**self.data_simple_valid)
        self.doc_simple_invalid = TestDoc(**self.data_simple_invalid)
        self.doc_embedded_valid = TestDoc(**self.data_embeded_valid)
        self.doc_embedded_invalid = TestDoc(**self.data_embeded_invalid)

    def test_choices_validates(self):
        self.assertTrue(self.doc_simple_valid.validate())

    def test_validation_failes(self):
        self.assertRaises(ShieldException, self.doc_simple_invalid.validate)

    def test_choices_validates_with_embedded(self):
        self.assertTrue(self.doc_embedded_valid.validate())

    def test_validation_failes_with_embedded(self):
        self.assertRaises(ShieldException, self.doc_embedded_invalid.validate)

