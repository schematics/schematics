#!/usr/bin/env python


"""
"""

import hashlib

from schematics.models import Model
from schematics.validation import validate
from schematics.serialize import to_python, whitelist, wholelist
from schematics.types import MD5Type, StringType
from schematics.exceptions import ValidationError


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
u.name = 'this name is going to be much, much, much too long for this field'

### Validation will fail
print 'VALIDATING: %s' % (to_python(u))
try:
    u.validate()
except ValidationError, ve:
    print '    FAILED:', ve
 

### Set the password *correctly* and validation will pass
u.name = 'J2D2'
u.set_password('whatevz')
print 'VALIDATING: %s' % (to_python(u))

### Validation will pass
u.validate()


###
### Instantiate an instance from a dict
###
 
total_input = {
    'secret': '34165b7d7c2d95bbecd41c05c19379c4',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_type': 'MWAHAHA',
}

print 'VALIDATING: %s' % (total_input)

### Validate dict against our model definition
validate(User, total_input)


### Add the rogue type back to `total_input`
total_input['rogue_type'] = 'MWAHAHA'

print 'INSTANTIATING: %s' % (total_input)
user_doc = User(**total_input)

### Observe that rogue field was tossed away via instantiation
print '       PYTHON: %s' % (to_python(user_doc))
