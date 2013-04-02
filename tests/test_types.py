
import unittest
import datetime

from schematics.types import (
    StringType, DateTimeType, DateType, IntType, EmailType
)
from schematics.exceptions import ValidationError, StopValidation


class TestType(unittest.TestCase):

    def test_required(self):
        with self.assertRaises(ValidationError):
            StringType(required=True)(None)
        self.assertEqual(StringType()(None), None)

    def test_date(self):
        today = datetime.date(2013, 3, 1)

        date_type = DateType()
        self.assertEqual(date_type("2013-03-01"), today)

        self.assertEqual(date_type.to_primitive(today), "2013-03-01")

    def test_datetime(self):
        dt = datetime.datetime.now()
        self.assertEqual(DateTimeType()(dt.isoformat()), dt)

    def test_datetime_format(self):
        input = '2013.03.07 15:31'
        dt = datetime.datetime(2013, 3, 7, 15, 31)
        self.assertEqual(DateTimeType(formats=['%Y.%m.%d %H:%M'])(input), dt)

    def test_datetime_primitive(self):
        output = '2013.03.07 15:31'
        dt = datetime.datetime(2013, 3, 7, 15, 31)
        dt_type = DateTimeType(serialized_format='%Y.%m.%d %H:%M')
        self.assertEqual(dt_type(dt.isoformat()), dt)
        self.assertEqual(dt_type.to_primitive(dt), output)

    def test_datetime_accepts_datetime(self):
        output = '2013.03.07 15:31'
        dt = datetime.datetime(2013, 3, 7, 15, 31)
        dt_type = DateTimeType(serialized_format='%Y.%m.%d %H:%M')
        self.assertEqual(dt_type(dt), dt)
        self.assertEqual(dt_type.to_primitive(dt), output)

    def test_string(self):
        with self.assertRaises(ValidationError):
            StringType(required=True)('')
        with self.assertRaises(ValidationError):
            StringType(min_length=1)('')

    def test_string_regex(self):
        self.assertEqual(StringType(regex='\d+')("1"), "1")
        with self.assertRaises(ValidationError):
            StringType(regex='\d+')("a")

    def test_int(self):
        with self.assertRaises(ValidationError):
            IntType()('a')
        self.assertEqual(IntType()(1), 1)

    def test_email_type_with_invalid_email(self):
        with self.assertRaises(StopValidation):
            EmailType().convert(u'sdfg\U0001f636\U0001f46e')

        with self.assertRaises(ValidationError):
            EmailType()(u'sdfg\U0001f636\U0001f46e')
