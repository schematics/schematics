import copy
import unittest
import json
from dictshield.document import Document
from dictshield.fields.base import IntField

class TestEqualityTest(unittest.TestCase):
    def setUp(self):
        class TestDocument(Document):
            some_int = IntField()
        self.TestDoc = TestDocument
        self.testdoc = TestDocument()

    def test_equality(self):
        self.testdoc.some_int = 4
        self.assertEqual(self.testdoc, copy.copy(self.testdoc)) 
        some_other_doc = self.TestDoc()
        some_other_doc.some_int = 4
        self.assertNotEqual(self.testdoc, some_other_doc)
        del some_other_doc._fields['id']
        self.assertEqual(self.testdoc, some_other_doc)


if __name__ == '__main__':
    unittest.main()
