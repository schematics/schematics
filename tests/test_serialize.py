# -*- coding: utf-8 -*-
import pytest

from schematics.models import Model
from schematics.types import StringType, LongType, IntType, MD5Type
from schematics.types.compound import ModelType, DictType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import blacklist, whitelist, wholelist


def test_serializable():
    class Location(Model):
        country_code = StringType()

        @serializable
        def country_name(self):
            return "United States" if self.country_code == "US" else "Unknown"

    location_US = Location({"country_code": "US"})

    assert location_US.country_name == "United States"

    d = location_US.serialize()
    assert d == {"country_code": "US", "country_name": "United States"}

    location_IS = Location({"country_code": "IS"})

    assert location_IS.country_name == "Unknown"

    d = location_IS.serialize()
    assert d == {"country_code": "IS", "country_name": "Unknown"}


def test_serializable_with_serializable_name():
    class Location(Model):
        country_code = StringType(serialized_name="cc")

        @serializable(serialized_name="cn")
        def country_name(self):
            return "United States" if self.country_code == "US" else "Unknown"

    location_US = Location({"cc": "US"})

    assert location_US.country_name == "United States"

    d = location_US.serialize()
    assert d == {"cc": "US", "cn": "United States"}


def test_serializable_with_custom_serializable_class():
    class PlayerIdType(LongType):

        def to_primitive(self, value):
            return unicode(value)

    class Player(Model):
        id = LongType()

        @serializable(type=PlayerIdType())
        def player_id(self):
            return self.id

    player = Player({"id": 1})

    assert player.id == 1
    assert player.player_id == 1

    d = player.serialize()
    assert d == {"id": 1, "player_id": "1"}


def test_serializable_with_model():
    class ExperienceLevel(Model):
        level = IntType()
        title = StringType()

    class Player(Model):
        total_points = IntType()

        @serializable(type=ModelType(ExperienceLevel))
        def xp_level(self):
            return ExperienceLevel(dict(level=self.total_points * 2, title="Best"))

    player = Player({"total_points": 2})

    assert player.xp_level.level == 4

    d = player.serialize()
    assert d == {"total_points": 2, "xp_level": {"level": 4, "title": "Best"}}


def test_serializable_with_model_when_None():
    class ExperienceLevel(Model):
        level = IntType()
        title = StringType()

    class Player(Model):
        total_points = IntType()

        @serializable(type=ModelType(ExperienceLevel))
        def xp_level(self):
            return None if not self.total_points else ExperienceLevel()

    player = Player({"total_points": 0})

    assert player.xp_level is None

    d = player.serialize()
    assert d == {"total_points": 0, "xp_level": None}


def test_serializable_with_model_hide_None():
    class ExperienceLevel(Model):
        level = IntType()
        title = StringType()

    class Player(Model):
        total_points = IntType()

        @serializable(type=ModelType(ExperienceLevel), serialize_when_none=False)
        def xp_level(self):
            return None if not self.total_points else ExperienceLevel()

    player = Player({"total_points": 0})

    assert player.xp_level is None

    d = player.serialize()
    assert d == {"total_points": 0}


def test_serializable_with_embedded_models_and_list():
    class Question(Model):
        id = LongType()

    class QuestionPack(Model):
        id = LongType()
        questions = ListType(ModelType(Question))

    class Game(Model):
        id = StringType()
        question_pack = ModelType(QuestionPack)

    q1 = Question({"id": 1})
    q2 = Question({"id": 2})

    game = Game({
        "id": "1",
        "question_pack": {
            "id": 2,
            "questions": [q1, q2]
        }
    })

    assert game.question_pack.questions[0] == q1
    assert game.question_pack.questions[1] == q2

    d = game.serialize()

    assert d == {
        "id": "1",
        "question_pack": {
            "id": 2,
            "questions": [
                {
                    "id": 1,
                },
                {
                    "id": 2,
                },
            ]
        }
    }


