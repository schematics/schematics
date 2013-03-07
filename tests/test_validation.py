#!/usr/bin/env python

import unittest
import datetime

from schematics.models import Model
from schematics.exceptions import ValidationError
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
        valid = self.doc_simple_valid.validate(self.data_simple_valid)
        self.assertEqual(valid, True)

    def test_validation_fails(self):
        valid = self.doc_simple_invalid.validate(self.data_simple_invalid)
        self.assertNotEqual(valid, True)

    def test_choices_validates_with_embedded(self):
        valid = self.doc_embedded_valid.validate(self.data_embeded_valid)
        self.assertEqual(valid, True)

    def test_validation_failes_with_embedded(self):
        valid = self.doc_embedded_invalid.validate(self.data_embeded_invalid)
        self.assertNotEqual(valid, True)


class TestRequired(unittest.TestCase):

    def test_validation_fails(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        t = TestDoc()
        t.validate({})

        self.assertEqual(len(t.errors), 1)  # Only one failure
        self.assertIn(u'This field is required', t.errors.items()[0][1])

    def test_validation_none_fails(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        t = TestDoc(first_name=None)
        valid = t.validate(t.serialize())

        self.assertNotEqual(t.errors, {})
        self.assertEqual(len(t.errors), 1)  # Only one failure
        self.assertIn(u'This field is required', t.errors.items()[0][1])

    def test_validation_empty_string_not_pass(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        t = TestDoc(first_name='')
        valid = t.validate(t.serialize())
        self.assertEqual(valid, False)

    def test_validation_empty_string_length_fail(self):
        class TestDoc(Model):
            first_name = StringType(required=True, min_length=1)

        t = TestDoc(first_name='')
        valid = t.validate(t.serialize())

        self.assertEqual(valid, False)
        self.assertEqual(len(t.errors), 1)  # Only one failure
        # Length failure, not *FIELD_REQUIRED*
        self.assertIn('first_name', t.errors)
        self.assertEqual(len(t.errors['first_name']), 1)

    def test_validation_none_string_length_pass(self):
        class TestDoc(Model):
            first_name = StringType(min_length=1)

        t = TestDoc()
        valid = t.validate({'first_name': ''})
        self.assertEqual(valid, False)
        valid = t.validate({'first_name': None})
        self.assertEqual(valid, True)



class TestCustomValidators(unittest.TestCase):

    def setUp(self):

        now = datetime.datetime(2012, 1, 1, 0, 0)
        self.future_error_msg = u'Future dates are not valid'

        def is_not_future(dt, *args):
            if dt > now:
                raise ValidationError, self.future_error_msg

        class TestDoc(Model):
            publish = DateTimeType(validators=[is_not_future])
            author = StringType(required=True)
            title = StringType(required=False)

        self.Doc = TestDoc

    def test_custom_validators(self):

        doc = self.Doc()
        valid = doc.validate({
            'publish': datetime.datetime(2012, 2, 1, 0, 0),
            'author': u'Hemingway',
            'title': u'Old Man',
        })

        self.assertIn(self.future_error_msg, doc.errors['publish'])


class TestErrors(unittest.TestCase):

    def setUp(self):

        class Person(Model):
            name = StringType(required=True)

        class Course(Model):
            id = StringType(required=True, validators=[])
            attending = ListType(ModelType(Person))
            prerequisit = ModelType("self")

        class School(Model):
            courses = ListType(ModelType(Course))

        self.Person = Person
        self.Course = Course
        self.School = School

        self.school = School()

    valid_data = {
        'courses': [
            {'id': 'ENG103', 'attending': [
                {'name': u'Danny'},
                {'name': u'Sandy'}],
             'prerequisit': None},
            {'id': 'ENG203', 'attending': [
                {'name': u'Danny'},
                {'name': u'Sandy'}],
             'prerequisit': {'id': 'ENG103'}}
        ]
    }

    def _test_deep_errors(self):

        valid = self.school.validate(self.valid_data)
        self.assertTrue(valid)
        course1, course2 = self.school.courses
        self.assertIsNone(course1.prerequisit)
        self.assertIsInstance(course2.prerequisit, self.Course)

        invalid_data = self.school.serialize()
        invalid_data['courses'][0]['attending'][0]['name'] = None
        valid = self.school.validate(invalid_data)
        self.assertFalse(valid)


if __name__ == '__main__':
    unittest.main()
