
import unittest

from schematics.models import Model
from schematics.types import StringType, LongType, IntType
from schematics.types.compound import ModelType, DictType
from schematics.types.serializable import serializable
from schematics.serialize import blacklist


class TestSerializable(unittest.TestCase):

    def test_serializable(self):
        class Location(Model):
            country_code = StringType()

            @serializable
            def country_name(self):
                return "United States" if self.country_code == "US" else "Unknown"

        location_US = Location({"country_code": "US"})

        self.assertEqual(location_US.country_name, "United States")

        d = location_US.serialize()
        self.assertEqual(d, {"country_code": "US", "country_name": "United States"})

        location_IS = Location({"country_code": "IS"})

        self.assertEqual(location_IS.country_name, "Unknown")

        d = location_IS.serialize()
        self.assertEqual(d, {"country_code": "IS", "country_name": "Unknown"})

    def test_serializable_doesnt_keep_global_state(self):
        class Location(Model):
            country_code = StringType()

            @serializable
            def country_name(self):
                return "United States" if self.country_code == "US" else "Unknown"

        location_US = Location({"country_code": "US"})
        location_IS = Location({"country_code": "IS"})

        self.assertNotEqual(
            id(location_US._serializables["country_name"]),
            id(location_IS._serializables["country_name"])
        )

    def test_serializable_with_serializable_name(self):
        class Location(Model):
            country_code = StringType(serialized_name="cc")

            @serializable(serialized_name="cn")
            def country_name(self):
                return "United States" if self.country_code == "US" else "Unknown"

        location_US = Location({"cc": "US"})

        self.assertEqual(location_US.country_name, "United States")

        d = location_US.serialize()
        self.assertEqual(d, {"cc": "US", "cn": "United States"})

    def test_serializable_with_custom_serializable_class(self):
        class PlayerIdType(LongType):

            def to_primitive(self, value):
                return unicode(value)

        class Player(Model):
            id = LongType()

            @serializable(type=PlayerIdType())
            def player_id(self):
                return self.id

        player = Player({"id": 1})

        self.assertEqual(player.id, 1)
        self.assertEqual(player.player_id, 1)

        d = player.serialize()
        self.assertEqual(d, {"id": 1, "player_id": "1"})

    def test_serializable_with_model(self):
        class ExperienceLevel(Model):
            level = IntType()
            title = StringType()

        class Player(Model):
            total_points = IntType()

            @serializable(type=ModelType(ExperienceLevel))
            def xp_level(self):
                return ExperienceLevel(dict(level=self.total_points * 2, title="Best"))

        player = Player({"total_points": 2})

        self.assertEqual(player.xp_level.level, 4)

        d = player.serialize()
        self.assertEqual(d, {"total_points": 2, "xp_level": {"level": 4, "title": "Best"}})

    def test_serializable_with_dict(self):
        class Player(Model):
            id = LongType()
            display_name = StringType()

        class Game(Model):
            id = StringType()
            all_players = DictType(ModelType(Player), coerce_key=lambda k: long(k))

            class Options:
                roles = {
                    "public": blacklist("all_players")
                }

            @serializable(type=DictType(ModelType(Player), coerce_key=lambda k: long(k)))
            def players(self):
                return dict((pid, p) for pid, p in self.all_players.iteritems())

        p1 = Player({"id": 1, "display_name": "A"})
        p2 = Player({"id": 2, "display_name": "B"})

        game = Game({
            "id": "1",
            "all_players": {
                1: p1,
                2: p2
            }
        })

        self.assertEqual(game.all_players[1], p1)
        self.assertEqual(game.all_players[2], p2)

        d = game.serialize(role="public")
        print d
        self.assertEqual(d, {
            "id": "1",
            "players": {
                "1": {
                    "id": 1,
                    "display_name": "A"
                },
                "2": {
                    "id": 2,
                    "display_name": "B"
                },
            }
        })


class TestRoles(unittest.TestCase):

    def test_fails_if_role_is_not_found(self):
        class Player(Model):
            id = StringType()

        p = Player(dict(id="1"))

        with self.assertRaises(ValueError):
            p.serialize(role="public")

    def test_doesnt_fail_if_role_isnt_found_on_embedded_models(self):
        class ExperienceLevel(Model):
            level = IntType()
            title = StringType()

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
        self.assertEqual(d, {
            "id": "1",
            "xp_level": {
                "level": 1,
                "title": "Starter"
            }
        })
