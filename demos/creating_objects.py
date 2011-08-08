#!/usr/bin/env python

"""This class demonstrates the basics of building `Document` structures.  In the
classes below I build a somewhat open-ended `Media` class with a `title`.  After
that I subclass it to make a `Movie` class.

The class hierarchy is listed in the `_types` field.  The class name itself is
saved as `_cls`.  Anything else on the structure is a field you import from
`dictshield.fields`.  Below we use a StringField, ObjectIdField and an IntField.

From Media class to json structure:

    {"_types": ["Media"], "_cls": "Media", "title": "Misc Media"}

From Movie class to json structure:

    {"personal_thoughts": "I wish I had three hands...", "_types": ["Media", "Media.Movie"], "title": "Total Recall", "_cls": "Media.Movie", "year": 1990}

Calling a make*safe funciton.  In this case, it's `make_json_ownersafe`.  This
produces a document with the class structure fields removed.  It functions like
a black list for fields.

    {"personal_thoughts": "I wish I had three hands...", "title": "Total Recall", "year": 1990}

Perhaps we're building an information repository where some of the data in each
`Document` is shareable with the public.  There is another make*safe function to
handle this case.  This time we use `make_json_publicsafe`.

This function checks for a `_public_fields` member on the class and then removes
any key that isn't in that list.  It functions like a white list for fields.

    {"title": "Total Recall", "year": 1990}
"""

import datetime
from dictshield.document import Document
from dictshield.fields import StringField
from dictshield.fields import ObjectIdField
from dictshield.fields import IntField

###
### The base class
###

class Media(Document):
    """Simple document that has one StringField member
    """
    owner = ObjectIdField() # probably set required=True
    title = StringField(max_length=40)

m = Media()
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
