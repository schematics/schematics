#!/usr/bin/env python


"""From Media class to json structure:

    {"owner": "2c8c9806-fafc-4cc7-920b-c8fa2e5f1bee", "_types": ["Media"], "_cls": "Media", "title": "Misc Media"}

From Movie class to json structure:

    {"personal_thoughts": "I wish I had three hands...", "_types": ["Media", "Media.Movie"], "title": "Total Recall", "_cls": "Media.Movie", "year": 1990}

Making mv json safe:

    {"personal_thoughts": "I wish I had three hands...", "title": "Total Recall", "year": 1990}

Making mv json public safe (only ['title', 'year'] should show):

    {"title": "Total Recall", "year": 1990}
"""


import uuid
import datetime
from dictshield.document import Document
from dictshield.fields import (StringField,
                               IntField,
                               UUIDField)


###
### The base class
###

class Media(Document):
    """Simple document that has one StringField member
    """
    owner = UUIDField()
    title = StringField(max_length=40)

make_believe_owner_id = uuid.uuid4()

m = Media()
m.owner = make_believe_owner_id
m.title = 'Misc Media'
print 'From Media class to json structure:\n\n    %s\n' % (m.to_json())


###
### Subclass `Media` to create a `Movie`
###

class Movie(Media):
    """Subclass of Foo. Adds bar and limits publicly shareable
    fields to only 'bar'.
    """
    _public_fields = ['title','year']
    year = IntField(min_value=1950, max_value=datetime.datetime.now().year)
    personal_thoughts = StringField(max_length=255)

mv = Movie()
mv.title = 'Total Recall'
mv.year = 1990
mv.personal_thoughts = 'I wish I had three hands...' # (.Y.Y.)
print 'From Movie class to json structure:\n\n    %s\n' % (mv.to_json())


###
### Scrubbing functions
###

ownersafe_json = Movie.make_json_ownersafe(mv)
ownersafe_str = 'Making mv json safe:\n\n    %s\n'
print ownersafe_str % (ownersafe_json)

publicsafe_json = Movie.make_json_publicsafe(mv)
publicsafe_str = 'Making mv json public safe (only %s should show):\n\n    %s\n'
print  publicsafe_str % (Movie._public_fields, publicsafe_json)
