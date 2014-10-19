"""This module contains fields that depend on importing `bson`. `bson` is
a part of the pymongo distribution.
"""

from schematics.types import BaseType
from schematics.exceptions import ConversionError, ValidationError

import bson

try:
    unicode #PY2
except:
    import codecs
    unicode = str #PY3

class ObjectIdType(BaseType):

    """An field wrapper around MongoDB ObjectIds.  It is correct to say they're
    bson fields, but I am unaware of bson being used outside MongoDB.

    `auto_fill` is disabled by default for ObjectIdType's as they are
    typically obtained after a successful save to Mongo.
    """

    MESSAGES = {
        'convert': u"Couldn't interpret value as an ObjectId.",
    }

    def __init__(self, auto_fill=False, **kwargs):
        self.auto_fill = auto_fill
        super(ObjectIdType, self).__init__(**kwargs)

    def to_native(self, value, context=None):
        if not isinstance(value, bson.objectid.ObjectId):
            try:
                value = bson.objectid.ObjectId(unicode(value))
            except bson.objectid.InvalidId:
                raise ConversionError(self.messages['convert'])
        return value

    def to_primitive(self, value, context=None):
        return str(value)

    def validate_id(self, value):
        if not isinstance(value, bson.objectid.ObjectId):
            try:
                value = bson.objectid.ObjectId(unicode(value))
            except Exception:
                raise ValidationError('Invalid ObjectId')
        return True