def test_serializable_with_embedded_models():
    class ExperienceLevel(Model):
        level = IntType()
        stars = IntType()

        @classmethod
        def from_total_points(cls, total_points, category_slug):
            return cls(dict(level=total_points * 2, stars=total_points))

    class CategoryStatsInfo(Model):
        category_slug = StringType()
        total_points = IntType(default=0)

        @serializable(type=ModelType(ExperienceLevel))
        def xp_level(self):
            return ExperienceLevel.from_total_points(self.total_points, self.category_slug)

    class PlayerInfo(Model):
        id = LongType()
        display_name = StringType()

    class PlayerCategoryInfo(PlayerInfo):
        categories = DictType(ModelType(CategoryStatsInfo))

    info = PlayerCategoryInfo(dict(
        id="1",
        display_name="John Doe",
        categories={
            "math": {
                "category_slug": "math",
                "total_points": 1
            }
        }
    ))

    assert info.categories["math"].xp_level.level == 2
    assert info.categories["math"].xp_level.stars == 1

    d = info.serialize()
    assert d == {
        "id": 1,
        "display_name": "John Doe",
        "categories": {
            "math": {
                "category_slug": "math",
                "total_points": 1,
                "xp_level": {
                    "level": 2,
                    "stars": 1,
                }
            }
        }
    }


def test_serializable_works_with_inheritance():
    class Location(Model):
        country_code = StringType()

        @serializable
        def country_name(self):
            return "United States" if self.country_code == "US" else "Unknown"

    class LocationWithCity(Location):
        city_code = StringType()

        @serializable
        def city_name(self):
            return "Oklahoma" if self.city_code == "OK" else "Unknown"

    location = LocationWithCity(dict(country_code="US", city_code="OK"))

    assert location.country_code == "US"
    assert location.country_name == "United States"
    assert location.city_code == "OK"
    assert location.city_name == "Oklahoma"

    d = location.serialize()
    assert d == {
        "country_code": "US",
        "country_name": "United States",
        "city_code": "OK",
        "city_name": "Oklahoma",
    }


def test_serialize_with_complex_types():
    class QuestionResource(Model):
        url = StringType()

    class Question(Model):
        question_id = StringType(required=True)
        resources = DictType(ListType(ModelType(QuestionResource)))

    q = Question(dict(
        question_id="1",
        resources={
            "pictures": [{
                "url": "http://www.mbl.is",
            }]
        }
    ))

    d = q.serialize()
    assert d == dict(
        question_id="1",
        resources={
            "pictures": [{
                "url": "http://www.mbl.is",
            }]
        }
    )

    q_with_no_resources = Question(dict(
        question_id="1"
    ))

    d = q_with_no_resources.serialize()
    assert d == dict(
        question_id="1",
        resources=None,
    )


def test_field_with_serialize_when_none():
    class Question(Model):
        id = StringType()
        question = StringType()
        resources = DictType(StringType, serialize_when_none=False)

    q = Question(dict(id=1, question="Who's the man?"))

    d = q.serialize()
    assert d == {
        "id": "1",
        "question": "Who's the man?",
    }

    q = Question(dict(id=1, question="Who's the man?", resources={"A": "B"}))

    d = q.serialize()
    assert d == {
        "id": "1",
        "question": "Who's the man?",
        "resources": {"A": "B"}
    }


def test_set_serialize_when_none_on_whole_model():
    class Question(Model):
        id = StringType(required=True)
        question = StringType()
        resources = DictType(StringType)

        class Options:
            serialize_when_none = False

    q = Question(dict(id=1))

    d = q.serialize()
    assert d == {"id": "1"}


def test_possible_to_override_model_wide_serialize_when_none():
    class Question(Model):
        id = StringType(required=True)
        question = StringType()
        resources = DictType(StringType)

        class Options:
            serialize_when_none = False

    class StrictQuestion(Question):
        strictness = IntType()

        class Options:
            serialize_when_none = True

    q = StrictQuestion(dict(id=1))

    d = q.serialize()
    assert d == {"id": "1", "question": None, "resources": None, "strictness": None}


