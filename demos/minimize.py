#!/usr/bin/env python


"""MOVIE ] ----------------------------------------
    schema :: {"type": "object", "properties": {"y": {"minimum": 1950, "type": "number", "maximum": 2012, "title": "year"}, "p": {"title": "personal_thoughts", "type": "string", "maxLength": 255}, "t": {"title": "title", "type": "string", "maxLength": 40}}, "title": "Movie"}
    python :: {'y': 2011, 'p': u'It was pretty good', 't': u'Some Movie'}
      json :: {"y": 2011, "p": "It was pretty good", "t": "Some Movie"}
     owner :: {'y': 2011, 'p': u'It was pretty good', 't': u'Some Movie'}
    public :: {"y": 2011, "t": "Some Movie"}

Movie as JSON ] --------------------------------
      json :: {"y": 2011, "p": "It was pretty good", "t": "Some Movie"}

RESTORED MOVIE ] -------------------------------
    schema :: {"type": "object", "properties": {"y": {"minimum": 1950, "type": "number", "maximum": 2012, "title": "year"}, "p": {"title": "personal_thoughts", "type": "string", "maxLength": 255}, "t": {"title": "title", "type": "string", "maxLength": 40}}, "title": "Movie"}
"""

import json
import datetime

from schematics.models import Model
from schematics.types import StringType, IntType
from schematics.serialize import (to_python, to_json, to_jsonschema,
                                  whitelist, blacklist,
                                  make_safe_python, make_safe_json)

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
        roles = {
            'owner': blacklist(),
            'public': whitelist('title', 'year'),
        }
        


m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')


print 'MOVIE ]', ('-' * 40)
print '    schema ::', to_jsonschema(m)
print '    python ::', to_python(m)
print '      json ::', to_json(m)
print '     owner ::', make_safe_python(Movie, m, 'owner')
print '    public ::', make_safe_json(Movie, m, 'public')
print


#movie_json = m.to_json()
movie_json = make_safe_json(Movie, m, 'owner')
print 'Movie as JSON ]', ('-' * 32)
print '      json ::', movie_json
print


### Reload movie
movie_data = json.loads(movie_json)
m2 = Movie(**movie_data)

print 'RESTORED MOVIE ]', ('-' * 31)
print '    schema ::', to_jsonschema(m2)
print '    python ::', to_python(m2)
print '      json ::', to_json(m2)
print '     owner ::', make_safe_python(Movie, m2, 'owner')
print '    public ::', make_safe_json(Movie, m2, 'public')

