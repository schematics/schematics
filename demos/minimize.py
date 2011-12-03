#!/usr/bin/env python

import json

import sys
sys.path.append('..')

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
    
    _public_fields = ["title", "year", "personal_thoughts"]
    
    title = StringField(max_length=40, minimized_field_name="t")
    year = IntField(min_value=1950, max_value=datetime.datetime.now().year, minimized_field_name="y")
    personal_thoughts = StringField(max_length=255, minimized_field_name="p")

m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')

# print m.for_jsonschema()
# print m.to_python()
print Movie.make_json_publicsafe(m)

print Movie.make_publicsafe(m)

data = json.loads(Movie.make_json_publicsafe(m))
print data

print "====="

m2 = Movie(**data)
print m2.title
print m2.year
print m2.personal_thoughts

print Movie.make_publicsafe(m2)

print m2.to_python()