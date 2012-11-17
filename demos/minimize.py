#!/usr/bin/env python


"""MOVIE ] ----------------------------------------
    schema :: {'type': 'object', 'properties': {'year': {'minimum': 1950, 'type': 'number', 'maximum': 2011, 'title': 'year'}, 'title': {'title': 'title', 'type': 'string', 'maxLength': 40}}, 'title': 'Movie'}
    python :: {'p': u'It was pretty good', 't': u'Some Movie', 'y': 2011}
      json :: {"p": "It was pretty good", "t": "Some Movie", "y": 2011}
     owner :: {'p': 'It was pretty good', 't': 'Some Movie', 'y': 2011}
    public :: {"y": 2011, "t": "Some Movie"}

Movie as JSON ] --------------------------------
      json :: {"p": "It was pretty good", "t": "Some Movie", "y": 2011}

RESTORED MOVIE ] -------------------------------
    schema :: {'type': 'object', 'properties': {'year': {'minimum': 1950, 'type': 'number', 'maximum': 2011, 'title': 'year'}, 'title': {'title': 'title', 'type': 'string', 'maxLength': 40}}, 'title': 'Movie'}
    python :: {'p': u'It was pretty good', 't': u'Some Movie', 'y': 2011}
      json :: {"p": "It was pretty good", "title": "Some Movie", "y": 2011}
     owner :: {'p': u'It was pretty good', 't': u'Some Movie', 'y': 2011}
    public :: {"y": 2011, "t": "Some Movie"}
"""

import json

import datetime
from schematics.models import Model
from schematics.types import StringType, IntType
from schematics.serialize import (to_python, to_json, for_jsonschema,
                                  make_ownersafe, make_json_ownersafe,
                                  make_json_publicsafe)

###
### The base class
###

class Movie(Model):
    """Simple model that has one StringType member
    """
    title = StringType(max_length=40, minimized_field_name="t")
    year = IntType(min_value=1950,max_value=datetime.datetime.now().year,
                   minimized_field_name="y")
    personal_thoughts = StringType(max_length=255, minimized_field_name="p")
    class Options:
        public_fields = ["title", "year"]


m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')


print 'MOVIE ]', ('-' * 40)
print '    schema ::', for_jsonschema(m)
print '    python ::', to_python(m)
print '      json ::', to_json(m)
print '     owner ::', make_ownersafe(Movie, m)
print '    public ::', make_json_publicsafe(Movie, m)
print


#movie_json = m.to_json()
movie_json = make_json_ownersafe(Movie, m)
print 'Movie as JSON ]', ('-' * 32)
print '      json ::', movie_json
print


### Reload movie
movie_data = json.loads(movie_json)
m2 = Movie(**movie_data)

print 'RESTORED MOVIE ]', ('-' * 31)
print '    schema ::', for_jsonschema(m2)
print '    python ::', to_python(m2)
print '      json ::', to_json(m2)
print '     owner ::', make_ownersafe(Movie, m2)
print '    public ::', make_json_publicsafe(Movie, m2)

