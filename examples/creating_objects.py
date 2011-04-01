#!/usr/bin/env python

import datetime
from dictshield.document import Document
from dictshield.fields import StringField
from dictshield.fields import ObjectIdField
from dictshield.fields import IntField


class Media(Document):
    """Simple document that has one StringField member
    """
    owner = ObjectIdField() # probably set required=True
    title = StringField(max_length=40)

m = Media()
m.title = 'Misc Media'
print 'From Media class to json structure:\n\n    %s\n' % (m.to_json())


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
mv.personal_thoughts = 'I wish I had three hands...' # :P
print 'From Movie class to json structure:\n\n    %s\n' % (mv.to_json())


ownersafe_json = Movie.make_json_ownersafe(mv.to_json())
ownersafe_str = 'Making mv json safe:\n\n    %s\n'
print ownersafe_str % (ownersafe_json)

publicsafe_json = Movie.make_json_publicsafe(mv.to_json())
publicsafe_str = 'Making mv json public safe (only %s should show):\n\n    %s\n'
print  publicsafe_str % (Movie._public_fields, publicsafe_json)
                                                               
