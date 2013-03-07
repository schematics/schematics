
import unittest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, DictType
from schematics.serialize import wholelist
from schematics.exceptions import ValidationError


class TestDictType(unittest.TestCase):

    def test_basic_type(self):
        class PlayerInfo(Model):
            categories = DictType(StringType)

        info = PlayerInfo(categories={
            "math": "math"
        })

        self.assertEqual(info.categories["math"], "math")

        d = info.serialize()
        self.assertEqual(d, {
            "categories": {
                "math": "math"
            }
        })

    # def test(self):
    #     class CategoryStatsInfo(StructuredObject):
    #         slug = unicode

    #     class PlayerInfo(StructuredObject):
    #         categories = TypedDict(CategoryStatsInfo)

    #     stats = CategoryStatsInfo(slug="math")
    #     info = PlayerInfo({
    #         "categories": {"math": {"slug": "math"}}
    #     })

    #     self.assert_equal(info.categories, {"math": stats})

    #     d = info.to_dict()
    #     self.assert_equal(d, {
    #         "categories": {"math": {"slug": "math"}}
    #     })

    # def test_coerce_to_dict_with_default_type_empty(self):
    #     class CategoryStatsInfo(StructuredObject):
    #         slug = unicode

    #     class PlayerInfo(StructuredObject):
    #         categories = TypedDict(CategoryStatsInfo)

    #     info = PlayerInfo()

    #     self.assert_equal(info.categories, {})

    #     d = info.to_dict()
    #     self.assert_equal(d, {
    #         "categories": {}
    #     })

    # def test_coerce_to_dict_with_default_type_and_key_coercer(self):
    #     class CategoryStatsInfo(StructuredObject):
    #         slug = unicode

    #     class PlayerInfo(StructuredObject):
    #         categories = DictAttribute(CategoryStatsInfo, int, unicode)

    #     stats = CategoryStatsInfo(slug="math")
    #     info = PlayerInfo({
    #         "categories": {"1": {"slug": "math"}}
    #     })

    #     self.assert_equal(info.categories, {1: stats})

    #     d = info.to_dict()
    #     self.assert_equal(d, {
    #         "categories": {"1": {"slug": "math"}}
    #     })

    # def test_coerce_to_dict_with_default_type_and_key_coercer_empty(self):
    #     class CategoryStatsInfo(StructuredObject):
    #         slug = unicode

    #     class PlayerInfo(StructuredObject):
    #         categories = DictAttribute(CategoryStatsInfo, int, unicode)

    #     info = PlayerInfo()

    #     self.assert_equal(info.categories, {})

    #     d = info.to_dict()
    #     self.assert_equal(d, {
    #         "categories": {}
    #     })