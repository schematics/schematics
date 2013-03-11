
import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.serializable import serializable
from schematics.types.compound import ModelType, DictType


class TestDictType(unittest.TestCase):

    def test_basic_type(self):
        class PlayerInfo(Model):
            categories = DictType(StringType)

        info = PlayerInfo(dict(categories={
            "math": "math",
            "batman": "batman"
        }))

        self.assertEqual(info.categories["math"], "math")

        d = info.serialize()
        self.assertEqual(d, {
            "categories": {
                "math": "math",
                "batman": "batman"
            }
        })

    def test_dict_type_with_model_type(self):
        class CategoryStats(Model):
            category_slug = StringType()
            total_wins = IntType()

        class PlayerInfo(Model):
            categories = DictType(ModelType(CategoryStats))
            #TODO: Maybe it would be cleaner to have
            #       DictType(CategoryStats) and implicitly convert to ModelType(CategoryStats)

        info = PlayerInfo(dict(categories={
            "math": {
                "category_slug": "math",
                "total_wins": 1
            },
            "batman": {
                "category_slug": "batman",
                "total_wins": 3
            }
        }))

        math_stats = CategoryStats({"category_slug": "math", "total_wins": 1})
        self.assertEqual(info.categories["math"], math_stats)

        d = info.serialize()
        self.assertEqual(d, {
            "categories": {
                "math": {
                    "category_slug": "math",
                    "total_wins": 1
                },
                "batman": {
                    "category_slug": "batman",
                    "total_wins": 3
                }
            }
        })

    def test_dict_type_with_model_type_init_with_instance(self):
        class ExperienceLevel(Model):
            level = IntType()

        class CategoryStats(Model):
            category_slug = StringType()
            total_wins = IntType()

            @serializable(type=ModelType(ExperienceLevel))
            def xp_level(self):
                return ExperienceLevel(dict(level=self.total_wins))

        class PlayerInfo(Model):
            id = IntType()
            categories = DictType(ModelType(CategoryStats))
            #TODO: Maybe it would be cleaner to have
            #       DictType(CategoryStats) and implicitly convert to ModelType(CategoryStats)

        math_stats = CategoryStats({
            "category_slug": "math",
            "total_wins": 1
        })

        info = PlayerInfo(dict(id=1, categories={
            "math": math_stats,
        }))

        self.assertEqual(info.categories["math"], math_stats)

        d = info.serialize()

        self.assertEqual(d, {
            "id": 1,
            "categories": {
                "math": {
                    "category_slug": "math",
                    "total_wins": 1,
                    "xp_level": {
                        "level": 1
                    }
                },
            }
        })

    def test_with_empty(self):
        class CategoryStatsInfo(Model):
            slug = StringType()

        class PlayerInfo(Model):
            categories = DictType(
                ModelType(CategoryStatsInfo),
                default=lambda: {}
            )

        info = PlayerInfo()

        self.assertEqual(info.categories, {})

        d = info.serialize()
        self.assertEqual(d, {
            "categories": {}
        })

    def test_key_type(self):
        def player_id(value):
            return long(value)

        class CategoryStatsInfo(Model):
            slug = StringType()

        class PlayerInfo(Model):
            categories = DictType(ModelType(CategoryStatsInfo), coerce_key=player_id)

        stats = CategoryStatsInfo({
            "slug": "math"
        })

        info = PlayerInfo({
            "categories": {"1": {"slug": "math"}}
        })

        self.assertEqual(info.categories, {1: stats})

        d = info.serialize()
        self.assertEqual(d, {
            "categories": {"1": {"slug": "math"}}
        })
