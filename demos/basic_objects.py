#!/usr/bin/env python


"""From Media class to json string:

    {"owner": "ba2fa3fb-0d51-4545-8131-24b8a5c86282", "id": "ddb01ce9-d337-493b-8860-2220689b6cfe", "title": "Misc Media"}

From Movie class to json string:

    {"personal_thoughts": "I wish I had three hands...", "title": "Total Recall", "id": "5b5f6ed8-587d-4b3b-a109-6415eee5d8a6", "year": 1990}

    {'personal_thoughts': u'I wish I had three hands...', 'title': u'Total Recall', 'id': UUID('5b5f6ed8-587d-4b3b-a109-6415eee5d8a6'), 'year': 1990}

    {"personal_thoughts": "I wish I had three hands...", "title": "Total Recall", "id": "5b5f6ed8-587d-4b3b-a109-6415eee5d8a6", "year": 1990}

Making mv json safe:

    {"owner": null, "personal_thoughts": "I wish I had three hands...", "title": "Total Recall", "id": "5b5f6ed8-587d-4b3b-a109-6415eee5d8a6", "year": 1990}

Making mv json public safe (only ['title', 'year'] should show):

    {"title": "Total Recall", "year": 1990}

You can also scrub the models according to whatever system you want:

    {"title": "Total Recall"}
"""


import uuid
import datetime
from schematics.models import Model
from schematics.serialize import (to_python, to_json, make_safe_python,
                                  make_safe_json, blacklist, whitelist)
from schematics.types import (StringType, IntType, UUIDType)


###
### The base class
###

class Media(Model):
    """Simple document that has one StringField member
    """
    id = UUIDType(auto_fill=True)
    owner = UUIDType()
    title = StringType(max_length=40)

make_believe_owner_id = uuid.uuid4()

m = Media()
m.owner = make_believe_owner_id
m.title = 'Misc Media'

print 'From Media class to json string:\n\n    %s\n' % (to_json(m))


###
### Subclass `Media` to create a `Movie`
###

class Movie(Media):
    """Subclass of Foo. Adds bar and limits publicly shareable
    fields to only 'bar'.
    """
    year = IntType(min_value=1950, max_value=datetime.datetime.now().year)
    personal_thoughts = StringType(max_length=255)
    class Options:
        roles = {
            'owner': blacklist(),
            'public': whitelist('title', 'year'),
        }

mv = Movie()
mv.title = 'Total Recall'
mv.year = 1990
mv.personal_thoughts = 'I wish I had three hands...'

print 'From Movie class to json string:\n\n    %s\n' % (to_json(mv))
print '    %s\n' % (to_python(mv, allow_none=True))
print '    %s\n' % (to_json(mv, allow_none=True))


###
### Scrubbing functions
###

ownersafe_json = make_safe_json(Movie, mv, 'owner')
ownersafe_str = 'Making mv safe:\n\n    %s\n'
print ownersafe_str % (ownersafe_json)

publicsafe_json = make_safe_json(Movie, mv, 'public')
publicsafe_str = 'Making mv safe in json:\n\n    %s\n'
print  publicsafe_str % (publicsafe_json)

print 'You can also scrub the models according to whatever system you want:\n'
print '    %s\n' % (to_json(mv, gottago=whitelist('title')))
