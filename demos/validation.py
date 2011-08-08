#!/usr/bin/env python

"""This example demonstrates some of DictShield's validation abilities.
"""

from dictshield.base import DictPunch
from dictshield.document import Document
from dictshield.fields import MD5Field, StringField
import hashlib


###
### Basic User model
###

class User(Document):
    _public_fields = ['name', 'bio']
    
    secret = MD5Field()
    name = StringField(required=True, max_length=50)
    bio = StringField(max_length=100)

    def set_password(self, plaintext):
        hash_string = hashlib.md5(plaintext).hexdigest()
        self.secret = hash_string


###
### Manually create an instance
###

### Create instance with bogus password
u = User()
u.secret = 'whatevz'
u.name = 'test hash'

### Validation will fail because u.secret does not contain an MD5 hash
print '  Attempting validation on:\n\n    %s\n' % (u.to_json())
try:
    u.validate()
    print '  Validation passed\n'
except DictPunch, dp:
    print '  DictPunch caught: %s\n' % (dp)
    

### Set the password *correctly* using our `set_password` function
u.set_password('whatevz')
print '  Adjusted invalid data and trying again on:\n\n    %s\n' % (u.to_json())
try:
    u.validate()
    print '  Validation passed\n'
except DictPunch, dp:
    print '  DictPunch caught: %s (This section wont actually run)\n' % (dp)


###
### Instantiate an instance with this data
###
 
total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_field': 'MWAHAHA',
}

### Checking for any failure. Exception thrown on first failure.
print '  Attempting validation on:\n\n    %s\n' % (total_input)
try:
    User.validate_class_fields(total_input)
    print 'Validation passed'
except DictPunch, dp:
    print('DictPunch caught: %s' % (dp))
print '  After validation:\n\n    %s\n' % (total_input)


### Check all fields and collect all failures
exceptions = User.validate_class_fields(total_input, validate_all=True)

if len(exceptions) == 0:
    print 'Validation passed\n'
else:
    print '%s exceptions found\n\n    %s\n' % (len(exceptions),
                                               [str(e) for e in exceptions])


###
### Field Security
###

# Add the rogue field back to `total_input`
total_input['rogue_field'] = 'MWAHAHA'

user_doc = User(**total_input)
print '  Document as Python:\n    %s\n' % (user_doc.to_python())
safe_doc = User.make_json_ownersafe(user_doc)
print '  Owner safe doc:\n    %s\n' % (safe_doc)
public_safe_doc = User.make_json_publicsafe(user_doc)
print '  Public safe doc:\n    %s\n' % (public_safe_doc)

