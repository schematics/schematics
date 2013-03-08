
import unittest

from schematics.models import Model
from schematics.types import StringType, LongType, IntType
from schematics.types.serializable import serializable, Serializable


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
        class ToUnicodeSerializable(Serializable):

            def to_primitive(self, value):
                return unicode(value)

        class Player(Model):
            id = LongType()

            @serializable(serialized_class=ToUnicodeSerializable)
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

            @serializable
            def xp_level(self):
                return ExperienceLevel(dict(level=self.total_points * 2, title="Best"))

        player = Player({"total_points": 2})

        self.assertEqual(player.xp_level.level, 4)

        d = player.serialize()
        self.assertEqual(d, {"total_points": 2, "xp_level": {"level": 4, "title": "Best"}})
