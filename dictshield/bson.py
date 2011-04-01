#!/usr/bin/env python

"""This module offers functionality for working with MongoDB
"""

import bson
from base import BaseField, DictPunch

class ObjectIdField(BaseField):
    """An field wrapper around MongoDB ObjectIds.
    """

    def to_python(self, value):
        try:
            return bson.objectid.ObjectId(unicode(value))
        except Exception, e:
            raise InvalidShield(unicode(e))
        return str(value)

    def to_json(self, value):
        return str(value)

    def validate(self, value):
        try:
            bson.objectid.ObjectId(unicode(value))
        except:
            raise DictPunch('Invalid Object ID')
