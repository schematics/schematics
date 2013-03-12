# -*- coding: utf-8 -*-
import copy
import unittest
import datetime

from schematics.models import Model
from schematics.types.base import *
from schematics.validation import validate_instance
from schematics.serialize import to_json, to_python
from schematics.exceptions import ValidationError


class TestStringType(unittest.TestCase):

    class User(Model):
        name = StringType()

    def testEmptyUser(self):
        user = self.User()
        user.name = "Ryan"
        self.assertEqual(user.name, "Ryan")
        self.assertTrue(isinstance(user.name, unicode))
        assert validate_instance(user)

    def testUserWithName(self):
        user = self.User(name="Ryan")
        self.assertEqual(user.name, "Ryan")
        self.assertTrue(isinstance(user.name, unicode))
        assert validate_instance(user)

class TestIntType(unittest.TestCase):

    class User(Model):
        age = IntType()

    def testEmptyUser(self):
        user = self.User()
        user.age = 34
        self.assertEqual(user.age, 34)
        self.assertTrue(isinstance(user.age, int))
        assert validate_instance(user)

    def testUserWithIntAge(self):
        user = self.User(age=34)
        self.assertEqual(user.age, 34)
        self.assertTrue(isinstance(user.age, int))
        assert validate_instance(user)

    def testUserWithStringAge(self):
        user = self.User(age="34")
        self.assertEqual(user.age, 34)
        self.assertTrue(isinstance(user.age, int))
        assert validate_instance(user)

class TestDateTimeType(unittest.TestCase):

    class TestModel(Model):
        datetime = DateTimeType()
        date = DateType()
        time = TimeType()

    def testBasicDateTime(self):
        test = self.TestModel()
        test.datetime = datetime.datetime.utcnow()
        self.assertTrue(isinstance(test.datetime, datetime.datetime))
        test.date = test.datetime.date()
        test.time = test.datetime.time()
        validate_instance(test)

    def testDateType(self):
        test = self.TestModel()
        test.date = "2013-02-20"
        validate_instance(test)
        test.date = u"2013-02-20"

    def testDateTypeWithFormat(self):
        class TestModel(Model):
            iso_date = DateType()
            usa_date = DateType(format="%m/%d/%Y")
        test = TestModel()
        test.iso_date = "2013-02-20"
        test.usa_date = "02/20/2013"
        self.assertEqual(test.iso_date,test.usa_date)

    def testTimeType(self):
        test = self.TestModel()
        test.time = "1:15 PM"
        validate_instance(test)

    def testTimeTypeWithFormat(self):
        class TestModel(Model):
            iso_time = TimeType(format="%H:%M")
            usa_time = TimeType()
        test = TestModel()
        test.iso_time = "13:15"
        test.usa_time = "1:15 PM"
        self.assertEqual(test.iso_time, test.usa_time)
        try:
            test.usa_time = "9:15"
            self.fail("ValueError expected")
        except ValueError:
            pass
        test.usa_time = "9:15 AM"
        test.iso_time = "9:15"
        self.assertEqual(test.iso_time, test.usa_time)

class TestIPv4Type(unittest.TestCase):
    class Test(Model):
        ip = IPv4Type()

    def testValidIP(self):
        test = self.Test()
        test.ip = '8.8.8.8'
        assert validate_instance(test)

    def testInvalidIPAddresses(self):
        fun = lambda: validate_instance(self.Test(ip='1.1.1.1.1'))
        self.assertRaises(ValidationError, fun)
        
        fun = lambda: validate_instance( self.Test(ip='1.1.11') )
        self.assertRaises(ValidationError, fun)
        
        fun = lambda: validate_instance( self.Test(ip='1.1.1111.1') )
        self.assertNotEqual(ValidationError, fun)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStringType, 'test'))
    suite.addTest(unittest.makeSuite(TestIntType, 'test'))
    suite.addTest(unittest.makeSuite(TestDateTimeType, 'test'))
    suite.addTest(unittest.makeSuite(TestIPv4Type, 'test'))
    return suite


if __name__ == '__main__':
   unittest.main(defaultTest='suite')
