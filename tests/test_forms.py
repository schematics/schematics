# encoding=utf-8

import unittest

from schematics import Form, InvalidForm
from schematics.types import StringType, IntType, DateTimeType, BooleanType
from schematics.types.compound import ModelType, ListType
from schematics.exceptions import ValidationError
from schematics.serialize import whitelist


class Game(Form):
    opponent_id = IntType(required=True)

class Player(Form):
    total_games = IntType(min_value=0, required=True)
    name = StringType(required=True)
    verified = BooleanType()
    bio = StringType()
    games = ListType(ModelType(Game), required=True)

    class Options:
        roles = {
            'public': whitelist('total_games', 'name', 'bio', 'games'),
        }


def multiple_of_three(value):
    if value % 3 != 0:
        raise ValidationError, u'Game master rank must be a multiple of 3'

class GameMaster(Player):
    rank = IntType(min_value=0, max_value=12, validators=[multiple_of_three], required=True)


class TestChoices(unittest.TestCase):

    good_data = {
        'total_games': 2,
        'name': u'Jölli',
        'games': [{'opponent_id': 2}, {'opponent_id': 3}],
        'bio': u'Iron master',
        'rank': 6,
    }

    def assertErrors(self, form, data, error_fields, partial=False):
        with self.assertRaises(InvalidForm) as cm:
            player = form.from_json(data, partial=partial)
        self.assertEqual(set(cm.exception.errors), set(error_fields))

    def test_partial_form(self):
        self.assertErrors(Player, {'bio': 'Iron Master'}, 'games name total_games'.split())
        player = Player.from_json({'bio': 'Irom master'}, partial=True)

    def test_strict_input(self):
        with self.assertRaises(InvalidForm) as cm:
            Player.from_json(self.good_data, strict=True)
        self.assertEqual(cm.exception.errors.keys(), ['rank'])

    def test_public_role(self):
        player = Player.from_json(self.good_data)
        public_keys = set(player.to_json(role="public").keys())
        self.assertEqual(public_keys, set('bio games name total_games'.split()))

    def test_subclass_form(self):
        player = GameMaster.from_json(self.good_data)
        self.assertEqual(len(player.games), 2)
        self.assertTrue(isinstance(player.games[0], Game))

    def test_custom_validators(self):
        with self.assertRaises(InvalidForm) as cm:
            player = GameMaster.from_json({
                'rank': '2',
            }, partial=True)
        self.assertIn('rank', cm.exception.errors)

