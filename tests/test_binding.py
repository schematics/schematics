# -*- coding: utf-8 -*-
import pytest

from schematics.models import Model
from schematics.types.base import StringType
from schematics.types.compound import ListType, ModelType
from schematics.types.serializable import serializable
from schematics.exceptions import ValidationError


def test_reason_why_we_must_bind_fields():
    class Person(Model):
        name = StringType(required=True)

    p1 = Person()
    p2 = Person()

    assert p1 == p2
    assert id(p1) != id(p2)

    assert p1.name == p2.name
    assert id(p1.name) == id(p2.name)

    p1.name = "Jóhann"
    p1.validate()
    with pytest.raises(ValidationError):
        p2.validate()

    assert p1 != p2
    assert id(p1) != id(p2)
    assert p1.name != p2.name
    assert id(p1.name) != id(p2.name)

    assert id(p1._fields["name"]) == id(p2._fields["name"])


def test_reason_why_we_must_bind_fields_model_field():
    class Location(Model):
        country_code = StringType(required=True)

    class Person(Model):
        location = ModelType(Location)

    p1 = Person()
    p2 = Person()

    assert p1 == p2
    assert id(p1) != id(p2)

    assert p1.location == p2.location
    assert id(p1.location) == id(p2.location)

    p1.location = {"country_code": "us"}
    assert p1.location.country_code == "us"

    p2.location = {}

    with pytest.raises(ValidationError):
        p2.validate()

    assert p1 != p2
    assert id(p1) != id(p2)
    assert p1.location != p2.location
    assert id(p1.location) != id(p2.location)

    assert id(p1._fields["location"]) == id(p2._fields["location"])


def test_field_binding():
    class Person(Model):
        name = StringType(required=True)

    class Course(Model):
        id = StringType(required=True, validators=[])
        attending = ListType(ModelType(Person))

    class School(Model):
        courses = ListType(ModelType(Course))

    valid_data = {
        'courses': [
            {'id': 'ENG103', 'attending': [
                {'name': u'Danny'},
                {'name': u'Sandy'}]},
            {'id': 'ENG203', 'attending': [
                {'name': u'Danny'},
                {'name': u'Sandy'}
            ]}
        ]
    }

    new_school = School(valid_data)
    new_school.validate()

    school = School(valid_data)
    school.validate()

    assert id(new_school) != id(school)

    assert id(new_school.courses[0].attending[0]) != id(school.courses[0].attending[0])


def test_serializable_doesnt_keep_global_state():
    class Location(Model):
        country_code = StringType()

        @serializable
        def country_name(self):
            return "United States" if self.country_code == "US" else "Unknown"

    location_US = Location({"country_code": "US"})
    location_IS = Location({"country_code": "IS"})

    assert id(location_US._serializables["country_name"]) == id(
        location_IS._serializables["country_name"])
