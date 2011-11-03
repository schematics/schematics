#!/usr/bin/env python

"""
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


