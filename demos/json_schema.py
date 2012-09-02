#!/usr/bin/env python


"""{'type': 'object', 'properties': {'personal_thoughts': {'type': 'string', 'id': 'personal_thoughts', 'maxLength': 255}, 'title': {'type': 'string', 'id': 'title', 'maxLength': 40}, 'id': {'type': 'string'}, 'year': {'minimum': 1950, 'type': 'integer', 'id': 'year', 'maximum': 2011}}}
"""


import datetime
from schematics.models import Model
from schematics.types import StringType, IntType

###
### The base class
###

class Movie(Model):
    """Simple model that has one StringType member
    """
    title = StringType(max_length=40)
    year = IntType(min_value=1950, max_value=datetime.datetime.now().year)
    personal_thoughts = StringType(max_length=255)

m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')

print m.for_jsonschema()
