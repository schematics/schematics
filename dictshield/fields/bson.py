"""This module contains fields that depend on importing `bson`. `bson` is
as part of the pymongo distribution.
"""

from dictshield.base import BaseField, ShieldException

import bson

class ObjectIdField(BaseField):
    """An field wrapper around MongoDB ObjectIds.  It is correct to say they're
    bson fields, but I am unaware of bson being used outside MongoDB.
    """

    def _jsonschema_type(self):
        return 'string'

    def to_python(self, value):
        try:
            return bson.objectid.ObjectId(unicode(value))
        except Exception, e:
            raise InvalidShield(unicode(e))

    def for_json(self, value):
        return str(value)

    def validate(self, value):
        try:
            bson.objectid.ObjectId(unicode(value))
        except Exception, e:
            raise ShieldException('Invalid ObjectId', self.field_name, value)
