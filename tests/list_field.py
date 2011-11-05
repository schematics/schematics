import unittest
from dictshield.document import Document
from dictshield.fields.base import ListField, IntField
from fixtures import demos

class TestSingleScalarData(unittest.TestCase):
    def setUp(self):
        class TestDocument(Document):
            the_list = ListField(IntField())
        self.testdoc = TestDocument()

    def test_good_value(self):
        self.testdoc.the_list = [2]
        self.assertEqual(self.testdoc.the_list, [2])

    def test_single_good_value(self):
        self.testdoc.the_list = 2
        self.assertEqual(self.testdoc.the_list, [2])


if __name__ == '__main__':
    unittest.main()
