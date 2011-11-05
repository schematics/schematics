import copy
import unittest
import json
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields.base import SortedListField, IntField, EmbeddedDocumentField, StringField, ListField
from dictshield.base import ShieldException

class TestSetGetSingleScalarData(unittest.TestCase):
    def setUp(self):
        self.listfield = ListField(IntField())
        class TestDocument(Document):
            the_list = self.listfield
        self.TestDoc = TestDocument
        self.testdoc = TestDocument()

    def test_good_value_for_python(self):
        self.testdoc.the_list = [2]
        self.assertEqual(self.testdoc.the_list, [2])

    def test_single_bad_value_for_python(self):
        self.testdoc.the_list = 2
        self.assertEqual(self.testdoc.the_list, 2) #since no validation happens, nothing should yell at us

    def test_collection_good_values_for_python(self):
        self.testdoc.the_list = [2,2,2,2,2,2]
        self.assertEqual(self.testdoc.the_list, [2,2,2,2,2,2])

    def test_collection_bad_values_for_python(self):
        expected = self.testdoc.the_list = ["2","2","2","2","2","2"]
        actual = self.testdoc.the_list
        self.assertEqual(actual, expected)  #since no validation happens, nothing should yell at us

    def test_good_value_for_json(self):
        expected = self.testdoc.the_list = [2]
        actual = self.listfield.for_json(self.testdoc.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_for_json(self):
        expected = self.testdoc.the_list = [2,2,2,2,2,2]
        actual = self.listfield.for_json(self.testdoc.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_into_json(self):
        self.testdoc.the_list = [2,2,2,2,2,2]
        actual = self.TestDoc.make_json_ownersafe(self.testdoc)
        expected = json.dumps({"the_list":[2,2,2,2,2,2]})
        self.assertEqual(actual, expected)

    def test_good_value_into_json(self):
        self.testdoc.the_list = [2]
        actual = self.TestDoc.make_json_ownersafe(self.testdoc)
        expected = json.dumps({"the_list":[2]})
        self.assertEqual(actual, expected)

    def test_good_value_validates(self):
        self.testdoc.the_list = [2,2,2,2,2,2]
        self.testdoc.validate()

    def test_coerceible_value_passes_validation(self):
        self.testdoc.the_list = ["2","2","2","2","2","2"]
        self.testdoc.validate()

    def test_uncoerceible_value_passes_validation(self):
        self.testdoc.the_list = ["2","2","2","2","horse","2"]
        self.assertRaises(ShieldException, self.testdoc.validate)        
        
    @unittest.expectedFailure
    def test_validation_converts_value(self):
        self.testdoc.the_list = ["2","2","2","2","2","2"]
        self.testdoc.validate()
        self.assertEqual(self.testdoc.the_list, [2,2,2,2,2,2])

class TestGetSingleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestDocument(EmbeddedDocument):
            bandname = StringField()
        self.embeded_test_document = EmbeddedTestDocument
        self.embedded_field = EmbeddedDocumentField(EmbeddedTestDocument)
        class TestDocument(Document):
            the_doc = ListField(self.embedded_field)
        self.TestDoc = TestDocument
        self.testdoc = TestDocument()

    @unittest.expectedFailure #because the set shouldn't upcast until validation
    def test_good_value_for_python_upcasts(self):
        self.testdoc.the_doc = [{'bandname': 'fugazi'}]
        actual = self.testdoc.the_doc
        embeded_test = self.embeded_test_document()
        embeded_test['bandname'] = 'fugazi'
        expected = [embeded_test]
        self.assertEqual(actual, expected)


class TestMultipleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestDocument(EmbeddedDocument):
            bandname = StringField()
        class SecondEmbeddedTestDocument(EmbeddedDocument):
            food = StringField()
        self.embeded_test_document = EmbeddedTestDocument
        self.second_embeded_test_document = EmbeddedTestDocument
        
        self.embedded_field = EmbeddedDocumentField(EmbeddedTestDocument)
        self.second_embedded_field = EmbeddedDocumentField(SecondEmbeddedTestDocument)

        class TestDocument(Document):
            the_doc = ListField([self.embedded_field, self.second_embedded_field])

        self.TestDoc = TestDocument
        self.testdoc = TestDocument()


    @unittest.expectedFailure #because the set shouldn't upcast until validation
    def test_good_value_for_python_upcasts(self):
        self.testdoc.the_doc = [{'bandname': 'fugazi'}, {'food':'cake'}]
        actual = self.testdoc.the_doc
        embeded_test_one = self.embeded_test_document()
        embeded_test_one['bandname'] = 'fugazi'
        embeded_test_two = self.second_embeded_test_document()
        embeded_test_two['food'] = 'cake'
        expected = [embeded_test_one, embeded_test_two]
        self.assertEqual(actual, expected)
        

class TestSetGetSingleScalarDataSorted(unittest.TestCase):
    def setUp(self):
        self.listfield = SortedListField(IntField())
        class TestDocument(Document):
            the_list = self.listfield
        self.TestDoc = TestDocument
        self.testdoc = TestDocument()

    def test_collection_good_values_for_python(self):
        expected = self.testdoc.the_list = [1,2,3,4,5,6]
        self.assertEqual(self.testdoc.the_list, expected)

    def test_collection_good_values_for_python_gets_sorted(self):
        expected = self.testdoc.the_list = [6,5,4,3,2,1]
        expected = copy.copy(expected)
        expected.reverse()
        actual = self.testdoc.to_python()['the_list']
        self.assertEqual(actual, expected)


        

if __name__ == '__main__':
    unittest.main()
