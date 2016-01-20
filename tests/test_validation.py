import pytest
import datetime

from schematics.models import Model
from schematics.exceptions import (
    ConversionError, ValidationError, StopValidationError, DataError)
from schematics.types import StringType, DateTimeType, BooleanType, IntType
from schematics.types.compound import ModelType, ListType, DictType
from schematics.validate import prepare_validator


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
    with pytest.raises(DataError):
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

    with pytest.raises(DataError):
        doc.validate()


def test_validation_none_fails():
    class Player(Model):
        first_name = StringType(required=True)

    with pytest.raises(DataError) as exception:
        Player({"first_name": None}).validate()

    messages = exception.value.messages
    assert len(messages) == 1  # Only one failure
    assert messages["first_name"][0] == 'This field is required.'


def test_custom_validators():
    now = datetime.datetime(2012, 1, 1, 0, 0)

    def is_not_future(dt, context=None):
        if dt > now:
            raise ValidationError(future_error_msg)

    def without_context(dt):
        pass

    class TestDoc(Model):
        publish = DateTimeType(validators=[is_not_future, without_context])
        author = StringType(required=True)
        title = StringType(required=False)

    with pytest.raises(DataError) as exception:
        TestDoc({
            "publish": datetime.datetime(2012, 2, 1, 0, 0),
            "author": "Hemingway",
            "title": "Old Man"
        }).validate()

    messages = exception.value.messages
    assert future_error_msg in messages['publish']


def test_messages_subclassing():
    class MyStringType(StringType):
        MESSAGES = {'required': u'Never forget'}

    class TestDoc(Model):
        title = MyStringType(required=True)

    with pytest.raises(DataError) as exception:
        TestDoc({'title': None}).validate()

    messages = exception.value.messages
    assert u'Never forget' in messages['title']


def test_messages_instance_level():
    class TestDoc(Model):
        title = StringType(required=True, messages={'required': u'Never forget'})

    with pytest.raises(DataError) as exception:
        TestDoc({'title': None}).validate()

    messages = exception.value.messages
    assert u'Never forget' in messages['title']


def test_model_validators():
    now = datetime.datetime(2012, 1, 1, 0, 0)
    future = now + datetime.timedelta(1)

    assert future > now

    class TestDoc(Model):
        can_future = BooleanType()
        publish = DateTimeType()
        foo = StringType()

        def validate_publish(self, data, dt, context):
            if dt > datetime.datetime(2012, 1, 1, 0, 0) and not data['can_future']:
                raise ValidationError(future_error_msg)

        def validate_foo(self, data, dt): # without context param
            pass

    TestDoc({'publish': now}).validate()

    with pytest.raises(DataError):
        TestDoc({'publish': future}).validate()


def test_validator_wrapper():
    def f(x, y):
        pass

    assert prepare_validator(f, 2) is f
    assert prepare_validator(f, 3) is not f


def test_nested_model_validators():

    class SubModel(Model):
        should_raise = BooleanType()

        def validate_should_raise(self, data, value, context):
            if value:
                raise ValidationError('message')

    class MainModel(Model):
        modelfield = ModelType(SubModel)

    with pytest.raises(DataError):
        MainModel({'modelfield': {'should_raise': True}}).validate()

    MainModel({'modelfield': {'should_raise': False}}).validate()


def test_multi_key_validation():
    now = datetime.datetime(2012, 1, 1, 0, 0)
    future = now + datetime.timedelta(1)

    input = str(future.isoformat())

    class GoodModel(Model):
        should_raise = BooleanType(default=True)
        publish = DateTimeType()

        def validate_publish(self, data, dt, context):
            if data['should_raise'] is True:
                raise ValidationError(u'')
            return dt

    with pytest.raises(DataError):
        GoodModel({'publish': input}).validate()

    GoodModel({'publish': input, 'should_raise': False}).validate()

    with pytest.raises(DataError):
        GoodModel({'publish': input, 'should_raise': True}).validate()


