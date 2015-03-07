import pytest
from bson.objectid import ObjectId
from bson.dbref import DBRef
import json

from schematics.contrib.mongo import ObjectIdType, DBRefType
from schematics.exceptions import ConversionError, ValidationError

FAKE_OID = ObjectId()

class TestObjectIdClass:
    def test_to_native(self):
        oid = ObjectIdType()

        assert oid.to_native(FAKE_OID) == FAKE_OID
        assert oid.to_native(str(FAKE_OID)) == FAKE_OID

        with pytest.raises(ConversionError):
            oid.to_native('foo')


    def test_to_primitive(self):
        oid = ObjectIdType()

        assert oid.to_primitive(FAKE_OID) == str(FAKE_OID)
        assert oid.to_primitive(str(FAKE_OID)) == str(FAKE_OID)


    def test_validate_id(self):
        oid = ObjectIdType()

        assert oid.validate_id(FAKE_OID) is True
        assert oid.validate_id(str(FAKE_OID)) is True

        with pytest.raises(ValidationError):
            oid.validate_id('foo')

class TestDBRefClass:

    def test_to_native(self):
        dbref = DBRefType()

        with pytest.raises(ConversionError):
            dbref.to_native("non-dict")

        value = {
            "$ref": "ref_collection",
            "$id": FAKE_OID,
            "$db": "optional"
        }

        fake_dbref = DBRef(value["$ref"], value["$id"], value["$db"])
        assert dbref.to_native(value) == fake_dbref

        with pytest.raises(ConversionError):
            value['$ref'] = None
            dbref.to_native(value)

        with pytest.raises(ConversionError):
            value.pop("$ref")
            dbref.to_native(value)

    def test_to_primitive(self):
        dbref = DBRefType()

        value = {
            "$ref": "ref_collection",
            "$id": FAKE_OID,
            "$db": "optional"
        }

        assert dbref.to_primitive(value) == json.dumps(value)

    def test_validate_dbref(self):
        dbref = DBRefType()

        value = {
            "$ref": "ref_collection",
            "$id": FAKE_OID,
            "$db": "optional"
        }

        assert dbref.validate_dbref(value) is True

        with pytest.raises(ValidationError):
            dbref.validate_dbref('foo')

    def test_validate_id(self):
        dbref = DBRefType()

        assert dbref.validate_id(DBRef("collection", FAKE_OID)) is True

        with pytest.raises(ValidationError):
            dbref.validate_id(DBRef("collection", "NoObjectId"))

