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

        self.TestDoc = TestDoc

    def test_choices_validates(self):
        data_simple_valid = {'language': 'de'}
        doc = self.TestDoc(data_simple_valid)

        valid = doc.validate(data_simple_valid)
        self.assertEqual(valid, True)

    def test_validation_fails(self):
        data_simple_invalid = {'language': 'fr'}

        with self.assertRaises(ValidationError):
            self.TestDoc(data_simple_invalid)

    def test_choices_validates_with_embedded(self):
        data_embedded_valid = {
            'language': 'de',
            'other': {
                'info': ['somevalue', 'other']
            }
        }

        doc = self.TestDoc(data_embedded_valid)

        valid = doc.validate(data_embedded_valid)
        self.assertEqual(valid, True)

    def test_validation_failes_with_embedded(self):
        data_embedded_invalid = {
            'language': 'fr',
            'other': {
                'info': ['somevalue', 'other']
            }
        }

        with self.assertRaises(ValidationError):
            self.TestDoc(data_embedded_invalid)


class TestRequired(unittest.TestCase):

    def test_non_partial_init_fails(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        with self.assertRaises(ValidationError) as context:
            TestDoc(partial=False)

        exception = context.exception

        self.assertEqual(len(exception.messages), 1)  # Only one failure
        self.assertIn(u'This field is required', exception.messages["first_name"][0])

    def test_validation_none_fails(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        with self.assertRaises(ValidationError) as context:
            TestDoc().validate({"first_name": None})

        exception = context.exception

        self.assertNotEqual(exception.messages, {})
        self.assertEqual(len(exception.messages), 1)  # Only one failure
        self.assertIn(u'This field is required', exception.messages["first_name"][0])

    def test_validation_empty_string_not_pass(self):
        class TestDoc(Model):
            first_name = StringType(required=True)

        with self.assertRaises(ValidationError):
            TestDoc().validate({"first_name": ''})

    def test_validation_empty_string_length_fail(self):
        class TestDoc(Model):
            first_name = StringType(required=True, min_length=2)

        with self.assertRaises(ValidationError) as context:
            TestDoc().validate({"first_name": "A"})

        exception = context.exception

        self.assertEqual(len(exception.messages), 1)  # Only one failure
        # Length failure, not *FIELD_REQUIRED*
        self.assertIn('first_name', exception.messages)
        self.assertEqual(len(exception.messages['first_name']), 1)

    def test_validation_none_string_length_pass(self):
        class TestDoc(Model):
            first_name = StringType(min_length=1)

        t = TestDoc()
        valid = t.validate({'first_name': None})
        self.assertEqual(valid, True)


class TestCustomValidators(unittest.TestCase):

    def test_custom_validators(self):
        now = datetime.datetime(2012, 1, 1, 0, 0)
        future_error_msg = u'Future dates are not valid'

        def is_not_future(dt, *args):
            if dt > now:
                raise ValidationError(future_error_msg)

        class TestDoc(Model):
            publish = DateTimeType(validators=[is_not_future])
            author = StringType(required=True)
            title = StringType(required=False)

        with self.assertRaises(ValidationError) as context:
            TestDoc({
                "publish": datetime.datetime(2012, 2, 1, 0, 0),
                "author": "Hemingway",
                "title": "Old Man"
            })

        exception = context.exception

        self.assertIn(future_error_msg, exception.messages['publish'])


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