def test_multi_key_validation_part_two():
    class Signup(Model):
        name = StringType()
        call_me = BooleanType(default=False)

        def validate_call_me(self, data, value, context):
            if data['name'] == u'Brad' and value is True:
                raise ValidationError(u'I\'m sorry I never call people who\'s name is Brad')
            return value

    Signup({'name': u'Brad'}).validate()
    Signup({'name': u'Brad', 'call_me': False}).validate()

    with pytest.raises(DataError):
        Signup({'name': u'Brad', 'call_me': True}).validate()


def test_multi_key_validation_fields_order():
    class Signup(Model):
        name = StringType()
        call_me = BooleanType(default=False)

        def validate_name(self, data, value, context):
            if data['name'] == u'Brad':
                value = u'Joe'
                data['name'] = value
                return value
            return value

        def validate_call_me(self, data, value, context):
            if data['name'] == u'Joe':
                raise ValidationError(u"Don't try to decept me! You're Joe!")
            return value

    Signup({'name': u'Tom'}).validate()

    with pytest.raises(DataError):
        Signup({'name': u'Brad'}).validate()



def test_basic_error():
    class School(Model):
        name = StringType(required=True)

    school = School()

    with pytest.raises(DataError) as exception:
        school.validate()

    errors = exception.value.messages

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

    with pytest.raises(DataError) as exception:
        school.validate()

    errors = exception.value.messages

    assert "headmaster" in errors
    assert "name" in errors["headmaster"]
    assert errors["headmaster"]["name"] == ["This field is required."]


@pytest.mark.parametrize('idx1', (0, 1))
@pytest.mark.parametrize('idx2', (0, 1))
def test_deep_errors_with_lists(idx1, idx2):
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
    invalid_data['courses'][idx1]['attending'][idx2]['name'] = None

    school = School(invalid_data)
    with pytest.raises(DataError) as exception:
        school.validate()

    messages = exception.value.messages

    assert messages == {
        'courses': {
            idx1: {
                'attending': {
                    idx2: {
                        'name': [u'This field is required.'],
                    },
                },
            }
        }
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
    with pytest.raises(DataError) as exception:
        school.validate()

    messages = exception.value.messages

    assert messages == {
        'courses': {
            "ENG103": {
                'attending': {
                    0: {
                        'name': [u'This field is required.']
                    }
                }
            }
        }
    }


def test_field_validator_override():

    class CustomIntType(IntType):
        def validate_range(self, value, context=None):
            pass

    CustomIntType(max_value=1).validate(9)


def test_model_validator_override():

    class Base(Model):
        def validate_foo(self, data, value, context=None):
            pass
        def validate_bar(self, data, value, context=None):
            pass

    class Child(Base):
        def validate_bar(self, data, value, context=None):
            pass

    assert Child._validator_functions['foo'] is Base._validator_functions['foo']
    assert Child._validator_functions['bar'] is not Base._validator_functions['bar']


def test_validate_convert():

    class M(Model):
        field1 = IntType()

    m = M()
    m.field1 = "1"
    m.validate()
    assert m.field1 == 1

    m = M()
    m.field1 = "foo"
    m.validate(convert=False)
    assert m.field1 == "foo"


def test_validate_apply_defaults():

    class M(Model):
        field1 = StringType()
        field2 = StringType(default='foo')

    m = M({'field1': None}, init=False)

    m.validate()
    assert m.to_primitive() == {'field1': None}

    m.validate(apply_defaults=True)
    assert m.to_primitive() == {'field1': None, 'field2': 'foo'}


def test_clean_validation_messages():
    error = ValidationError("A")
    assert error.messages == ["A"]


def test_clean_validation_messages_list():
    error = ValidationError(["A", "B", "C"])
    assert error.messages, ["A", "B", "C"]


def test_builtin_conversion_exception():
    with pytest.raises(TypeError):
        raise ConversionError('message')


def test_builtin_validation_exception():
    with pytest.raises(ValueError):
        raise ValidationError('message')

