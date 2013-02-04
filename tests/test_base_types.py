
import copy
import unittest
import datetime

from schematics.models import Model
from schematics.types.base import *
from schematics.validation import validate_instance
from schematics.serialize import to_json, to_python

class TestStringType(unittest.TestCase):

    class User(Model):
        name = StringType()

    def testEmptyUser(self):
        user = self.User()
        user.name = "Ryan"
        self.assertEqual(user.name, "Ryan")
        self.assertTrue(isinstance(user.name, unicode))
        result = validate_instance(user)
        self.assertEqual(result.tag, 'OK')

    def testUserWithName(self):
        user = self.User(name="Ryan")
        self.assertEqual(user.name, "Ryan")
        self.assertTrue(isinstance(user.name, unicode))
        result = validate_instance(user)
        self.assertEqual(result.tag, 'OK')

class TestIntType(unittest.TestCase):

    class User(Model):
        age = IntType()

    def testEmptyUser(self):
        user = self.User()
        user.age = 34
        self.assertEqual(user.age, 34)
        self.assertTrue(isinstance(user.age, int))
        result = validate_instance(user)
        self.assertEqual(result.tag, 'OK')

    def testUserWithIntAge(self):
        user = self.User(age=34)
        self.assertEqual(user.age, 34)
        self.assertTrue(isinstance(user.age, int))
        result = validate_instance(user)
        self.assertEqual(result.tag, 'OK')

    def testUserWithStringAge(self):
        user = self.User(age="34")
        self.assertEqual(user.age, 34)
        self.assertTrue(isinstance(user.age, int))
        result = validate_instance(user)
        self.assertEqual(result.tag, 'OK')

class TestDateTimeType(unittest.TestCase):

    class User(Model):
        joined_on = DateTimeType()

    def testEmptyUser(self):
        user = self.User()
        user.joined_on = datetime.datetime.utcnow()
        self.assertTrue(isinstance(user.joined_on, datetime.datetime))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStringType, 'test'))
    suite.addTest(unittest.makeSuite(TestIntType, 'test'))
    suite.addTest(unittest.makeSuite(TestDateTimeType, 'test'))
    return suite

if __name__ == '__main__':
   unittest.main(defaultTest='suite')
