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
    
    _public_fields = ["title", "year"]
    
    title = StringField(max_length=40, minimized_field_name="t")
    year = IntField(min_value=1950, max_value=datetime.datetime.now().year, minimized_field_name="y")
    personal_thoughts = StringField(max_length=255, minimized_field_name="p")

m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')

print 'MOVIE ]', ('-' * 40)
print '    schema ::', m.for_jsonschema()
print '    python ::', m.to_python()
print '     owner ::', Movie.make_ownersafe(m)
print '    public ::', Movie.make_json_publicsafe(m)
print

#movie_json = m.to_json()
movie_json = Movie.make_json_ownersafe(m)
print 'Movie as JSON ]', ('-' * 32)
print '      json ::', movie_json
print

### Reload movie
movie_data = json.loads(movie_json)
m2 = Movie(**movie_data)

print 'RESTORED MOVIE ]', ('-' * 31)
print '    schema ::', m2.for_jsonschema()
print '    python ::', m2.to_python()
print '     owner ::', Movie.make_ownersafe(m2)
print '    public ::', Movie.make_json_publicsafe(m2)

