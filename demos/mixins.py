#!/usr/bin/env python

"""SomeDoc as JSON:

    {"body": "Scenester twee mlkshk readymade butcher. Letterpress portland +1\nsalvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.\nSartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.\n", "_types": ["SomeDoc"], "liked": true, "title": "Some Document", "deleted": false, "archived": false, "_cls": "SomeDoc"}
"""

from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import (BaseField,
                               StringField,
                               BooleanField,
                               URLField,
                               EmailField,
                               LongField)
from dictshield.fields.compound import ListField

class InterestMixin(EmbeddedDocument):
    liked = BooleanField(default=False)
    archived = BooleanField(default=False)
    deleted = BooleanField(default=False)
    class Meta:
        mixin = True


class SomeDoc(Document, InterestMixin):
    title = StringField()
    body = StringField()


sd = SomeDoc()
sd.title = 'Some Document'
sd.body = """Scenester twee mlkshk readymade butcher. Letterpress portland +1
salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.
Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.
"""

sd.liked = True

print 'SomeDoc as JSON:\n\n    %s\n' % (sd.to_json())