def test_possible_to_override_model_wide_settings_per_field():
    class Question(Model):
        id = StringType(required=True)
        question = StringType()
        resources = DictType(StringType, serialize_when_none=True)

        class Options:
            serialize_when_none = False

    q = Question(dict(id=1))

    d = q.serialize()
    assert d == {"id": "1", "resources": None}


def test_complex_types_hiding_after_apply_role_leaves_it_empty():
    class QuestionResource(Model):
        name = StringType()
        url = StringType()

        class Options:
            serialize_when_none = False
            roles = {'public': whitelist('name')}

    class Question(Model):
        question_id = StringType(required=True)
        resources = DictType(ListType(ModelType(QuestionResource)))

        class Options:
            serialize_when_none = False
            roles = {'public': whitelist('question_id', 'resources')}

    q = Question(dict(
        question_id="1",
        resources={
            "pictures": [{
                "url": "http://www.mbl.is",
            }]
        }
    ))

    d = q.serialize('public')
    assert d == {'question_id': '1'}


def test_roles_work_with_subclassing():
    class Address(Model):
        private_key = StringType()
        city = StringType()

        class Options:
            roles = {'public': blacklist('private_key')}

    class AddressWithPostalCode(Address):
        postal_code = IntType()

    a = AddressWithPostalCode(dict(
        postal_code=101,
        city=u"Reykjavík",
        private_key="secret"
    ))

    d = a.serialize(role="public")
    assert d == {
        "city": u"Reykjavík",
        "postal_code": 101,
    }


def test_role_propagate():
    class Address(Model):
        city = StringType()

        class Options:
            roles = {'public': whitelist('city')}

    class User(Model):
        name = StringType(required=True)
        password = StringType()
        addresses = ListType(ModelType(Address))

        class Options:
            roles = {'public': whitelist('name')}

    model = User({'name': 'a', 'addresses': [{'city': 'gotham'}]})
    assert model.addresses[0].city == 'gotham'

    d = model.serialize(role="public")
    assert d == {
        "name": "a",
    }


def test_fails_if_role_is_not_found():
    class Player(Model):
        id = StringType()

    p = Player(dict(id="1"))

    with pytest.raises(ValueError):
        p.serialize(role="public")


def test_doesnt_fail_if_role_isnt_found_on_embedded_models():
    class ExperienceLevel(Model):
        level = IntType()
        title = StringType()

        class Options:
            roles = {
                "public": wholelist(),
            }

    class Player(Model):
        id = StringType()
        secret = StringType()

        xp_level = ModelType(ExperienceLevel)

        class Options:
            roles = {
                "public": blacklist("secret")
            }

    p = Player(dict(
        id="1",
        secret="super_secret",
        xp_level={
            "level": 1,
            "title": "Starter"
        }
    ))

    d = p.serialize(role="public")
    assert d == {
        "id": "1",
        "xp_level": {
            "level": 1,
            "title": "Starter",
        }
    }


def test_doesnt_fail_serialize_when_none_on_whole_model_with_roles():
    class Question(Model):
        id = StringType(required=True)
        question = StringType()
        resources = DictType(StringType)

        class Options:
            serialize_when_none = False
            roles = {
                "public": whitelist("id"),
            }

    q = Question({"id": "1"})

    d = q.serialize(role="public")
    assert d == {"id": "1"}


def test_uses_roles_on_embedded_models_if_found():
    class ExperienceLevel(Model):
        level = IntType()
        title = StringType()

        class Options:
            roles = {
                "public": blacklist("title")
            }

    class Player(Model):
        id = StringType()
        secret = StringType()

        xp_level = ModelType(ExperienceLevel)

        class Options:
            roles = {
                "public": blacklist("secret")
            }

    p = Player(dict(
        id="1",
        secret="super_secret",
        xp_level={
            "level": 1,
            "title": "Starter"
        }
    ))

    d = p.serialize(role="public")
    assert d == {
        "id": "1",
        "xp_level": {
            "level": 1,
        }
    }


