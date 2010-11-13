#!/usr/bin/env python

from dictshield.document import *
from dictshield.fields import *

class User(Document):
    _private_fields = ['secret']
    _public_fields = ['name']
    
    secret = MD5Field()
    name = StringField(required=True, max_length=50)
    bio = StringField(max_length=100)
    
u = User()
u.secret = 'whatevz'
u.name = 'test hash'

print 'Attempting first validation...'
try:
    u.validate()
except DictPunch, dp:
    print('  DictPunch caught: %s\n' % (dp))
    

print 'Fixing data and trying validation again...'
u.secret = 'e8b5d682452313a6142c10b045a9a135'
u.validate()
print '  Validated!\n'


total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    #'secret': 'not an md5. not even close.',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_field': 'MWAHAHA',
}

print 'Validating:\n\n    %s\n' % (total_input)
valid_fields = User.check_class_fields(total_input)

if valid_fields:
    print 'Remove rogue field by building a DictShield Document'
    user_doc = User(**total_input).to_mongo()
    print user_doc
    print '  Document:\n    %s' % (user_doc)
    safe_doc = User.make_json_safe(user_doc)
    print '  Safe doc:\n    %s' % (safe_doc)
    public_safe_doc = User.make_json_publicsafe(safe_doc)
    print '  Public safe doc:\n    %s\n' % (public_safe_doc)
else:
    raise DictPunch('Failed validation!')


