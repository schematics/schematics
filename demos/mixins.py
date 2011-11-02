#!/usr/bin/env python

"""This thing to notice in this example is that the class hierarcy is not
influenced by subclassing EmbeddedDocuments with meta['mixin'] = True. This
can be useful if you know you're going to use something of an EmbeddedDocument
in the top level document structure

{
    "_cls": "SomeDoc", 
    "_types": [
        "SomeDoc"
    ], 
    "archived": false, 
    "body": "Scenester twee mlkshk readymade butcher. Letterpress portland +1\nsalvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.\nSartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.\n", 
    "deleted": false, 
    "liked": true, 
    "title": "Some Document"
}
"""

from dictshield.base import BaseField
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import (StringField,
                               BooleanField,
                               URLField,
                               EmailField,
                               LongField,
                               ListField)


class InterestMixin(EmbeddedDocument):
    liked = BooleanField(default=False)
    archived = BooleanField(default=False)
    deleted = BooleanField(default=False)
    meta = {
        'mixin': True,
    }


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

print sd.to_json()
