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
6. Removed `to_python`. Having the model instance is Python enough for me.
7. Removed all jsonschema related things.
8. Removed the demos. If this goes well I will write up proper documentation
   with examples.
9. Renamed to_json to to_dict and removed all mention of json.
10. Redid the declarative stuff and field getters and setters. Inspired by
   fungiform by @mitsuhiko.
11. Redid the compound types, not sure why, but that’s what happens when you
   start refactoring and don’t know where to stop.

Finally settled on terminology for receiving and sending data. The term
"primitive" is used to express a lowest common denominator datatype. Usually
this would pretty much be a string, but JSON is a little more expressive so
we allow a little more here. All fields impliment `to_primitive` and `convert`.
Again, taking queues from fungiform.

## Models

I added classmethod `validate` and `serialize` to the model. This does 90% of
what you will need in one class (apart from the actual `schematics.types`
classes). Here’s some code to show off what can be accomplished with little
heavy lifting.

All the hard stuff is done in the original non-forked library. Credit where
credit’s due.

```python

from schematics import Model, InvalidModel
from schematics.types import StringType, IntType, DateTimeType, BooleanType
from schematics.types.compound import ModelType, ListType
from schematics.exceptions import ValidationError
from schematics.serialize import whitelist


class Game(Model):
    opponent_id = IntType(required=True)

class Player(Model):
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


You can instantiate models with the constructor

```python
>>> model = Model(**items)
```

Setting raw data will automatically initiate needed models:

```python
>>> from schematics.models import Model
>>> from schematics.types import StringType
>>> from schematics.types.compound import ModelType
>>>
>>> model.user = {'name': u'Doggy'}
>>> type()

No validation has occured. To send data back out, user serialize and the role
system.

`Model.serialize`

+ `role`: The filter to make output consumable. Default: None (returns all keys)

`Model.validate`

+ `items`: Untrusted data tree from `json.loads` or such
+ `strict`: Strict mode raises errors for unexpected keys. Default: True
+ `partial`: Ignore `required=True` requirements when validating fields. Default: False
