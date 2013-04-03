#!/usr/bin/env python

import unittest
import datetime

from schematics.models import Model
from schematics.exceptions import ValidationError
from schematics.types import StringType, DateTimeType, BooleanType
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


future_error_msg = u'Future dates are not valid'


class TestCustomValidators(unittest.TestCase):

    def test_custom_validators(self):
        now = datetime.datetime(2012, 1, 1, 0, 0)

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

    def test_messages_subclassing(self):
        class MyStringType(StringType):
            MESSAGES = {'required': u'Never forget'}

        class TestDoc(Model):
            title = MyStringType(required=True)

        with self.assertRaises(ValidationError) as context:
            TestDoc({'title': None})
        self.assertIn(u'Never forget', context.exception.messages['title'])

    def test_messages_instance_level(self):
        class TestDoc(Model):
            title = StringType(required=True, messages={'required': u'Never forget'})

        with self.assertRaises(ValidationError) as context:
            TestDoc({'title': None})
        self.assertIn(u'Never forget', context.exception.messages['title'])


class TestModelLevelValidators(unittest.TestCase):

    def test_model_validators(self):
        now = datetime.datetime(2012, 1, 1, 0, 0)
        future = now + datetime.timedelta(1)

        self.assertGreater(future, now)

        class TestDoc(Model):
            can_future = BooleanType()
            publish = DateTimeType()

            def validate_publish(self, data, dt):
                if dt > datetime.datetime(2012, 1, 1, 0, 0) and not data['can_future']:
                    raise ValidationError(future_error_msg)

        with self.assertRaises(ValidationError):
            TestDoc().validate({'publish': future})

    def test_position_hint(self):
        now = datetime.datetime(2012, 1, 1, 0, 0)
        future = now + datetime.timedelta(1)

        input = str(future.isoformat())

        class BadModel(Model):
            publish = DateTimeType()
            can_future = BooleanType(default=False)

            def validate_publish(self, data, dt):
                data['can_future']

        with self.assertRaises(KeyError):
            BadModel({'publish': input})

    def test_multi_key_validation(self):
        now = datetime.datetime(2012, 1, 1, 0, 0)
        future = now + datetime.timedelta(1)

        input = str(future.isoformat())

        class GoodModel(Model):
            should_raise = BooleanType(default=True)
            publish = DateTimeType()

            def validate_publish(self, data, dt):
                if data['should_raise'] is True:
                    raise ValidationError(u'')
                return dt

        with self.assertRaises(ValidationError):
            GoodModel().validate({'publish': input})

        self.assertTrue(GoodModel().validate({'publish': input, 'should_raise': False}))

        with self.assertRaises(ValidationError):
            GoodModel().validate({'publish': input, 'should_raise': True})

    def test_multi_key_validation_part_two(self):
        class Signup(Model):
            name = StringType()
            call_me = BooleanType(default=False)

            def validate_call_me(self, data, value):
                if data['name'] == u'Brad' and value is True:
                    raise ValidationError(u'I\'m sorry I never call people who\'s name is Brad')
                return value

        assert Signup().validate({'name': u'Brad'}) is True
        assert Signup().validate({'name': u'Brad', 'call_me': False}, raises=False) is True
        assert Signup().validate({'name': u'Brad', 'call_me': True}, raises=False) is False


class TestErrors(unittest.TestCase):

    def test_basic_error(self):
        class School(Model):
            name = StringType(required=True)

        school = School()
        is_valid = school.validate({}, raises=False)

        self.assertFalse(is_valid)

        self.assertIn("name", school.errors)
        self.assertEqual(school.errors["name"], ["This field is required."])

    def test_deep_errors(self):
        class Person(Model):
            name = StringType(required=True)

        class School(Model):
            name = StringType(required=True)
            headmaster = ModelType(Person, required=True)

        school = School()
        is_valid = school.validate({
            "name": "Hogwarts",
            "headmaster": {}
        }, raises=False)

        self.assertFalse(is_valid)

        self.assertIn("headmaster", school.errors)
        self.assertIn("name", school.errors["headmaster"])
        self.assertEqual(school.errors["headmaster"]["name"], ["This field is required."])

    def test_deep_errors_with_lists(self):
        class Person(Model):
            name = StringType(required=True)

        class Course(Model):
            id = StringType(required=True, validators=[])
            attending = ListType(ModelType(Person))

        class School(Model):
            courses = ListType(ModelType(Course))

        valid_data = {
            'courses': [
                {'id': 'ENG103', 'attending': [
                    {'name': u'Danny'},
                    {'name': u'Sandy'}]},
                {'id': 'ENG203', 'attending': [
                    {'name': u'Danny'},
                    {'name': u'Sandy'}
                ]}
            ]
        }

        school = School()
        valid = school.validate(valid_data)
        self.assertTrue(valid)

        invalid_data = school.serialize()
        invalid_data['courses'][0]['attending'][0]['name'] = None

        valid = school.validate(invalid_data, raises=False)
        self.assertFalse(valid)

    def test_field_binding(self):
        class Person(Model):
            name = StringType(required=True)

        class Course(Model):
            id = StringType(required=True, validators=[])
            attending = ListType(ModelType(Person))

        class School(Model):
            courses = ListType(ModelType(Course))

        valid_data = {
            'courses': [
                {'id': 'ENG103', 'attending': [
                    {'name': u'Danny'},
                    {'name': u'Sandy'}]},
                {'id': 'ENG203', 'attending': [
                    {'name': u'Danny'},
                    {'name': u'Sandy'}
                ]}
            ]
        }

        new_school = School()
        new_school.validate(valid_data)

        school = School()
        school.validate(valid_data)

        self.assertNotEqual(id(new_school), id(school))

        self.assertNotEqual(
            id(new_school.courses[0].attending[0]),
            id(school.courses[0].attending[0])
        )


if __name__ == '__main__':
    unittest.main()
