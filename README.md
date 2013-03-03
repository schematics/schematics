Schematics
==========

Python Data Structures for Humans™.

**This is a fork of the original project by @j2labs**

## My Changes

1. Removed modules `forms` and `types.mongo`.
2. Changed the error reporting back to to `Exception` based. It now resembles
   the validation chain implimented in WTForms. `FieldResult` and all that is
   gone. Errors are aggregated into `self.errors` and further aggregated into a
   dictionary. I needed this to inform API clients of data errors.
3. The main validation methods now return a `(items, errors)` tuple instead of
   a boolean.
4. `Field.validators` is now a list of callables, similar to WTForms.
5. Some things like type checking was mixed with the validation error reporting
   layer have been changed into simple Python asserts. I considered this a
   leaky abstraction.

## Forms

I added a top level convenience `schematics.Form`. This does 90% of what you
will need in one class (apart from the actual `schematics.types` classes).
Here’s some code to show off what can be accomplished with little heavy lifting.

Please note, all the hard stuff is done in the original non-forked library.
Credit where credit’s due.

```python

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

```

Now that you have your form schemas defined you can start validating data and
dumping it safely.

```python
>>> good_data = {
...   'total_games': 2,
...   'name': u'Jölli',
...   'games': [{'opponent_id': 2}, {'opponent_id': 3}],
...   'bio': u'Iron master',
...   'rank': 6,
... }
>>> player = Player.from_json(good_data)
>>> print json.dumps(player.to_json(), indent=2, sort_keys=True)
{
  "bio": "Iron master",
  "games": [
    {
      "opponent_id": 2
    },
    {
      "opponent_id": 3
    }
  ],
  "name": "J\u00f6lli",
  "total_games": 2,
  "verified": null
}

```

`to_json` has two keyword arguments:

+ `role`: The filter to make output consumable. Default: None (returns all keys)
+ `strict`: Strict mode raises errors for unexpected keys. Default: False
