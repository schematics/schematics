
import unittest

from schematics.serialize import expand
from schematics.models import Model
from schematics.types import StringType, IntType
from schematics.types.compound import ModelType, ListType


class FlattenTests(unittest.TestCase):

    def test_flattend(self):
        class Location(Model):
            country_code = StringType()
            region_code = StringType()

        info = Location(dict(country_code="US", region_code="CA"))
        flat_dict = info.serialize(flat=True)

        self.assertEqual(flat_dict, {
            "country_code": "US",
            "region_code": "CA"
        })

        info_from_flat_dict = Location.from_flat(flat_dict)

        self.assertEqual(type(info), type(info_from_flat_dict))
        self.assertEqual(info, info_from_flat_dict)

    def test_to_flat_dict_one_level_deep(self):
        class Location(Model):
            country_code = StringType()
            region_code = StringType()

        class PlayerInfo(Model):
            id = StringType()
            location = ModelType(Location)

        location = Location(dict(country_code="US", region_code="CA"))
        info = PlayerInfo(dict(id=1, location=location))

        flat_dict = info.serialize(flat=True)

        self.assertEqual(flat_dict, {
            "id": "1",
            "location.country_code": "US",
            "location.region_code": "CA"
        })

        info_from_flat_dict = PlayerInfo.from_flat(flat_dict)

        self.assertEqual(type(info), type(info_from_flat_dict))
        self.assertEqual(info, info_from_flat_dict)
        self.assertEqual(info.location, info_from_flat_dict.location)

    def test_to_flat_dict_two_level_deep(self):
        class Something(Model):
            id = IntType()

        class Location(Model):
            country_code = StringType()
            region_code = StringType()

            something = ModelType(Something)

        class PlayerInfo(Model):
            id = StringType()
            location = ModelType(Location)

        location_info = Location(dict(
            country_code="US",
            region_code="CA",
            something={
                "id": 1
            }
        ))

        info = PlayerInfo(dict(
            id="1",
            location=location_info
        ))

        flat_dict = info.serialize(flat=True)

        self.assertEqual(flat_dict, {
            "id": "1",
            "location.country_code": "US",
            "location.region_code": "CA",
            "location.something.id": 1
        })

        info_from_flat_dict = PlayerInfo.from_flat(flat_dict)

        self.assertEqual(type(info), type(info_from_flat_dict))
        self.assertEqual(info, info_from_flat_dict)
        self.assertEqual(info_from_flat_dict.location, location_info)

    def test_to_flat_dict_if_has_json_list_as_attribute(self):
        class ExperienceLevelInfo(Model):
            level = IntType()
            stars = IntType()
            title = StringType()

        class CategoryStatsInfo(Model):
            slug = StringType()

            xp_level = ModelType(ExperienceLevelInfo)

        class PlayerInfo(Model):
            id = StringType()

        class PlayerCategoryInfo(PlayerInfo):
            categories = ListType(ModelType(CategoryStatsInfo))

        input_data = {
            "id": 1,
            "categories": [
            {
                "slug": "math",
                "xp_level": {
                    "level": 1,
                    "stars": 1,
                    "title": "Master"
                }
            },
            {
                "slug": "twilight",
                "xp_level": {
                    "level": 2,
                    "stars": 1,
                    "title": "Master"
                }
            }]
        }
        info = PlayerCategoryInfo(input_data)

        flat_dict = info.serialize(flat=True)

        self.assertEqual(flat_dict, {
            "id": "1",
            "categories.0.slug": "math",
            "categories.0.xp_level.level": 1,
            "categories.0.xp_level.stars": 1,
            "categories.0.xp_level.title": "Master",
            "categories.1.slug": "twilight",
            "categories.1.xp_level.level": 2,
            "categories.1.xp_level.stars": 1,
            "categories.1.xp_level.title": "Master",
        })

        info_from_flat_dict = PlayerCategoryInfo.from_flat(flat_dict)

        self.assertEqual(info, info_from_flat_dict)

#     def test_to_flat_dict_ignores_none(self):
#         class LocationInfo(StructuredObject):
#             country_code = unicode
#             region_code = unicode

#         info = LocationInfo(country_code="US")
#         flat_dict = info.to_flat_dict()

#         self.assert_equal(flat_dict, {
#             "country_code": "US",
#         })

#         info_from_flat_dict = LocationInfo.from_flat_dict(flat_dict)

