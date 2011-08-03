#!/usr/bin/env python

from dictshield.document import EmbeddedDocument,Document
from dictshield.fields import StringField, EmbeddedDocumentField, ListField

class Action(EmbeddedDocument):
    name = StringField(required=True, max_length=256)

class TaskL(Document):
    action = ListField(EmbeddedDocumentField(Action))

class Task(Document):
    action = EmbeddedDocumentField(Action)

a = Action(name='Phone call')

tl = TaskL()
t=Task()

tl.action = [a]
t.action = a

print a.to_python()
print tl.to_python()
print t.to_python()

print a.to_json()
print tl.to_json()
print t.to_json()
