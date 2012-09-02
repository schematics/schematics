#!/usr/bin/env python

print """ 

THIS DEMO IS CURRENTLY BROKEN

"""


"""MOVIE ] ----------------------------------------
    schema :: {'type': 'object', 'properties': {'year': {'minimum': 1950, 'type': 'number', 'maximum': 2011, 'title': 'year'}, 'title': {'title': 'title', 'type': 'string', 'maxLength': 40}}, 'title': 'Movie'}
    python :: {'personal_thoughts': u'It was pretty good', '_types': ['Movie'], 'title': u'Some Movie', '_cls': 'Movie', 'year': 2011}
      json :: {"personal_thoughts": "It was pretty good", "_types": ["Movie"], "title": "Some Movie", "_cls": "Movie", "year": 2011}
     owner :: {'p': 'It was pretty good', 't': 'Some Movie', 'y': 2011}
    public :: {"y": 2011, "t": "Some Movie"}

Movie as JSON ] --------------------------------
      json :: {"p": "It was pretty good", "t": "Some Movie", "y": 2011}

RESTORED MOVIE ] -------------------------------
    schema :: {'type': 'object', 'properties': {'year': {'minimum': 1950, 'type': 'number', 'maximum': 2011, 'title': 'year'}, 'title': {'title': 'title', 'type': 'string', 'maxLength': 40}}, 'title': 'Movie'}
    python :: {'personal_thoughts': u'It was pretty good', '_types': ['Movie'], 'title': u'Some Movie', '_cls': 'Movie', 'year': 2011}
      json :: {"personal_thoughts": "It was pretty good", "_types": ["Movie"], "title": "Some Movie", "_cls": "Movie", "year": 2011}
     owner :: {'p': u'It was pretty good', 't': u'Some Movie', 'y': 2011}
    public :: {"y": 2011, "t": "Some Movie"}
"""

import json

import sys
sys.path.append('..')

import datetime
from schematics.models import Model
from schematics.types import StringType, IntType

###
### The base class
###

class Movie(Model):
    """Simple model that has one StringType member
    """
    
    _public_types = ["title", "year"]
    
    title = StringType(max_length=40, minimized_field_name="t")
    year = IntType(min_value=1950, max_value=datetime.datetime.now().year, minimized_field_name="y")
    personal_thoughts = StringType(max_length=255, minimized_field_name="p")

m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')

print 'MOVIE ]', ('-' * 40)
print '    schema ::', m.for_jsonschema()
print '    python ::', m.to_python()
print '      json ::', m.to_json()
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
print '      json ::', m2.to_json()
print '     owner ::', Movie.make_ownersafe(m2)
print '    public ::', Movie.make_json_publicsafe(m2)

