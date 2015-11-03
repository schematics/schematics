from schematics.datastructures import OrderedDict
from schematics.transforms import expand, whitelist, flatten
from schematics.models import Model
from schematics.types.serializable import serializable
from schematics.types import StringType, IntType
from schematics.types.compound import (
    ModelType, ListType, EMPTY_LIST, DictType, EMPTY_DICT
)


def test_flattend():
    class Location(Model):
        country_code = StringType()
        region_code = StringType()

    info = Location(dict(country_code="US", region_code="CA"))
    flat_dict = info.flatten()

    assert flat_dict == {
        "country_code": "US",
        "region_code": "CA",
    }

    info_from_flat_dict = Location.from_flat(flat_dict)

    assert type(info) == type(info_from_flat_dict)
    assert info == info_from_flat_dict


def test_flatten_with_root_prefix():
    class Location(Model):
        country_code = StringType()
        region_code = StringType()

    info = Location(dict(country_code="US", region_code="CA"))
    flat_dict = info.flatten(prefix="my_location")

    assert flat_dict == {
        "my_location.country_code": "US",
        "my_location.region_code": "CA",
    }


def test_to_flat_dict_one_level_deep():
    class Location(Model):
        country_code = StringType()
        region_code = StringType()

    class PlayerInfo(Model):
        id = StringType()
        location = ModelType(Location)

    location = Location(dict(country_code="US", region_code="CA"))
    info = PlayerInfo(dict(id=1, location=location))

    flat_dict = info.flatten()

    assert flat_dict == {
        "id": "1",
        "location.country_code": "US",
        "location.region_code": "CA",
    }

    info_from_flat_dict = PlayerInfo.from_flat(flat_dict)

    assert type(info) == type(info_from_flat_dict)
    assert info == info_from_flat_dict
    assert info.location == info_from_flat_dict.location


def test_to_flat_dict_two_level_deep():
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
            "id": 1,
        }
    ))

    info = PlayerInfo(dict(
        id="1",
        location=location_info
    ))

    flat_dict = info.flatten()

    assert flat_dict == {
        "id": "1",
        "location.country_code": "US",
        "location.region_code": "CA",
        "location.something.id": 1,
    }

    info_from_flat_dict = PlayerInfo.from_flat(flat_dict)

    assert type(info) == type(info_from_flat_dict)
    assert info == info_from_flat_dict
    assert info_from_flat_dict.location == location_info


def test_flatten_wiht_listtype_empty_value():
    class PlayerCategoryInfo(Model):
        id = StringType(required=True)
        categories = ListType(IntType, required=True)

    p = PlayerCategoryInfo(dict(id="1", categories=[]))
    flat = p.flatten()

    assert flat == {
        "id": "1",
        "categories": EMPTY_LIST,
    }

    p_from_flat = PlayerCategoryInfo.from_flat(flat)
    assert p_from_flat.categories == []
    assert p == p_from_flat


def test_flatten_wiht_listtype_basic_types():
    class PlayerCategoryInfo(Model):
        id = StringType(required=True)
        categories = ListType(IntType, required=True)

    p = PlayerCategoryInfo(dict(id="1", categories=[1, 2, 3]))
    flat = p.flatten()

    assert flat == {
        "id": "1",
        "categories.0": 1,
        "categories.1": 2,
        "categories.2": 3,
    }

    p_from_flat = PlayerCategoryInfo.from_flat(flat)
    assert p_from_flat.categories == [1, 2, 3]
    assert p == p_from_flat


def test_flatten_with_listtype_after_appending():

    class Game(Model):
        players = ListType(StringType, default=lambda: [])

    game = Game()
    game.players.append("John")

    flat_dict = game.flatten()

    assert flat_dict == {
        "players.0": "John",
    }

    game_from_flat_dict = Game.from_flat(flat_dict)

    assert game == game_from_flat_dict


def test_flatten_with_listtype():
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
                "title": "Master",
            }
        },
        {
            "slug": "twilight",
            "xp_level": {
                "level": 2,
                "stars": 1,
                "title": "Master",
            }
        }]
    }
    info = PlayerCategoryInfo(input_data)

    flat_dict = info.flatten()

    assert flat_dict == {
        "id": "1",
        "categories.0.slug": "math",
        "categories.0.xp_level.level": 1,
        "categories.0.xp_level.stars": 1,
        "categories.0.xp_level.title": "Master",
        "categories.1.slug": "twilight",
        "categories.1.xp_level.level": 2,
        "categories.1.xp_level.stars": 1,
        "categories.1.xp_level.title": "Master",
    }

    info_from_flat_dict = PlayerCategoryInfo.from_flat(flat_dict)

    assert info == info_from_flat_dict


def test_flatten_with_dicttype_empty_value():
    class PlayerCategoryInfo(Model):
        id = StringType(required=True)
        categories = DictType(IntType, required=True)

    p = PlayerCategoryInfo(dict(id="1", categories={}))
    flat = p.flatten()

    assert flat == {
        "id": "1",
        "categories": EMPTY_DICT,
    }

    p_from_flat = PlayerCategoryInfo.from_flat(flat)
    assert p_from_flat.categories == {}
    assert p == p_from_flat


