# encoding=utf-8

import unittest

from schematics.models import Model
from schematics.transforms import whitelist, blacklist
from schematics.models import ModelOptions

from schematics.types.base import StringType, IntType
from schematics.types.compound import ModelType
from schematics.exceptions import ValidationError, ConversionError, ModelConversionError


class TestModels(unittest.TestCase):
    def test_init_with_dict(self):
        class Player(Model):
            id = IntType()

        p1 = Player({"id": 4})
        self.assertEqual(p1.id, 4)

    def test_invalid_model_fail_validation(self):
        class Player(Model):
            name = StringType(required=True)

        p = Player()
        self.assertIsNone(p.name)

        with self.assertRaises(ValidationError):
            p.validate()

    def test_invalid_models_validate_partially(self):
        class User(Model):
            name = StringType(required=True)

        u = User()
        u.validate(partial=True)

    def test_equality(self):
        class Player(Model):
            id = IntType()

        p1 = Player({"id": 4})
        p2 = Player({"id": 4})

        self.assertEqual(p1, p2)

        p3 = Player({"id": 5})

        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)

    def test_dict_interface(self):
        class Player(Model):
            name = StringType()

        p = Player()
        p.name = u"Jóhann"

        self.assertIn("name", p)
        self.assertEqual(p['name'], u"Jóhann")
        self.assertNotIn('fake_key', p)

    def test_init_model_from_another_model(self):
        class User(Model):
            name = StringType(required=True)
            bio = StringType(required=True)

        u = User(dict(name="A", bio="Asshole"))

        u2 = User(u)
        self.assertEqual(u, u2)

    def test_raises_validation_error_on_non_partial_validate(self):
        class User(Model):
            name = StringType(required=True)
            bio = StringType(required=True)

        u = User(dict(name="Joe"))

        with self.assertRaises(ValidationError) as context:
            u.validate()

        self.assertEqual(context.exception.messages, {"bio": [u"This field is required."]})

    def test_model_inheritance(self):
        class Parent(Model):
            name = StringType(required=True)

        class Child(Parent):
            bio = StringType()

        input_data = {'bio': u'Genius', 'name': u'Joey'}

        model = Child(input_data)
        model.validate()

        self.assertEqual(model.serialize(), input_data)

        child = Child({"name": "Baby Jane", "bio": "Always behaves"})
        self.assertEqual(child.name, "Baby Jane")
        self.assertEqual(child.bio, "Always behaves")

    def test_validation_uses_internal_state(self):
        class User(Model):
            name = StringType(required=True)
            age = IntType(required=True)

        u = User({'name': u'Henry VIII'})
        u.age = 99
        u.validate()

        self.assertEqual(u.name, u'Henry VIII')
        self.assertEqual(u.age, 99)

    def test_validation_fails_if_internal_state_is_invalid(self):
        class User(Model):
            name = StringType(required=True)
            age = IntType(required=True)

        u = User()
        with self.assertRaises(ValidationError) as context:
            u.validate()

        exception = context.exception
        self.assertEqual(exception.messages, {
            "name": ["This field is required."],
            "age": ["This field is required."]
        })

        self.assertIsNone(u.name)
        self.assertIsNone(u.age)

    def test_returns_nice_conversion_errors(self):
        class User(Model):
            name = StringType(required=True)
            age = IntType(required=True)

        with self.assertRaises(ModelConversionError) as context:
            User({"name": "Jóhann", "age": "100 years"})

        errors = context.exception.messages

        self.assertEqual(errors, {
            "age": [u'Value is not int']
        })


class TestDefaultValues(unittest.TestCase):

    def test_field_default(self):
        class User(Model):
            name = StringType(default=u'Doggy')

        u = User()
        self.assertEqual(User.name.__class__, StringType)
        self.assertEqual(u.name, u'Doggy')

    def test_attribute_default_to_none_if_no_value(self):
        class User(Model):
            name = StringType()

        u = User()
        self.assertIsNone(u.name)

    def test_field_has_default_value(self):
        class Question(Model):
            question_id = StringType(required=True)

            type = StringType(default="text")

        q = Question(dict(question_id=1))

        self.assertEqual(q.type, "text")
        self.assertTrue("type" in q)
        self.assertEqual(q.get("type"), "text")

    def test_default_value_when_updating_model(self):
        class Question(Model):
            question_id = StringType(required=True)

            type = StringType(default="text")

        q = Question(dict(question_id=1, type="not default"))
        self.assertEqual(q.type, "not default")

        q.validate(dict(question_id=2))
        self.assertEqual(q.type, "not default")

    def test_explicit_values_override_defaults(self):
        class User(Model):
            name = StringType(default=u'Doggy')

        u = User({"name": "Voffi"})
        u.validate()
        self.assertEqual(u.name, u'Voffi')

        u = User()
        u.name = "Guffi"
        u.validate()

        self.assertEqual(u.name, "Guffi")


class TestModelOptions(unittest.TestCase):

    def test_good_options_args(self):
        mo = ModelOptions(klass=None, roles=None)
        self.assertNotEqual(mo, None)

        self.assertEqual(mo.roles, {})

    def test_bad_options_args(self):
        args = {
            'klass': None,
            'roles': None,
            'badkw': None,
        }

        with self.assertRaises(TypeError):
            ModelOptions(**args)

    def test_no_options_args(self):
        args = {}
        mo = ModelOptions(None, **args)
        self.assertNotEqual(mo, None)

    def test_options_parsing_from_model(self):
        class Foo(Model):
            class Options:
                namespace = 'foo'
                roles = {}

        f = Foo()
        fo = f._options

        self.assertEqual(fo.__class__, ModelOptions)
        self.assertEqual(fo.namespace, 'foo')
        self.assertEqual(fo.roles, {})

    def test_subclassing_preservers_roles(self):
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

        self.assertEqual(options.roles, {
            "public": blacklist("id")
        })

    def test_subclassing_overides_roles(self):
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

        self.assertEqual(options.roles, {
            "grandchildren": whitelist("age"),
            "public": blacklist("id", "family_secret"),
            "gender": blacklist("gender")
        })


class TestCompoundTypes(unittest.TestCase):

    def test_as_field_validate(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        c = Card({"user": {'name': u'Doggy'}})
        self.assertEqual(c.user.name, u'Doggy')

        with self.assertRaises(ConversionError):
            c.user = [1]
            c.validate()

        self.assertEqual(c.user.name, u'Doggy', u'Validation should not remove or modify existing data')

    def test_model_field_validate_structure(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        with self.assertRaises(ConversionError):
            Card({'user': [1, 2]})
