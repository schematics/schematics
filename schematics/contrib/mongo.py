"""This module contains fields that depend on importing `bson`. `bson` is
a part of the pymongo distribution.
"""

import bson  # type: ignore

from ..exceptions import ConversionError
from ..translator import _
from ..types import BaseType

__all__ = ["ObjectIdType"]


class ObjectIdType(BaseType):

    """An field wrapper around MongoDB ObjectIds.  It is correct to say they're
    bson fields, but I am unaware of bson being used outside MongoDB.

    `auto_fill` is disabled by default for ObjectIdType's as they are
    typically obtained after a successful save to Mongo.
    """

    MESSAGES = {
        "convert": _("Couldn't interpret value as an ObjectId."),
    }

    def __init__(self, auto_fill=False, **kwargs):
        self.auto_fill = auto_fill
        super().__init__(**kwargs)

    def to_native(self, value, context=None):
        if not isinstance(value, bson.objectid.ObjectId):
            try:
                value = bson.objectid.ObjectId(str(value))
            except bson.objectid.InvalidId as exc:
                raise ConversionError(self.messages["convert"]) from exc
        return value

    def to_primitive(self, value, context=None):
        return str(value)
