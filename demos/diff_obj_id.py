#!/usr/bin/env python


from dictshield.document import diff_id_field
from dictshield.document import Document
from dictshield.fields import StringField, IntField
from dictshield.fields.mongo import ObjectIdField

from bson.objectid import ObjectId


###
### Decorate a Document instance with diff_id_field to swap UUIDField for
### ObjectIdField.
###

@diff_id_field(ObjectIdField, ['id'])
class SimpleDoc(Document):
    """Simple document.
    """
    title = StringField(max_length=40)
    num = IntField()


sd = SimpleDoc()
sd.title = 'simple doc'
sd.num = 1998
sd.id = ObjectId()
print 'SimpleDoc:', sd.to_python()

print 'Validating SimpleDoc instance'
sd.validate()
print 'Validation passed'


###
### Subclass decorated object to show inheritance works fine
###

class ComplexDoc(SimpleDoc):
    body = StringField()


cd = ComplexDoc()
cd.title = 'complex title'
cd.num = 1996
cd.id = ObjectId()
print 'ComplexDoc:', cd.to_python()
print 'ComplexDoc JSON:', cd.to_json()
print 'ComplexDoc ownersafe:', ComplexDoc.make_ownersafe(cd)

print 'Validating ComplexDoc instance'
cd.validate()
print 'Validation passed'
