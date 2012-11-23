#!/usr/bin/env python


"""
"""


from schematics.models import Model
from schematics.validation import (validate_instance, validate_class_fields,
                                   TypeResult, OK)
from schematics.serialize import (to_python, to_json, whitelist, wholelist,
                                  make_safe_python, make_safe_json)
from schematics.types import MD5Type, StringType
import hashlib


###
### Basic User model
###

class User(Model):
    secret = MD5Type()
    name = StringType(required=True, max_length=50)
    bio = StringType(max_length=100)

    class Options:
        roles = {
            'owner': wholelist(),
            'public': whitelist('name', 'bio'),
        }

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

### Validation will fail
print 'VALIDATING: %s' % (to_json(u))
result = validate_instance(u)
if result.tag == OK:
    print 'OK: %s\n' %(result.model)
else:
    print 'ERROR: %s\n' % (result.message)
    

### Set the password *correctly* and validation will pass
u.set_password('whatevz')
print 'VALIDATING: %s' % (to_json(u))
result = validate_instance(u)
if result.tag == OK:
    print 'OK: %s\n' % (result.model)
else:
    print 'ERROR: %s\n' % (result.message)


###
### Instantiate an instance with this data
###
 
total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_type': 'MWAHAHA',
}

print 'Validating: %s' % (total_input)

result = validate_class_fields(User, total_input)
if result.tag == OK:
    print 'OK: %s\n' % (result.value)
else:
    print 'ERROR: %s' % (result.message)
    print '%s exceptions: %s\n' % (len(result.value), result.model)


### Check all types and collect all failures
result = validate_class_fields(User, total_input, validate_all=True)

if result.tag == OK:
    print 'OK: %s\n' % (result.value)
else:
    print 'ERROR: %s' % (result.message)
    print '%s exceptions: %s\n' % (len(result.value), result.model)


###
### Type Security
###

# Add the rogue type back to `total_input`
total_input['rogue_type'] = 'MWAHAHA'

print 'INSTANTIATING: %s' % (total_input)
user_doc = User(**total_input)

print 'SERIALIZING: %s' % (user_doc)
print 'Python: %s' % (to_python(user_doc))
safe_doc = make_safe_json(User, user_doc, 'owner')
print 'Owner: %s' % (safe_doc)
public_safe_doc = make_safe_json(User, user_doc, 'public')
print 'Public: %s' % (public_safe_doc)

