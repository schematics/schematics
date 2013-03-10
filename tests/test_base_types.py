# -*- coding: utf-8 -*-
import copy
import unittest
import datetime

from schematics.models import Model
from schematics.types.base import *
from schematics.validation import validate_instance
from schematics.serialize import to_json, to_python
from schematics.exceptions import ValidationError


class TestIPv4Type(unittest.TestCase):
    class Test(Model):
        ip = IPv4Type()

    def testValidIP(self):
        test = self.Test()
        test.ip = '8.8.8.8'
        validate_instance(test)

    def testInvalidIPAddresses(self):
        fun = lambda: validate_instance(self.Test(ip='1.1.1.1.1'))
        self.assertRaises(ValidationError, fun)
        
        fun = lambda: validate_instance( self.Test(ip='1.1.11') )
        self.assertRaises(ValidationError, fun)
        
        fun = lambda: validate_instance( self.Test(ip='1.1.1111.1') )
        self.assertNotEqual(ValidationError, fun)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIPv4Type, 'test'))
    return suite


if __name__ == '__main__':
   unittest.main(defaultTest='suite')
