# -*- coding: utf-8 -*-
import copy
import unittest
import datetime

from schematics.models import Model
from schematics.types.base import *
from schematics.validation import validate
from schematics.serialize import to_json, to_python
from schematics.exceptions import ValidationError


class TestIPv4Type(unittest.TestCase):
    class Test(Model):
        ip = IPv4Type()

    def testValidIP(self):
        test = self.Test()
        test.ip = '8.8.8.8'
        test.validate(test)

    def testInvalidIPAddresses(self):
        fun = lambda: self.Test(ip='1.1.1.1.1').validate()
        self.assertRaises(ValidationError, fun)
        
        fun = lambda: self.Test(ip='1.1.11').validate()
        self.assertRaises(ValidationError, fun)
        
        fun = lambda: self.Test(ip='1.1.1111.1').validate()
        self.assertNotEqual(ValidationError, fun)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIPv4Type, 'test'))
    return suite


if __name__ == '__main__':
   unittest.main(defaultTest='suite')