#         self.assert_equal(type(info), type(info_from_flat_dict))
#         self.assert_equal(info, info_from_flat_dict)

#     def test_to_flat_dict_perserves_dicts(self):
#         class LocationInfo(StructuredObject):
#             urls = dict

#         info = LocationInfo(urls={"a": True})
#         flat_dict = info.to_flat_dict()

#         self.assert_equal(flat_dict, {
#             "urls.a": True,
#         })

#         info_from_flat_dict = LocationInfo.from_flat_dict(flat_dict)

#         self.assert_equal(info, info_from_flat_dict)



#     def test_to_flat_dict_if_has_json_dict_as_attribute(self):
#         class ExperienceLevelInfo(StructuredObject):
#             level = int
#             stars = int
#             title = unicode

#         class CategoryStatsInfo(StructuredObject):
#             slug = unicode

#             xp_level = ExperienceLevelInfo

#         class PlayerInfo(StructuredObject):
#             id = (long, unicode)

#         class PlayerCategoryInfo(PlayerInfo):
#             categories = TypedDict(CategoryStatsInfo)

#         info = PlayerCategoryInfo({
#             "id": 1,
#             "categories": {
#                 "math": {
#                     "slug": "math",
#                     "xp_level": {
#                         "level": 1,
#                         "stars": 1,
#                         "title": "Master"
#                     }
#                 }
#             }
#         })

#         flat_dict = info.to_flat_dict()

#         self.assert_equal(flat_dict, {
#             "id": "1",
#             "categories.math.slug": "math",
#             "categories.math.xp_level.level": 1,
#             "categories.math.xp_level.stars": 1,
#             "categories.math.xp_level.title": "Master",
#         })

#         info_from_flat_dict = PlayerCategoryInfo.from_flat_dict(flat_dict)

#         self.assert_equal(info, info_from_flat_dict)

#     def test_to_flat_dict_if_has_list_as_attribute(self):
#         class PlayerInfo(StructuredObject):
#             id = (long, unicode)
#             followers = list

#         info = PlayerInfo({
#             "id": "1",
#             "followers": [1, 2, 3]
#         })

#         flat_dict = info.to_flat_dict()
#         self.assert_equal(flat_dict, {
#             "id": "1",
#             "followers.0": 1,
#             "followers.1": 2,
#             "followers.2": 3,
#         })

#         info_from_flat_dict = PlayerInfo.from_flat_dict(flat_dict)

#         self.assert_equal(info, info_from_flat_dict)



#     def test_coerce_to_flat_dict_with_default_type_and_key_coercer(self):
#         class CategoryStatsInfo(StructuredObject):
#             slug = unicode

#         class PlayerInfo(StructuredObject):
#             categories = DictAttribute(CategoryStatsInfo, int, unicode)

#         stats = CategoryStatsInfo(slug="math")
#         info = PlayerInfo({
#             "categories": {"1": {"slug": "math"}}
#         })

#         self.assert_equal(info.categories, {1: stats})

#         flat_dict = info.to_flat_dict()
#         self.assert_equal(flat_dict, {
#             "categories.1.slug": "math"
#         })

#         info_from_flat_dict = PlayerInfo.from_flat_dict(flat_dict)

#         self.assert_equal(info, info_from_flat_dict)


# class MultipleInheritanceTests(PEP8TestCase):

#     def test_mixin(self):
#         class Mixin(object):

#             def to_dict(self):
#                 d = super(Mixin, self).to_dict()
#                 d["mango"] = True
#                 return d

#         class PlayerInfo(Mixin, StructuredObject):
#             id = int

#         info = PlayerInfo(id=1)

#         self.assert_equal(info.id, 1)

#         self.assert_equal(info.to_dict(), {
#             "id": 1,
#             "mango": True
#         })

#     def test_mixin_with_subclass(self):
#         class Mixin(object):

#             def to_dict(self):
#                 d = super(Mixin, self).to_dict()
#                 d["mango"] = True
#                 return d

#         class PlayerInfo(StructuredObject):
#             id = int

#         class PlayerCategoryInfo(Mixin, PlayerInfo):
#             secret = unicode

#         info = PlayerCategoryInfo(id=1, secret="leyni")

#         self.assert_equal(info.id, 1)
#         self.assert_equal(info.secret, "leyni")

#         self.assert_equal(info.to_dict(), {
#             "id": 1,
#             "secret": "leyni",
#             "mango": True
#         })