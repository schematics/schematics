#!/usr/bin/env python

"""This demo simply shows how the specifics of a DictShield's model design can
be translated easily into a JSON schema definition.

$ ./json_schema.py 
{'type': 'object', 'properties': {'personal_thoughts': {'type': 'string', 'id': 'personal_thoughts', 'maxLength': 255}, 'title': {'type': 'string', 'id': 'title', 'maxLength': 40}, 'id': {'type': 'string'}, 'year': {'minimum': 1950, 'type': 'integer', 'id': 'year', 'maximum': 2011}}}
"""

import datetime
from dictshield.document import Document
from dictshield.fields import StringField, IntField

###
### The base class
###

class Movie(Document):
    """Simple document that has one StringField member
    """
    title = StringField(max_length=40)
    year = IntField(min_value=1950, max_value=datetime.datetime.now().year)
    personal_thoughts = StringField(max_length=255)

m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')

print m.for_jsonschema()


