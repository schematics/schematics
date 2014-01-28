import pytest
import datetime

from schematics.models import Model
from schematics.exceptions import (
    BaseError, ValidationError, ConversionError,
    ModelValidationError, ModelConversionError,
)
from schematics.types import StringType, DateTimeType, BooleanType
from schematics.types.compound import ModelType, ListType, DictType


future_error_msg = u'Future dates are not valid'


def test_choices_validates():
    class Document(Model):
        language = StringType(choices=['en', 'de'])

    doc = Document({'language': 'de'})
    doc.validate()


def test_validation_fails():
    class Document(Model):
        language = StringType(choices=['en', 'de'])

    doc = Document({'language': 'fr'})
    with pytest.raises(ValidationError):
        doc.validate()


def test_choices_validates_with_embedded():
    class Document(Model):
        language = StringType(choices=['en', 'de'])
        other = ListType(StringType())

    doc = Document({
        'language': 'de',
        'other': ['somevalue', 'other']
    })

    doc.validate()


def test_validation_failes_with_embedded():
    class Document(Model):
        language = StringType(choices=['en', 'de'])
        other = ListType(StringType())

    doc = Document({
        'language': 'fr',
        'other': ['somevalue', 'other']
    })

    with pytest.raises(ValidationError):
        doc.validate()


def test_validation_none_fails():
    class Player(Model):
        first_name = StringType(required=True)

    with pytest.raises(ValidationError) as exception:
        Player({"first_name": None}).validate()

        assert len(exception.messages) == 1  # Only one failure
        assert u'This field is required' in exception.messages["first_name"][0]


def test_custom_validators():
    now = datetime.datetime(2012, 1, 1, 0, 0)

    def is_not_future(dt, *args):
        if dt > now:
            raise ValidationError(future_error_msg)

    class TestDoc(Model):
        publish = DateTimeType(validators=[is_not_future])
        author = StringType(required=True)
        title = StringType(required=False)

    with pytest.raises(ValidationError) as exception:
        TestDoc({
            "publish": datetime.datetime(2012, 2, 1, 0, 0),
            "author": "Hemingway",
            "title": "Old Man"
        }).validate()

        assert future_error_msg in exception.messages['publish']


def test_messages_subclassing():
    class MyStringType(StringType):
        MESSAGES = {'required': u'Never forget'}

    class TestDoc(Model):
        title = MyStringType(required=True)

    with pytest.raises(ValidationError) as exception:
        TestDoc({'title': None}).validate()

        assert u'Never forget' in exception.messages['title']


def test_messages_instance_level():
    class TestDoc(Model):
        title = StringType(required=True, messages={'required': u'Never forget'})

    with pytest.raises(ValidationError) as exception:
        TestDoc({'title': None}).validate()
        assert u'Never forget' in exception.messages['title']


def test_model_validators():
    now = datetime.datetime(2012, 1, 1, 0, 0)
    future = now + datetime.timedelta(1)

    assert future > now

    class TestDoc(Model):
        can_future = BooleanType()
        publish = DateTimeType()

        def validate_publish(self, data, dt):
            if dt > datetime.datetime(2012, 1, 1, 0, 0) and not data['can_future']:
                raise ValidationError(future_error_msg)

    with pytest.raises(ValidationError):
        TestDoc({'publish': future}).validate()


def test_multi_key_validation():
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

    with pytest.raises(ValidationError):
        GoodModel({'publish': input}).validate()

    GoodModel({'publish': input, 'should_raise': False}).validate()

    with pytest.raises(ValidationError):
        GoodModel({'publish': input, 'should_raise': True}).validate()


def test_multi_key_validation_part_two():
    class Signup(Model):
        name = StringType()
        call_me = BooleanType(default=False)

        def validate_call_me(self, data, value):
            if data['name'] == u'Brad' and value is True:
                raise ValidationError(u'I\'m sorry I never call people who\'s name is Brad')
            return value

    Signup({'name': u'Brad'}).validate()
    Signup({'name': u'Brad', 'call_me': False}).validate()

    with pytest.raises(ValidationError):
        Signup({'name': u'Brad', 'call_me': True}).validate()


def test_multi_key_validation_fields_order():
    class Signup(Model):
        name = StringType()
        call_me = BooleanType(default=False)

        def validate_name(self, data, value):
            if data['name'] == u'Brad':
                value = u'Joe'
                data['name'] = value
                return value
            return value

        def validate_call_me(self, data, value):
            if data['name'] == u'Joe':
                raise ValidationError(u"Don't try to decept me! You're Joe!")
            return value

    Signup({'name': u'Tom'}).validate()

    with pytest.raises(ValidationError):
        Signup({'name': u'Brad'}).validate()



def test_basic_error():
    class School(Model):
        name = StringType(required=True)

    school = School()

    with pytest.raises(ValidationError) as exception:
        school.validate()

        errors = exception.messages

        assert "name" in errors
        assert errors["name"] == ["This field is required."]


def test_deep_errors():
    class Person(Model):
        name = StringType(required=True)

    class School(Model):
        name = StringType(required=True)
        headmaster = ModelType(Person, required=True)

    school = School()
    school.name = "Hogwarts"
    school.headmaster = {}

    with pytest.raises(ValidationError) as exception:
        school.validate()

        errors = exception.messages

        assert "headmaster" in errors
        assert "name" in errors["headmaster"]
        assert errors["headmaster"]["name"] == ["This field is required."]


def test_deep_errors_with_lists():
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
    with pytest.raises(ValidationError) as exception:
        school.validate()

        messages = exception.messages

        assert messages == {
            'courses': [
                {
                    'attending': [
                        {
                            'name': [u'This field is required.'],
                        },
                    ],
                }
            ]
        }


def test_deep_errors_with_dicts():
    class Person(Model):
        name = StringType(required=True)

    class Course(Model):
        id = StringType(required=True, validators=[])
        attending = ListType(ModelType(Person))

    class School(Model):
        courses = DictType(ModelType(Course))

    valid_data = {
        'courses': {
            "ENG103": {
                'id': 'ENG103', 'attending': [
                    {'name': u'Danny'},
                    {'name': u'Sandy'},
                ],
            },
            "ENG203": {
                'id': 'ENG203', 'attending': [
                    {'name': u'Danny'},
                    {'name': u'Sandy'},
                ],
            },
        }
    }

    school = School(valid_data)
    school.validate()

    invalid_data = school.serialize()
    invalid_data['courses']["ENG103"]['attending'][0]['name'] = None

    school = School(invalid_data)
    with pytest.raises(ValidationError) as exception:
        school.validate()

        messages = exception.messages

        assert messages == {
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
        }


def test_clean_validation_messages():
    error = BaseError(["A"])
    assert error.messages == ["A"]


def test_clean_validation_messages_list():
    error = BaseError(["A", "B", "C"])
    assert error.messages, ["A", "B", "C"]


def test_clean_validation_messages_dict():
    error = BaseError({"A": "B"})
    assert error.messages == {"A": "B"}


def test_builtin_conversion_exception():
    with pytest.raises(TypeError):
        raise ConversionError('TypeError')

    with pytest.raises(TypeError):
        raise ModelConversionError('TypeError')


def test_builtin_validation_exception():
    with pytest.raises(ValueError):
        raise ValidationError('ValueError')

    with pytest.raises(ValueError):
        raise ModelValidationError('ValueError')
