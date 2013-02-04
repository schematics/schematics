import unittest
from schematics.tests import test_base_types, test_list_type, test_validation

def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_base_types.suite())
    suite.addTest(test_list_type.suite())
    suite.addTest(test_validation.suite())
    return suite

if __name__ == '__main__':
   unittest.main(defaultTest='suite')
