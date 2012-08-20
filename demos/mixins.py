#!/usr/bin/env python

"""SomeDoc as JSON:

    {"body": "Scenester twee mlkshk readymade butcher. Letterpress portland +1\nsalvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.\nSartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.\n", "_types": ["SomeDoc"], "liked": true, "title": "Some Model", "deleted": false, "archived": false, "_cls": "SomeDoc"}
"""

from structures.models import Model
from structures.types import (BaseType,
                              StringType,
                              BooleanType,
                              URLType,
                              EmailType,
                              LongType)
from structures.types.compound import ListType


class Interested(Model):
    liked = BooleanType(default=False)
    archived = BooleanType(default=False)
    deleted = BooleanType(default=False)
    class Meta:
        mixin = True


class SomeModel(Model, Interested):
    title = StringType()
    body = StringType()


sm = SomeModel()
sm.title = 'Some Model'
sm.body = """Scenester twee mlkshk readymade butcher. Letterpress portland +1
salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.
Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.
"""

sm.liked = True

print 'SomeDoc as JSON:\n\n    %s\n' % (sm.to_json())
