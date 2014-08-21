"""This module contains fields that depend on importing `bson`. `bson` is
a part of the pymongo distribution.
"""

from schematics.types import BaseType
from schematics.exceptions import ConversionError, ValidationError
from schematics.transforms import to_primitive

import bson
import json


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


class DBRefType(BaseType):

    """An field wrapper around MongoDB DBRef.  It is correct to say they're
    bson fields, but I am unaware of bson being used outside MongoDB.

    `auto_fill` is disabled by default for ObjectIdType's as they are
    typically obtained after a successful save to Mongo.
    """

    MESSAGES = {
        'convert': u"Couldn't interpret value as an DBRef.",
        'required': u"Missing required fields $ref or $id",
        'convert_dict': u"Couldn't interpret value as an DBref.",
    }

    def __init__(self, auto_fill=False, **kwargs):
        self.auto_fill = auto_fill
        super(DBRefType, self).__init__(**kwargs)

    def to_native(self, value, context=None):
        if not isinstance(value, bson.dbref.DBRef):
            try:
                if not isinstance(value, dict):
                    raise ConversionError(self.messages['convert_dict'])
                else:
                    try:
                        value = bson.dbref.DBRef(
                            value["$ref"],
                            value["$id"],
                            value.get("$db", None)
                        )
                    except KeyError:
                        raise ConversionError(self.messages['required'])
            except TypeError:
                raise ConversionError(self.messages['convert'])
        return value

    def to_primitive(self, value, context=None):
        value['$id'] = ObjectIdType().to_primitive(value['$id'])
        return json.dumps(value)

    def validate_dbref(self, value):
        if not isinstance(value, bson.dbref.DBRef):
            try:
                value = bson.dbref.DBRef(
                    value["$ref"],
                    value["$id"],
                    value.get("$db", None)
                )
            except Exception:
                raise ValidationError('Invalid DBRef')
        return True

    def validate_id(self, value):
        if not isinstance(value.id, bson.objectid.ObjectId):
            try:
                value = bson.objectid.ObjectId(unicode(value.id))
            except Exception:
                raise ValidationError('Invalid ObjectId in $id')
        return True


