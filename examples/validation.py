#!/usr/bin/env python

from dictshield.document import *
from dictshield.fields import *

print '--------------------------------------------'
print 'Creating a User document and show validation'
print '--------------------------------------------\n'

class User(Document):
    _public_fields = ['name']
    
    secret = MD5Field()
    name = StringField(required=True, max_length=50)
    bio = StringField(max_length=100)
    
u = User()
u.secret = 'whatevz'
u.name = 'test hash'

print '  Attempting validation on:\n\n    %s\n' % (u.to_mongo())
try:
    u.validate()
    print ' Validation passed\n'
except DictPunch, dp:
    print '  DictPunch caught: %s\n' % (dp)
    

u.secret = 'e8b5d682452313a6142c10b045a9a135'
print '  Adjusted invalid data and trying again on:\n\n    %s\n' % (u.to_mongo())
try:
    u.validate()
    print '  Validation passed\n'
except DictPunch, dp:
    print '  DictPunch caught: %s\n' % (dp)

print '----------------------------------------------------------------'
print 'Converting a Python dictionary to a User document for validation'
print '----------------------------------------------------------------\n'

total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    #'secret': 'not an md5. not even close.',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_field': 'MWAHAHA',
}

print '  Attempting validation on:\n\n    %s\n' % (total_input)
print '  Checking for *any* exceptions: ',
try:
    User.validate_class_fields(total_input)
    print 'Validation passed'
except DictPunch, dp:
    print('DictPunch caught: %s' % (dp))

print '  Checking for *every* exception: ', 
exceptions = User.validate_class_fields(total_input, validate_all=True)

if len(exceptions) == 0:
    print 'Validation passed\n'
else:
    print '%s exceptions found\n\n    %s\n' % (len(exceptions),
                                               [str(e) for e in exceptions])

user_doc = User(**total_input).to_mongo()
print '  Document:\n    %s\n' % (user_doc)
safe_doc = User.make_json_ownersafe(user_doc)
print '  Owner safe doc:\n    %s\n' % (safe_doc)
public_safe_doc = User.make_json_publicsafe(safe_doc)
print '  Public safe doc:\n    %s\n' % (public_safe_doc)