def test_serializable_with_dict_and_roles():
    class Player(Model):
        id = LongType()
        display_name = StringType()

        class Options:
            roles = {
                "public": blacklist("id")
            }

    class Game(Model):
        id = StringType()
        result = IntType()
        players = DictType(ModelType(Player), coerce_key=lambda k: long(k))

        class Options:
            roles = {
                "public": blacklist("result")
            }

    p1 = Player({"id": 1L, "display_name": "A"})
    p2 = Player({"id": 2L, "display_name": "B"})

    game = Game({
        "id": "1",
        "players": {
            1: p1,
            2: p2
        }
    })

    assert game.players[1] == p1
    assert game.players[2] == p2

    d = game.serialize(role="public")

    assert d == {
        "id": "1",
        "players": {
            1L: {
                "display_name": "A"
            },
            2L: {
                "display_name": "B"
            },
        }
    }


def test_serializable_with_list_and_roles():
    class Player(Model):
        id = LongType()
        display_name = StringType()

        class Options:
            roles = {
                "public": blacklist("id")
            }

    class Game(Model):
        id = StringType()
        result = IntType()
        players = ListType(ModelType(Player))

        class Options:
            roles = {
                "public": blacklist("result")
            }

    p1 = Player({"id": 1, "display_name": "A"})
    p2 = Player({"id": 2, "display_name": "B"})

    game = Game({
        "id": "1",
        "players": [p1, p2]
    })

    assert game.players[0] == p1
    assert game.players[1] == p2

    d = game.serialize(role="public")

    assert d == {
        "id": "1",
        "players": [
            {
                "display_name": "A",
            },
            {
                "display_name": "B",
            },
        ]
    }


def test_role_set_operations():

    protected = whitelist('email', 'password')
    all_fields = whitelist('id', 'name') + protected

    def count(n):
        while True:
            yield n
            n += 1

    class User(Model):
        id = IntType(default=count(42).next)
        name = StringType()
        email = StringType()
        password = StringType()

        class Options:
            roles = {
                'create': all_fields - ['id'],
                'public': all_fields - ['password'],
                'nospam': blacklist('password') + blacklist('email'),
            }

    data = {
        'id': 'NaN',
        'name': 'Arthur',
        'email': 'adent@hitchhiker.gal',
        'password': 'dolphins',
    }

    user = User(
        dict(
            (k, v) for k, v in data.iteritems()
            if k in User._options.roles['create']  # filter by 'create' role
        )
    )

    d = user.serialize(role='public')

    assert d == {
        'id': 42,
        'name': 'Arthur',
        'email': 'adent@hitchhiker.gal',
    }

    d = user.serialize(role='nospam')

    assert d == {
        'id': 42,
        'name': 'Arthur',
    }

    def test_md5_type(self):
        class M(Model):
            md5 = MD5Type()

        import hashlib
        myhash = hashlib.md5("hashthis").hexdigest()
        m = M()
        m.md5 = myhash

        self.assertEqual(m.md5, myhash)
        d = m.serialize()
        self.assertEqual(d, {
            'md5': myhash
        })
        
        m2 = M(d)
        self.assertEqual(m2.md5, myhash)

def test_serializable_with_list_and_default_role():
    class Player(Model):
        id = LongType()
        display_name = StringType()

        class Options:
            roles = {
                "default": blacklist("id")
            }

    class Game(Model):
        id = StringType()
        result = IntType()
        players = ListType(ModelType(Player))

        class Options:
            roles = {
                "default": blacklist("result")
            }

    p1 = Player({"id": 1, "display_name": "A"})
    p2 = Player({"id": 2, "display_name": "B"})

    game = Game({
        "id": "1",
        "players": [p1, p2]
    })

    assert game.players[0] == p1
    assert game.players[1] == p2

    d = game.serialize(role="default")

    assert d == {
        "id": "1",
        "players": [
            {
                "display_name": "A",
            },
            {
                "display_name": "B",
            },
        ]
    }

    d = game.serialize()

    assert d == {
        "id": "1",
        "players": [
            {
                "display_name": "A",
            },
            {
                "display_name": "B",
            },
        ]
    }
