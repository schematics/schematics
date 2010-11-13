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
print 'From Media class to mongo structure:\n\n    %s\n' % (m.to_mongo())



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
print 'From Movie class to mongo structure:\n\n    %s\n' % (mv.to_mongo())


safe_json = Movie.make_json_safe(mv.to_mongo())
safe_str = 'Making mv json safe:\n\n    %s\n'
print safe_str % (safe_json)

publicsafe_json = Movie.make_json_publicsafe(safe_json)
psafe_str = 'Making mv json public safe (only %s should show):\n\n    %s\n'
print  psafe_str % (Movie._public_fields, publicsafe_json)
                                                               
