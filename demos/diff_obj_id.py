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


from structures.models import diff_id_field
from structures.models import Model
from structures.types import StringType, IntType
from structures.types.mongo import ObjectIdType

from bson.objectid import ObjectId


###
### Decorate a Document instance with diff_id_field to swap UUIDField for
### ObjectIdField.
###

class SimpleModel(Model):
    title = StringType(max_length=40)
    num = IntType()
    class Meta:
        id_field = ObjectIdType
    


sm = SimpleModel()
sm.title = 'simple model'
sm.num = 1998
sm.id = ObjectId()
print 'SimpleModel:\n\n    %s\n' % (sm.to_python())

print 'Validating SimpleModel instance'
sm.validate()
print 'Validation passed\n'


###
### Subclass decorated object to show inheritance works fine
###

class ComplexModel(SimpleModel):
    body = StringType()


cm = ComplexModel()
cm.title = 'complex title'
cm.num = 1996
cm.id = ObjectId()
print 'ComplexModel:\n\n    %s\n' % (cm.to_python())
print 'ComplexModel JSON:\n\n    %s\n' % (cm.to_json())
print 'ComplexModel ownersafe:\n\n    %s\n' % (ComplexModel.make_ownersafe(cm))
print 'ComplexModel publicsafe:\n\n    %s\n' % (ComplexModel.make_publicsafe(cm))

print 'Validating ComplexModel instance'
cm.validate()
print 'Validation passed\n'
