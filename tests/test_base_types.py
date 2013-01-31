
import copy
import unittest

from schematics.models import Model
from schematics.types.base import *
from schematics.validation import validate_instance

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


if __name__ == '__main__':
   unittest.main()
