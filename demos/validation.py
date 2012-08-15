#!/usr/bin/env python


"""Attempting validation on:

    {"_types": ["User"], "secret": "whatevz", "name": "test hash", "_cls": "User"}

TypeException caught: MD5 value is wrong length - secret:whatevz

Adjusted invalid data and trying again on:

    {"_types": ["User"], "secret": "34165b7d7c2d95bbecd41c05c19379c4", "name": "test hash", "_cls": "User"}

Validation passed

Attempting validation on:

    {'rogue_type': 'MWAHAHA', 'bio': 'J2D2 loves music', 'secret': 'e8b5d682452313a6142c10b045a9a135', 'name': 'J2D2'}

Validation passed
After validation:

    {'bio': 'J2D2 loves music', 'secret': 'e8b5d682452313a6142c10b045a9a135', 'name': 'J2D2'}

Validation passed

Model as Python:
    {'_types': ['User'], 'bio': u'J2D2 loves music', 'secret': 'e8b5d682452313a6142c10b045a9a135', 'name': u'J2D2', '_cls': 'User'}

Owner safe:
    {"bio": "J2D2 loves music", "secret": "e8b5d682452313a6142c10b045a9a135", "name": "J2D2"}

Public safe:
    {"bio": "J2D2 loves music", "name": "J2D2"}
"""


from structures.base import TypeException
from structures.models import Model
from structures.types import MD5Type, StringType
import hashlib


###
### Basic User model
###

class User(Model):
    _public_fields = ['name', 'bio']
    
    secret = MD5Type()
    name = StringType(required=True, max_length=50)
    bio = StringType(max_length=100)

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
print 'Attempting validation on:\n\n    %s\n' % (u.to_json())
try:
    u.validate()
    print 'Validation passed\n'
except TypeException, se:
    print 'TypeException caught: %s\n' % (se)
    

### Set the password *correctly* using our `set_password` function
u.set_password('whatevz')
print 'Adjusted invalid data and trying again on:\n\n    %s\n' % (u.to_json())
try:
    u.validate()
    print 'Validation passed\n'
except TypeException, se:
    print 'TypeException caught: %s (This section wont actually run)\n' % (se)


###
### Instantiate an instance with this data
###
 
total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_type': 'MWAHAHA',
}

### Checking for any failure. Exception thrown on first failure.
print 'Attempting validation on:\n\n    %s\n' % (total_input)
try:
    User.validate_class_fields(total_input)
    print 'Validation passed'
except TypeException, se:
    print('TypeException caught: %s' % (se))
print 'After validation:\n\n    %s\n' % (total_input)


### Check all types and collect all failures
exceptions = User.validate_class_fields(total_input, validate_all=True)

if len(exceptions) == 0:
    print 'Validation passed\n'
else:
    print '%s exceptions found\n\n    %s\n' % (len(exceptions),
                                               [str(e) for e in exceptions])


###
### Type Security
###

# Add the rogue type back to `total_input`
total_input['rogue_type'] = 'MWAHAHA'

user_doc = User(**total_input)
print 'Model as Python:\n    %s\n' % (user_doc.to_python())
safe_doc = User.make_json_ownersafe(user_doc)
print 'Owner safe doc:\n    %s\n' % (safe_doc)
public_safe_doc = User.make_json_publicsafe(user_doc)
print 'Public safe doc:\n    %s\n' % (public_safe_doc)

