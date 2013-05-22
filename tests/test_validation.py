#!/usr/bin/env python

import unittest
import datetime

from schematics.models import Model
from schematics.exceptions import (
    BaseError, ValidationError, ConversionError,
    ModelValidationError, ModelConversionError,
)
from schematics.types import StringType, DateTimeType, BooleanType
from schematics.types.compound import ModelType, ListType, DictType


class TestChoices(unittest.TestCase):

    def test_choices_validates(self):
        class Document(Model):
            language = StringType(choices=['en', 'de'])

        doc = Document({'language': 'de'})
        doc.validate()

    def test_validation_fails(self):
        class Document(Model):
            language = StringType(choices=['en', 'de'])

        doc = Document({'language': 'fr'})
        with self.assertRaises(ValidationError):
            doc.validate()

    def test_choices_validates_with_embedded(self):
        class Document(Model):
            language = StringType(choices=['en', 'de'])
            other = ListType(StringType())

        doc = Document({
            'language': 'de',
            'other': ['somevalue', 'other']
        })

        doc.validate()

    def test_validation_failes_with_embedded(self):
        class Document(Model):
            language = StringType(choices=['en', 'de'])
            other = ListType(StringType())

        doc = Document({
            'language': 'fr',
            'other': ['somevalue', 'other']
        })

        with self.assertRaises(ValidationError):
            doc.validate()


class TestRequired(unittest.TestCase):

    def test_validation_none_fails(self):
        class Player(Model):
            first_name = StringType(required=True)

        with self.assertRaises(ValidationError) as context:
            Player({"first_name": None}).validate()

        exception = context.exception

        self.assertEqual(len(exception.messages), 1)  # Only one failure
        self.assertIn(u'This field is required', exception.messages["first_name"][0])


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
            }).validate()

        exception = context.exception

        self.assertIn(future_error_msg, exception.messages['publish'])

    def test_messages_subclassing(self):
        class MyStringType(StringType):
            MESSAGES = {'required': u'Never forget'}

        class TestDoc(Model):
            title = MyStringType(required=True)

        with self.assertRaises(ValidationError) as context:
            TestDoc({'title': None}).validate()

        self.assertIn(u'Never forget', context.exception.messages['title'])

    def test_messages_instance_level(self):
        class TestDoc(Model):
            title = StringType(required=True, messages={'required': u'Never forget'})

        with self.assertRaises(ValidationError) as context:
            TestDoc({'title': None}).validate()
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
            TestDoc({'publish': future}).validate()

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
            GoodModel({'publish': input}).validate()

        GoodModel({'publish': input, 'should_raise': False}).validate()

        with self.assertRaises(ValidationError):
            GoodModel({'publish': input, 'should_raise': True}).validate()

    def test_multi_key_validation_part_two(self):
        class Signup(Model):
            name = StringType()
            call_me = BooleanType(default=False)

            def validate_call_me(self, data, value):
                if data['name'] == u'Brad' and value is True:
                    raise ValidationError(u'I\'m sorry I never call people who\'s name is Brad')
                return value

        Signup({'name': u'Brad'}).validate()
        Signup({'name': u'Brad', 'call_me': False}).validate()

        with self.assertRaises(ValidationError):
            Signup({'name': u'Brad', 'call_me': True}).validate()


class TestErrors(unittest.TestCase):

    def test_basic_error(self):
        class School(Model):
            name = StringType(required=True)

        school = School()

        with self.assertRaises(ValidationError) as context:
            school.validate()

        errors = context.exception.messages

        self.assertIn("name", errors)
        self.assertEqual(errors["name"], ["This field is required."])

    def test_deep_errors(self):
        class Person(Model):
            name = StringType(required=True)

        class School(Model):
            name = StringType(required=True)
            headmaster = ModelType(Person, required=True)

        school = School()
        school.name = "Hogwarts"
        school.headmaster = {}

        with self.assertRaises(ValidationError) as context:
            school.validate()

        errors = context.exception.messages

        self.assertIn("headmaster", errors)
        self.assertIn("name", errors["headmaster"])
        self.assertEqual(errors["headmaster"]["name"], ["This field is required."])

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

        school = School(valid_data)
        school.validate()

        invalid_data = school.serialize()
        invalid_data['courses'][0]['attending'][0]['name'] = None

        school = School(invalid_data)
        with self.assertRaises(ValidationError) as context:
            school.validate()

        exception = context.exception
        messages = exception.messages

        self.assertEqual(messages, {
            'courses': [
                {
                    'attending': [
                        {
                            'name': [u'This field is required.']
                        }
                    ]
                }
            ]
        })

    def test_deep_errors_with_dicts(self):
        class Person(Model):
            name = StringType(required=True)

        class Course(Model):
            id = StringType(required=True, validators=[])
            attending = ListType(ModelType(Person))

        class School(Model):
            courses = DictType(ModelType(Course))

        valid_data = {
            'courses': {
                "ENG103":
                    {'id': 'ENG103', 'attending': [
                        {'name': u'Danny'},
                        {'name': u'Sandy'}]},
                "ENG203":
                    {'id': 'ENG203', 'attending': [
                        {'name': u'Danny'},
                        {'name': u'Sandy'}
                    ]}
            }
        }

        school = School(valid_data)
        school.validate()

        invalid_data = school.serialize()
        invalid_data['courses']["ENG103"]['attending'][0]['name'] = None

        school = School(invalid_data)
        with self.assertRaises(ValidationError) as context:
            school.validate()

        exception = context.exception
        messages = exception.messages

        self.assertEqual(messages, {
            'courses': {
                "ENG103":
                {
                    'attending': [
                        {
                            'name': [u'This field is required.']
                        }
                    ]
                }
            }
        })


class TestValidationError(unittest.TestCase):

    def test_clean_validation_message(self):
        error = BaseError("A")

        self.assertEqual(error.messages, ["A"])

    def test_clean_validation_messages(self):
        error = BaseError(["A"])

        self.assertEqual(error.messages, ["A"])

    def test_clean_validation_messages_list(self):
        error = BaseError(["A", "B", "C"])

        self.assertEqual(error.messages, ["A", "B", "C"])

    def test_clean_validation_messages_dict(self):
        error = BaseError({"A": "B"})

        self.assertEqual(error.messages, {"A": "B"})


class TestBuiltinExceptions(unittest.TestCase):

    def test_builtin_conversion_exception(self):
        with self.assertRaises(TypeError):
            raise ConversionError('TypeError')
        with self.assertRaises(TypeError):
            raise ModelConversionError('TypeError')

    def test_builtin_validation_exception(self):
        with self.assertRaises(ValueError):
            raise ValidationError('ValueError')
        with self.assertRaises(ValueError):
            raise ModelValidationError('ValueError')
