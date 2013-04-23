#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from schematics.models import Model
from schematics.types.base import StringType
from schematics.types.compound import ListType, ModelType
from schematics.types.serializable import serializable


class TestFieldBinding(unittest.TestCase):

    def test_reason_why_we_must_bind_fields(self):
        class Person(Model):
            name = StringType(required=True)

        p1 = Person()
        p2 = Person()

        self.assertEqual(p1, p2)
        self.assertNotEqual(id(p1), id(p2))

        self.assertEqual(p1.name, p2.name)
        self.assertEqual(id(p1.name), id(p2.name))

        p1.validate({"name": u"Jóhann"}, raises=False)
        p2.validate(raises=False)

        self.assertNotEqual(p1, p2)
        self.assertNotEqual(id(p1), id(p2))
        self.assertNotEqual(p1.name, p2.name)
        self.assertNotEqual(id(p1.name), id(p2.name))

        self.assertEqual(id(p1._fields["name"]), id(p2._fields["name"]))

        self.assertFalse(p1.errors)
        self.assertTrue(p2.errors)

    def test_reason_why_we_must_bind_fields_model_field(self):
        class Location(Model):
            country_code = StringType(required=True)

        class Person(Model):
            location = ModelType(Location)

        p1 = Person()
        p2 = Person()

        self.assertEqual(p1, p2)
        self.assertNotEqual(id(p1), id(p2))

        self.assertEqual(p1.location, p2.location)
        self.assertEqual(id(p1.location), id(p2.location))

        p1.validate({"location": {"country_code": "us"}}, raises=False)
        p2.validate({"location": {}}, raises=False)

        self.assertNotEqual(p1, p2)
        self.assertNotEqual(id(p1), id(p2))
        self.assertNotEqual(p1.location, p2.location)
        self.assertNotEqual(id(p1.location), id(p2.location))

        self.assertEqual(id(p1._fields["location"]), id(p2._fields["location"]))

        self.assertFalse(p1.errors)
        self.assertTrue(p2.errors)

    def test_field_binding(self):
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

        new_school = School()
        new_school.validate(valid_data)

        school = School()
        school.validate(valid_data)

        self.assertNotEqual(id(new_school), id(school))

        self.assertNotEqual(
            id(new_school.courses[0].attending[0]),
            id(school.courses[0].attending[0])
        )

    def test_serializable_doesnt_keep_global_state(self):
        class Location(Model):
            country_code = StringType()

            @serializable
            def country_name(self):
                return "United States" if self.country_code == "US" else "Unknown"

        location_US = Location({"country_code": "US"})
        location_IS = Location({"country_code": "IS"})

        self.assertEqual(
            id(location_US._serializables["country_name"]),
            id(location_IS._serializables["country_name"])
        )
