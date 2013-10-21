# -*- coding: utf-8 -*-
import pytest

from schematics.models import Model
from schematics.transforms import whitelist, blacklist
from schematics.models import ModelOptions

from schematics.types.base import StringType, IntType
from schematics.types.compound import ModelType
from schematics.exceptions import ValidationError, ConversionError, ModelConversionError


def test_init_with_dict():
    class Player(Model):
        id = IntType()

    p1 = Player({"id": 4})
    assert p1.id == 4


def test_invalid_model_fail_validation():
    class Player(Model):
        name = StringType(required=True)

    p = Player()
    assert p.name is None

    with pytest.raises(ValidationError):
        p.validate()


def test_invalid_models_validate_partially():
    class User(Model):
        name = StringType(required=True)

    u = User()
    u.validate(partial=True)


def test_equality():
    class Player(Model):
        id = IntType()

    p1 = Player({"id": 4})
    p2 = Player({"id": 4})

    assert p1 == p2

    p3 = Player({"id": 5})

    assert p1 == p2
    assert p1 != p3


def test_dict_interface():
    class Player(Model):
        name = StringType()

    p = Player()
    p.name = u"Jóhann"

    assert "name" in p
    assert p['name'] == u"Jóhann"
    assert 'fake_key'not in p


def test_init_model_from_another_model():
    class User(Model):
        name = StringType(required=True)
        bio = StringType(required=True)

    u = User(dict(name="A", bio="Asshole"))

    u2 = User(u)
    assert u == u2


def test_raises_validation_error_on_non_partial_validate():
    class User(Model):
        name = StringType(required=True)
        bio = StringType(required=True)

    u = User(dict(name="Joe"))

    with pytest.raises(ValidationError) as exception:
        u.validate()
        assert exception.messages, {"bio": [u"This field is required."]}


def test_model_inheritance():
    class Parent(Model):
        name = StringType(required=True)

    class Child(Parent):
        bio = StringType()

    input_data = {'bio': u'Genius', 'name': u'Joey'}

    model = Child(input_data)
    model.validate()

    assert model.serialize() == input_data

    child = Child({"name": "Baby Jane", "bio": "Always behaves"})
    assert child.name == "Baby Jane"
    assert child.bio == "Always behaves"


def test_validation_uses_internal_state():
    class User(Model):
        name = StringType(required=True)
        age = IntType(required=True)

    u = User({'name': u'Henry VIII'})
    u.age = 99
    u.validate()

    assert u.name == u'Henry VIII'
    assert u.age == 99


def test_validation_fails_if_internal_state_is_invalid():
    class User(Model):
        name = StringType(required=True)
        age = IntType(required=True)

    u = User()
    with pytest.raises(ValidationError) as exception:
        u.validate()

        assert exception.messages, {
            "name": ["This field is required."],
            "age": ["This field is required."],
        }

    assert u.name is None
    assert u.age is None


def test_returns_nice_conversion_errors():
    class User(Model):
        name = StringType(required=True)
        age = IntType(required=True)

    with pytest.raises(ModelConversionError) as exception:
        User({"name": "Jóhann", "age": "100 years"})

        errors = exception.messages

        assert errors == {
            "age": [u'Value is not int'],
        }


def test_field_default():
    class User(Model):
        name = StringType(default=u'Doggy')

    u = User()
    assert User.name.__class__ == StringType
    assert u.name == u'Doggy'


def test_attribute_default_to_none_if_no_value():
    class User(Model):
        name = StringType()

    u = User()
    assert u.name is None


def test_field_has_default_value():
    class Question(Model):
        question_id = StringType(required=True)

        type = StringType(default="text")

    q = Question(dict(question_id=1))

    assert q.type == "text"
    assert "type" in q
    assert q.get("type") == "text"


def test_default_value_when_updating_model():
    class Question(Model):
        question_id = StringType(required=True)

        type = StringType(default="text")

    q = Question(dict(question_id=1, type="not default"))
    assert q.type == "not default"

    q.validate(dict(question_id=2))
    assert q.type == "not default"


def test_explicit_values_override_defaults():
    class User(Model):
        name = StringType(default=u'Doggy')

    u = User({"name": "Voffi"})
    u.validate()
    assert u.name == u'Voffi'

    u = User()
    u.name = "Guffi"
    u.validate()

    assert u.name == "Guffi"


def test_good_options_args():
    mo = ModelOptions(klass=None, roles=None)
    assert mo != None

    assert mo.roles == {}


def test_bad_options_args():
    args = {
        'klass': None,
        'roles': None,
        'badkw': None,
    }

    with pytest.raises(TypeError):
        ModelOptions(**args)


def test_no_options_args():
    args = {}
    mo = ModelOptions(None, **args)
    assert mo != None


def test_options_parsing_from_model():
    class Foo(Model):
        class Options:
            namespace = 'foo'
            roles = {}

    f = Foo()
    fo = f._options

    assert fo.__class__ == ModelOptions
    assert fo.namespace == 'foo'
    assert fo.roles == {}


def test_options_parsing_from_optionsclass():
    class FooOptions(ModelOptions):
        def __init__(self, klass, **kwargs):
            kwargs['namespace'] = kwargs.get('namespace') or 'foo'
            kwargs['roles'] = kwargs.get('roles') or {}
            super(FooOptions, self).__init__(klass, **kwargs)

    class Foo(Model):
        __optionsclass__ = FooOptions

    f = Foo()
    fo = f._options

    assert fo.__class__ == FooOptions
    assert fo.namespace == 'foo'
    assert fo.roles == {}


def test_subclassing_preservers_roles():
    class Parent(Model):
        id = StringType()
        name = StringType()

        class Options:
            roles = {'public': blacklist("id")}

    class GrandParent(Parent):
        age = IntType()

    gramps = GrandParent({
        "id": "1",
        "name": "Edward",
        "age": 87
    })

    options = gramps._options

    assert options.roles == {
        "public": blacklist("id"),
    }


def test_subclassing_overides_roles():
    class Parent(Model):
        id = StringType()
        gender = StringType()
        name = StringType()

        class Options:
            roles = {
                'public': blacklist("id", "gender"),
                'gender': blacklist("gender")
            }

    class GrandParent(Parent):
        age = IntType()
        family_secret = StringType()

        class Options:
            roles = {
                'grandchildren': whitelist("age"),
                'public': blacklist("id", "family_secret")
            }

    gramps = GrandParent({
        "id": "1",
        "name": "Edward",
        "gender": "Male",
        "age": 87,
        "family_secret": "Secretly Canadian"
    })

    options = gramps._options

    assert options.roles == {
        "grandchildren": whitelist("age"),
        "public": blacklist("id", "family_secret"),
        "gender": blacklist("gender"),
    }


def test_as_field_validate():
    class User(Model):
        name = StringType()

    class Card(Model):
        user = ModelType(User)

    c = Card({"user": {'name': u'Doggy'}})
    assert c.user.name == u'Doggy'

    with pytest.raises(ConversionError):
        c.user = [1]
        c.validate()

    assert c.user.name == u'Doggy', u'Validation should not remove or modify existing data'


def test_model_field_validate_structure():
    class User(Model):
        name = StringType()

    class Card(Model):
        user = ModelType(User)

    with pytest.raises(ConversionError):
        Card({'user': [1, 2]})
