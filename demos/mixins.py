#!/usr/bin/env python

"""SomeDoc as JSON:

    {"body": "Scenester twee mlkshk readymade butcher. Letterpress portland +1\nsalvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.\nSartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.\n", "_types": ["SomeDoc"], "liked": true, "title": "Some Model", "deleted": false, "archived": false, "_cls": "SomeDoc"}
"""

from schematics.models import Model, Mixin
from schematics.types import (BaseType,
                              StringType,
                              BooleanType,
                              URLType,
                              EmailType,
                              LongType)
from schematics.types.compound import ListType


class Interested(Mixin):
    liked = BooleanType(default=False)
    archived = BooleanType(default=False)
    deleted = BooleanType(default=False)


class SomeModel(Model, Interested):
    title = StringType()
    body = StringType()


sm = SomeModel()
sm.liked = True
sm.title = 'Some Model'
sm.body = """Scenester twee mlkshk readymade butcher. Letterpress portland +1
salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.
Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.
"""

print 'SomeDoc as JSON:\n\n    %s\n' % (sm.to_json())
