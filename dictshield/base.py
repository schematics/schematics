#!/usr/bin/env python

"""This module puts the basic framework for the Document and it's Metaclass
together. The Metaclass attribute `_fields`_ informs the validation system
about *what* to validate. `_fields` is also used for mapping inputs and outputs
to corresponding members of the Document, fascilitating easy document
validating like:

    d = Document(**key_map)
    try:
        d.validate()
    except:
        handler_validation_fail()

It also provides the basic framework for throwing errors when input doesn't
match expected patterns, as we see with the exception handling.

A `ShieldException` is thrown when validation fails.

An `InvalidShield` exception is thrown when the input data can't be mapped
to a `Document`.
"""

### If you're using Python 2.6, you should use simplejson
try:
    import simplejson as json
except:
    import json


###
### Exceptions
###

class InvalidShield(Exception):
    """A shield has been put together incorrectly
    """
    pass


class ShieldException(Exception):
    """The field did not pass validation.
    """
    def __init__(self, reason, field_name, field_value, *args, **kwargs):
        super(ShieldException, self).__init__(*args, **kwargs)
        self.reason = reason
        self.field_name = field_name
        self.field_value = field_value

    def __str__(self):
        return '%s - %s:%s' % (self.reason, self.field_name, self.field_value)

# Here from my younger, less venerable days.
DictPunch = ShieldException


def subclass_exception(name, parents, module):
    return type(name, parents, {'__module__': module})
