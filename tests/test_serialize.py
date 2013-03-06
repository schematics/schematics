
import unittest

from schematics.models import Model
from schematics.serialize import serializable
from schematics.types import StringType


class TestSerializable(unittest.TestCase):

    def test_serializable(self):
        class Location(Model):
            country_code = StringType()

            @serializable
            def country_name(self):
                return "United States" if self.country_code == "US" else "Unknown"

        location_US = Location(country_code="US")
        print Location.__dict__

        self.assertEqual(location_US.country_name, "United States")

        d = location_US.serialize()
        self.assertEqual(d, {"country_code": "US", "country_name": "United States"})

        location_IS = Location(country_code="IS")

        self.assertEqual(location_IS.country_name, "Unknown")

        d = location_IS.serialize()
        self.assertEqual(d, {"country_code": "IS", "country_name": "Unknown"})

    def test_serializable_with_serializable_name(self):
        class Location(Model):
            country_code = StringType(serialized_name="cc")

            @serializable(serialized_name="cn")
            def country_name(self):
                print "Country code", self._data, self.country_code
                return "United States" if self.country_code == "US" else "Unknown"

        location_US = Location(country_code="US")

        self.assertEqual(location_US.country_name, "United States")

        d = location_US.serialize()
        self.assertEqual(d, {"cc": "US", "cn": "United States"})