def test_flatten_with_dicttype_basic_types():
    class PlayerCategoryInfo(Model):
        id = StringType(required=True)
        categories = DictType(IntType, required=True)

    p = PlayerCategoryInfo(dict(id="1", categories={"a": 1, "b": 2}))
    flat = p.flatten()

    assert flat == {
        "id": "1",
        "categories.a": 1,
        "categories.b": 2
    }

    p_from_flat = PlayerCategoryInfo.from_flat(flat)
    assert p == p_from_flat


def test_flatten_with_dicttype_model_types():
    class CategoryStats(Model):
        total_wins = IntType()

    class PlayerCategoryInfo(Model):
        id = StringType(required=True)
        categories = DictType(ModelType(CategoryStats), required=True)

    p = PlayerCategoryInfo(dict(
        id="1",
        categories={
            "a": {"total_wins": 1},
            "b": {"total_wins": 5},
        }
    ))
    flat = p.flatten()

    assert flat == {
        "id": "1",
        "categories.a.total_wins": 1,
        "categories.b.total_wins": 5,
    }

    p_from_flat = PlayerCategoryInfo.from_flat(flat)
    assert p == p_from_flat


def test_flatten_serializables_on_by_default():
    class ExperienceLevel(Model):
        level = IntType()
        title = StringType()

    class Player(Model):
        total_points = IntType()

        @serializable(type=ModelType(ExperienceLevel))
        def xp_level(self):
            return ExperienceLevel(dict(level=self.total_points * 2, title="Best"))

    ExperienceLevel(dict(level=4, title="Best"))

    player = Player({"total_points": 2})

    assert player.xp_level.level == 4

    flat = player.flatten()
    assert flat == {"total_points": 2, "xp_level.level": 4, "xp_level.title": "Best"}

    player_from_flat = Player.from_flat(flat)
    assert player == player_from_flat


def test_flatten_ignores_none_by_default():
    class Player(Model):
        id = StringType()
        display_name = StringType()

    player = Player({"display_name": "Joe"})

    assert player.id is None

    flat = player.flatten()
    assert flat == {"display_name": "Joe"}

    player_from_flat = Player.from_flat(flat)
    assert player, player_from_flat


def test_flatten_includes_none_when_asked():
    class Player(Model):
        id = StringType()
        display_name = StringType()

    player = Player({"display_name": "Joe"})

    flat = flatten(Player, player, ignore_none=False)

    assert flat == {'display_name': 'Joe', 'id': None}


def test_flatten_with_whitelist():
    class TopicStats(Model):
        total_points = IntType()
        total_wins = IntType()
        total_losses = IntType()

        class Options:
            roles = {
                "public": whitelist("total_wins", "total_losses"),
            }

        @serializable
        def games_played(self):
            return self.total_wins + self.total_losses

    topic_stats = TopicStats(dict(
        total_points=2,
        total_wins=3,
        total_losses=4,
    ))

    flat = topic_stats.flatten(role="public")
    assert flat == {
        "total_wins": 3,
        "total_losses": 4,
    }


def test_flatten_dicts_coercers_keys_to_strings():

    class Player(Model):
        id = StringType()

    class Game(Model):
        id = StringType()
        players = DictType(ModelType(Player), coerce_key=lambda k: int(k))

    g = Game(dict(
        id="1",
        players={
            1: {
                "id": 1,
            }
        }
    ))

    assert g.id == "1"
    assert g.players == {1: Player(dict(id="1"))}

    flat = g.flatten()

    assert flat == {
        "id": "1",
        "players.1.id": "1",
    }

    g_from_flat = Game.from_flat(flat)
    assert g == g_from_flat


def test_expand_with_both_empty_dict_and_values():
    different_orderings = [
        [
            ("categories", '{}'),
            ("categories.basketball.category_slug", 'basketball'),
            ("categories.basketball.total_draws", '0'),
            ("categories.basketball.total_losses", '2'),
        ],
        [
            ("categories.basketball.category_slug", 'basketball'),
            ("categories", '{}'),
            ("categories.basketball.total_draws", '0'),
            ("categories.basketball.total_losses", '2'),
        ],
        [
            ("categories.basketball.category_slug", 'basketball'),
            ("categories.basketball.total_draws", '0'),
            ("categories.basketball.total_losses", '2'),
            ("categories", '{}'),
        ]
    ]

    for ordering in different_orderings:
        flat_data = OrderedDict(ordering)

        expanded = expand(flat_data)
        assert expanded == {
            "categories": {
                "basketball": {
                    "category_slug": "basketball",
                    "total_draws": "0",
                    "total_losses": "2",
                }
            }
        }


def test_expand_with_both_empty_list_and_values():
    different_orderings = [
        [
            ("categories", '[]'),
            ("categories.0", 'basketball'),
            ("categories.1", '0'),
            ("categories.2", '2'),
        ],
        [
            ("categories.0", 'basketball'),
            ("categories", '[]'),
            ("categories.1", '0'),
            ("categories.2", '2'),
        ],
        [
            ("categories.0", 'basketball'),
            ("categories.1", '0'),
            ("categories.2", '2'),
            ("categories", '[]'),
        ]
    ]
    for ordering in different_orderings:
        flat_data = OrderedDict(ordering)

        expanded = expand(flat_data)
        assert expanded == {
            "categories": {
                "0": "basketball",
                "1": "0",
                "2": "2",
            }
        }
