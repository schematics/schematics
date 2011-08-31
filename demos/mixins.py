#!/usr/bin/env python

from dictshield.base import BaseField, DictPunch
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import (StringField,
                               BooleanField,
                               URLField,
                               EmailField,
                               LongField,
                               ListField,
                               ObjectIdField)


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

print sd.to_python()
