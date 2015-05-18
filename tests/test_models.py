# -*- coding: utf-8 -*-
import pytest

from schematics.models import Model
from schematics.transforms import whitelist, blacklist
from schematics.models import ModelOptions

from schematics.types.base import StringType, IntType
from schematics.types.compound import ModelType
from schematics.exceptions import ValidationError, ConversionError, ModelConversionError

from six import PY3

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


def test_model_with_rogue_field_throws_exception():
    class User(Model):
        name = StringType()

    with pytest.raises(ModelConversionError):
        User({'foo': 'bar'})


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


def test_returns_partial_data_with_conversion_errors():
    class User(Model):
        name = StringType(required=True)
        age = IntType(required=True)
        account_level = IntType()

    with pytest.raises(ModelConversionError) as exception:
        User({"name": "Jóhann", "age": "100 years", "account_level": "3"})

    partial_data = exception.value.partial_data

    assert partial_data == {
        "name": u"Jóhann",
        "account_level": 3,
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
    assert mo is not None

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
    assert mo is not None


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


def test_model_deserialize_from_with_list():
    class User(Model):
        username = StringType(deserialize_from=['name', 'user'])

    assert User({'name': 'Ryan'}).username == 'Ryan'
    assert User({'user': 'Mike'}).username == 'Mike'
    assert User({'username': 'Mark'}).username == 'Mark'
    assert User({
        "username": "Mark",
        "name": "Second-class",
        "user": "key"
    }).username == 'Mark'


def test_model_deserialize_from_with_string():
    class User(Model):
        username = StringType(deserialize_from='name')

    assert User({'name': 'Mike'}).username == 'Mike'
    assert User({'username': 'Mark'}).username == 'Mark'
    assert User({'username': 'Mark', "name": "Second-class field"}).username == 'Mark'


def test_model_import_with_deserialize_mapping():
    class User(Model):
        username = StringType()

    mapping = {
        "username": ['name', 'user'],
    }

    assert User({'name': 'Ryan'}, deserialize_mapping=mapping).username == 'Ryan'
    assert User({'user': 'Mike'}, deserialize_mapping=mapping).username == 'Mike'
    assert User({'username': 'Mark'}, deserialize_mapping=mapping).username == 'Mark'
    assert User({'username': 'Mark', "name": "Second-class", "user": "key"},
                deserialize_mapping=mapping).username == 'Mark'


def test_model_import_data_with_mapping():
    class User(Model):
        username = StringType()

    mapping = {
        "username": ['name', 'user'],
    }

    user = User()
    user.import_data({'name': 'Ryan'}, mapping=mapping)
    assert user.username == 'Ryan'


def test_nested_model_import_data_with_mappings():
    class Nested(Model):
        nested_attr = StringType()

    class Root(Model):
        root_attr = StringType()
        nxt_level = ModelType(Nested)

    mapping = {
        'root_attr': ['attr'],
        'nxt_level': ['next'],
        'model_mapping': {
            'nxt_level': {
                'nested_attr': ['attr'],
            },
        },
    }

    root = Root()
    root.import_data({
        "attr": "root value",
        "next": {
            "attr": "nested value",
        },
    }, mapping=mapping)

    assert root.root_attr == 'root value'
    assert root.nxt_level.nested_attr == 'nested value'

    root = Root({
        "attr": "root value",
        "next": {
            "attr": "nested value",
        },
    }, deserialize_mapping=mapping)

    assert root.root_attr == 'root value'
    assert root.nxt_level.nested_attr == 'nested value'


def test_fielddescriptor_connectedness():
    class TestModel(Model):
        field1 = StringType()
        field2 = StringType()

    inst = TestModel()
    inst._data = {}
    with pytest.raises(AttributeError):
        inst.field1

    inst = TestModel()
    del inst._fields['field1']
    with pytest.raises(AttributeError):
        del inst.field1

    del inst.field2


def test_keys():
    class TestModel(Model):
        field1 = StringType()
        field2 = StringType()

    inst = TestModel({'field1': 'foo', 'field2': 'bar'})

    assert inst.keys() == ['field1', 'field2']


def test_values():
    class TestModel(Model):
        field1 = StringType()
        field2 = StringType()

    inst = TestModel({'field1': 'foo', 'field2': 'bar'})

    assert inst.values() == ['foo', 'bar']


def test_items():
    class TestModel(Model):
        field1 = StringType()
        field2 = StringType()

    inst = TestModel({'field1': 'foo', 'field2': 'bar'})

    assert inst.items() == [('field1', 'foo'), ('field2', 'bar')]


def test_get():
    class TestModel(Model):
        field1 = StringType()

    inst = TestModel({'field1': 'foo'})
    assert inst.get('field1') == 'foo'
    assert inst.get('foo') is None
    assert inst.get('foo', 'bar') == 'bar'


def test_setitem():
    class TestModel(Model):
        field1 = StringType()

    inst = TestModel()

    with pytest.raises(KeyError):
        inst['foo'] = 1

    inst['field1'] = 'foo'
    assert inst.field1 == 'foo'


def test_delitem():
    class TestModel(Model):
        field1 = StringType()

    inst = TestModel({'field1': 'foo'})

    with pytest.raises(KeyError):
        del inst['foo']

    del inst['field1']
    assert inst.field1 is None


def test_eq():
    class TestModel(Model):
        field1 = StringType()

    inst = TestModel({'field1': 'foo'})
    assert inst != 'foo'


def test_repr():
    class TestModel(Model):
        field1 = StringType()

    inst = TestModel({'field1': 'foo'})
    assert repr(inst) == '<TestModel: TestModel object>'

    if not PY3: #todo: make this work for PY3
        inst.__class__.__name__ = '\x80'
        assert repr(inst) == '<[Bad Unicode class name]: [Bad Unicode data]>'
