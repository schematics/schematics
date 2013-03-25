import copy
import unittest
import datetime

from schematics.models import Model
from schematics.serialize import whitelist, blacklist
from schematics.models import ModelOptions

from schematics.types.base import StringType, IntType, DateTimeType
from schematics.types.compound import ListType, ModelType
from schematics.exceptions import ValidationError


class TestModels(unittest.TestCase):
    def test_equality(self):
        class Player(Model):
            id = IntType()

        p1 = Player({"id": 4})
        self.assertEqual(p1, copy.copy(p1))

        p2 = Player({"id": 4})
        self.assertEqual(p1, p2)

        p3 = Player({"id": 5})

        self.assertTrue(p1 == p2)
        self.assertTrue(p1 != p3)

    def test_equality_with_embedded_models(self):
        class Location(Model):
            country_code = StringType()

        class Player(Model):
            id = IntType()
            location = ModelType(Location)

        p1 = Player(dict(id=1, location={"country_code": "US"}))
        p2 = Player(dict(id=1, location={"country_code": "US"}))

        self.assertTrue(p1.location == p2.location)
        self.assertFalse(p1.location != p2.location)
        self.assertEqual(p1.location, p2.location)

        self.assertTrue(p1 == p2)
        self.assertEqual(p1, p2)

    def test_model_field_list(self):
        it = IntType()

        class TestModel(Model):
            some_int = it

        self.assertEqual({'some_int': it}, TestModel.fields)

    def test_model_data(self):
        class TestModel(Model):
            some_int = IntType()

        self.assertRaises(AttributeError, lambda: TestModel.data)

    def test_instance_data(self):
        class TestModel(Model):
            some_int = IntType()

        tm = TestModel()
        tm.some_int = 5

        self.assertEqual({'some_int': 5}, tm._data)

    def test_dict_interface(self):
        class TestModel(Model):
            some_int = IntType()

        tm = TestModel()
        tm.some_int = 5

        self.assertEqual(True, 'some_int' in tm)
        self.assertEqual(5, tm['some_int'])
        self.assertEqual(True, 'fake_key' not in tm)


class TestDefaultValues(unittest.TestCase):
    def test_default_value(self):
        class Question(Model):
            question_id = StringType(required=True)

            type = StringType(default="text")

        q = Question(dict(question_id=1))

        self.assertEqual(q.type, "text")

    def test_default_value_when_embedded_model(self):
        class Question(Model):
            question_id = StringType(required=True)

            type = StringType(default="text")

        class QuestionPack(Model):

            question = ModelType(Question)

        pack = QuestionPack({
            "question": {
                "question_id": 1
            }
        })

        self.assertEqual(pack.question.question_id, "1")
        self.assertEqual(pack.question.type, "text")


class TestOptions(unittest.TestCase):
    """This test collection covers the `ModelOptions` class and related
    functions.
    """

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


class TestModelInterface(unittest.TestCase):

    def test_init_model_from_another_model(self):
        class User(Model):
            name = StringType(required=True)
            bio = StringType(required=True)

        u = User(dict(name="A", bio="Asshole"))

        u2 = User(u)
        self.assertEqual(u, u2)

    def test_raises_validation_error_on_init(self):
        class User(Model):
            name = StringType(required=True)
            bio = StringType(required=True)

        with self.assertRaises(ValidationError):
            User(dict(name="Joe"), partial=False)

        with self.assertRaises(ValidationError):
            User({'name': u'Jimi Hendrix'}).validate()

    def test_model_inheritance(self):
        class Parent(Model):
            name = StringType(required=True)

        class Child(Parent):
            bio = StringType()

        input_data = {'bio': u'Genius', 'name': u'Joey'}

        model = Child({
            "name": "Joey"
        })
        self.assertEqual(model.validate(input_data), True)
        self.assertEqual(model.serialize(), input_data)

        child = Child({"name": "Baby Jane", "bio": "Always behaves"})
        self.assertEqual(child.name, "Baby Jane")
        self.assertEqual(child.bio, "Always behaves")

    def test_validate_input_partial(self):
        class TestModel(Model):
            name = StringType(required=True)
            bio = StringType()

        model = TestModel({'bio': 'Genius'}, partial=True)

        self.assertIsNone(model.name)
        self.assertEqual(model.bio, 'Genius')


class TestCompoundTypes(unittest.TestCase):
    """
    """

    def test_init(self):
        class User(Model):
            pass

        User()

    def test_field_default(self):
        class User(Model):
            name = StringType(default=u'Doggy')

        u = User()
        self.assertEqual(User.name.__class__, StringType)
        self.assertEqual(u.name, u'Doggy')

    def test_model_type(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        c = Card({"user": {'name': u'Doggy'}})
        self.assertIsInstance(c.user, User)
        self.assertEqual(c.user.name, "Doggy")

    def test_as_field_validate(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        c = Card({"user": {'name': u'Doggy'}})
        self.assertEqual(c.user.name, u'Doggy')
        self.assertEqual(c.validate(dict(user=[1]), raises=False), False)
        self.assertEqual(c.user.name, u'Doggy', u'Validation should not remove or modify existing data')

        c = Card()
        self.assertEqual(c.validate(dict(user=[1]), raises=False), False)
        self.assertRaises(AttributeError, lambda: c.user.name)

    def test_validation_uses_internal_state(self):
        class User(Model):
            name = StringType(required=True)
            age = IntType(required=True)
        u = User({'name': u'Henry VIII'})
        self.assertEqual(u.validate({'age': 99}, raises=False), True, u'Calling `validate` did not take internal state into account')

    def test_model_field_validate_structure(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        with self.assertRaises(ValidationError):
            Card({'user': [1, 2]})

    def test_list_field(self):
        class User(Model):
            ids = ListType(StringType, required=True)

        c = User({
            "ids": []
        })
        self.assertEqual(c.validate({'ids': []}), True)

    def test_list_field_required(self):
        class User(Model):
            ids = ListType(StringType(required=True))

        c = User({
            "ids": []
        })

        self.assertEqual(c.validate({'ids': [1]}), True)
        self.assertEqual(c.validate({'ids': [None]}, raises=False), False)
        self.assertIsInstance(c.errors, dict)

    def test_list_field_convert(self):
        class User(Model):
            ids = ListType(IntType)
            date = DateTimeType()

        c = User({'ids': ["1", "2"]})

        self.assertEqual(c.ids, [1, 2])
        now = datetime.datetime.now()

        self.assertEqual(c.validate({'date': now.isoformat()}), True)
        self.assertEqual(c.date, now)

    def test_list_model_field(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            users = ListType(ModelType(User), min_size=1)

        data = {'users': [{'name': u'Doggy'}]}
        c = Card(data)

        valid = c.validate({'users': None}, raises=False)
        self.assertFalse(valid)
        self.assertEqual(c.errors['users'], [u'This field is required.'])
        self.assertEqual(c.users[0].name, u'Doggy')
