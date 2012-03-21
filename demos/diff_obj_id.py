#!/usr/bin/env python


"""SimpleDoc:

    {'_types': ['SimpleDoc'], 'title': u'simple doc', 'num': 1998, '_cls': 'SimpleDoc', '_id': ObjectId('4ee41cdc0f43833917000000')}

Validating SimpleDoc instance
Validation passed

ComplexDoc:

    {'_types': ['SimpleDoc', 'SimpleDoc.ComplexDoc'], 'title': u'complex title', 'num': 1996, '_cls': 'SimpleDoc.ComplexDoc', '_id': ObjectId('4ee41cdc0f43833917000001')}

ComplexDoc JSON:

    {"_types": ["SimpleDoc", "SimpleDoc.ComplexDoc"], "title": "complex title", "num": 1996, "_cls": "SimpleDoc.ComplexDoc", "_id": "4ee41cdc0f43833917000001"}

ComplexDoc ownersafe:

    {'num': 1996, 'title': 'complex title'}

ComplexDoc publicsafe:

    {'id': ObjectId('4ee41cdc0f43833917000001')}

Validating ComplexDoc instance
Validation passed
"""


from dictshield.document import diff_id_field
from dictshield.document import Document
from dictshield.fields import StringField, IntField
from dictshield.fields.mongo import ObjectIdField

from bson.objectid import ObjectId


###
### Decorate a Document instance with diff_id_field to swap UUIDField for
### ObjectIdField.
###

class SimpleDoc(Document):
    title = StringField(max_length=40)
    num = IntField()
    class Meta:
        id_field = ObjectIdField
    


sd = SimpleDoc()
sd.title = 'simple doc'
sd.num = 1998
sd.id = ObjectId()
print 'SimpleDoc:\n\n    %s\n' % (sd.to_python())

print 'Validating SimpleDoc instance'
sd.validate()
print 'Validation passed\n'


###
### Subclass decorated object to show inheritance works fine
###

class ComplexDoc(SimpleDoc):
    body = StringField()


cd = ComplexDoc()
cd.title = 'complex title'
cd.num = 1996
cd.id = ObjectId()
print 'ComplexDoc:\n\n    %s\n' % (cd.to_python())
print 'ComplexDoc JSON:\n\n    %s\n' % (cd.to_json())
print 'ComplexDoc ownersafe:\n\n    %s\n' % (ComplexDoc.make_ownersafe(cd))
print 'ComplexDoc publicsafe:\n\n    %s\n' % (ComplexDoc.make_publicsafe(cd))

print 'Validating ComplexDoc instance'
cd.validate()
print 'Validation passed\n'
