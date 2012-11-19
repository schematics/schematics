#!/usr/bin/env python


"""{'type': 'object', 'properties': {'personal_thoughts': {'type': 'string', 'id': 'personal_thoughts', 'maxLength': 255}, 'title': {'type': 'string', 'id': 'title', 'maxLength': 40}, 'id': {'type': 'string'}, 'year': {'minimum': 1950, 'type': 'integer', 'id': 'year', 'maximum': 2011}}}
"""


import datetime
from schematics.models import Model
from schematics.types import StringType, IntType, UUIDType
from schematics.serialize import to_python, for_jsonschema, from_jsonschema

###
### The base class
###

class Movie(Model):
    """Simple model that has one StringType member
    """
    id = UUIDType(auto_fill=True)
    title = StringType(max_length=40)
    year = IntType(min_value=1950, max_value=datetime.datetime.now().year)
    personal_thoughts = StringType(max_length=255)

m = Movie(title='Some Movie',
          year=2011,
          personal_thoughts='It was pretty good')


### Serialize the schema and the data
m_schema = for_jsonschema(m)
m_data = to_python(m)
print 'M :: ', m_schema
print '\n'

### Rebuild class from schema
m2_cls = from_jsonschema(m_schema)

m2 = m2_cls()
print 'M2:: ', for_jsonschema(m2)
print '\n'
