#!/usr/bin/env python

import copy
import unittest
import json

from schematics.models import Model
from schematics.types import  IntType, StringType
from schematics.types.compound import SortedListType, ModelType, ListType
from schematics.serialize import (to_python, wholelist, make_safe_json,
                                  make_safe_python)
from schematics.validation import validate_instance


class TestSetGetSingleScalarData(unittest.TestCase):
    def setUp(self):
        self.listtype = ListType(IntType())
        
        class TestModel(Model):
            the_list = self.listtype
            class Options:
                roles = {
                    'owner': wholelist(),
                }
            
        self.Testmodel = TestModel
        self.testmodel = TestModel()

    def test_good_value_for_python(self):
        self.testmodel.the_list = [2]
        self.assertEqual(self.testmodel.the_list, [2])

    def test_single_bad_value_for_python(self):
        self.testmodel.the_list = 2
        # since no validation happens, nothing should yell at us        
        self.assertEqual(self.testmodel.the_list, 2) 

    def test_collection_good_values_for_python(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        self.assertEqual(self.testmodel.the_list, [2,2,2,2,2,2])

    def test_collection_bad_values_for_python(self):
        expected = self.testmodel.the_list = ["2","2","2","2","2","2"]
        actual = self.testmodel.the_list
        # print validate_instance(self.testmodel)
        # since no validation happens, nothing should yell at us        
        self.assertEqual(actual, expected)  

    def test_good_value_for_json(self):
        expected = self.testmodel.the_list = [2]
        actual = self.listtype.for_json(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_for_json(self):
        expected = self.testmodel.the_list = [2,2,2,2,2,2]
        actual = self.listtype.for_json(self.testmodel.the_list)
        self.assertEqual(actual, expected)

    def test_good_values_into_json(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        actual = make_safe_json(self.Testmodel, self.testmodel, 'owner')
        expected = json.dumps({"the_list":[2,2,2,2,2,2]})
        self.assertEqual(actual, expected)

    def test_good_value_into_json(self):
        self.testmodel.the_list = [2]
        actual = make_safe_json(self.Testmodel, self.testmodel, 'owner')
        expected = json.dumps({"the_list":[2]})
        self.assertEqual(actual, expected)

    def test_good_value_validates(self):
        self.testmodel.the_list = [2,2,2,2,2,2]
        result = validate_instance(self.testmodel)
        self.assertEqual(result.tag, 'OK')

    def test_coerceible_value_passes_validation(self):
        self.testmodel.the_list = ["2","2","2","2","2","2"]
        result = validate_instance(self.testmodel)
        self.assertEqual(result.tag, 'OK')

    def test_uncoerceible_value_passes_validation(self):
        self.testmodel.the_list = ["2","2","2","2","horse","2"]
        result = validate_instance(self.testmodel)
        self.assertNotEqual(result.tag, 'OK')
        
    def test_validation_converts_value(self):
        self.testmodel.the_list = ["2","2","2","2","2","2"]
        result = validate_instance(self.testmodel)
        self.assertEqual(result.tag, 'OK')
        converted_data = result.value
        new_list = converted_data['the_list']
        self.assertEqual(new_list, [2,2,2,2,2,2])

        
class TestGetSingleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestmodel(Model):
            bandname = StringType()
            
        self.embedded_test_model = EmbeddedTestmodel
        self.embedded_type = ModelType(EmbeddedTestmodel)
        
        class Testmodel(Model):
            the_list = ListType(self.embedded_type)
            
        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_list = [{'bandname': 'fugazi'}]
        from_testmodel = self.testmodel.the_list[0]
        new_embedded_test = self.embedded_test_model()
        new_embedded_test['bandname'] = 'fugazi'
        self.assertEqual(from_testmodel, new_embedded_test)


class TestMultipleEmbeddedData(unittest.TestCase):
    def setUp(self):
        class EmbeddedTestmodel(Model):
            bandname = StringType()
            
        class SecondEmbeddedTestmodel(Model):
            food = StringType()
            
        self.embedded_test_document = EmbeddedTestmodel
        self.second_embedded_test_document = EmbeddedTestmodel
        
        self.embedded_type = ModelType(EmbeddedTestmodel)
        self.second_embedded_type = ModelType(SecondEmbeddedTestmodel)

        class Testmodel(Model):
            the_doc = ListType([self.embedded_type, self.second_embedded_type])

        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    @unittest.expectedFailure #because the set shouldn't upcast until validation
    def test_good_value_for_python_upcasts(self):
        self.testmodel.the_doc = [{'bandname': 'fugazi'}, {'food':'cake'}]
        actual = self.testmodel.the_doc
        embedded_test_one = self.embedded_test_document()
        embedded_test_one['bandname'] = 'fugazi'
        embedded_test_two = self.second_embedded_test_document()
        embedded_test_two['food'] = 'cake'
        expected = [embedded_test_one, embedded_test_two]
        self.assertEqual(actual, expected)
        

class TestSetGetSingleScalarDataSorted(unittest.TestCase):
    def setUp(self):
        self.listtype = SortedListType(IntType())
        
        class Testmodel(Model):
            the_list = self.listtype
            
        self.Testmodel = Testmodel
        self.testmodel = Testmodel()

    def test_collection_good_values_for_python(self):
        expected = self.testmodel.the_list = [1,2,3,4,5,6]
        self.assertEqual(self.testmodel.the_list, expected)

    def test_collection_good_values_for_python_gets_sorted(self):
        expected = self.testmodel.the_list = [6,5,4,3,2,1]
        expected = copy.copy(expected)
        expected.reverse()
        actual = to_python(self.testmodel)['the_list']
        self.assertEqual(actual, expected)

class TestListTypeProxy(unittest.TestCase):

    def setUp(self):
        self.listtype = ListType(IntType())
        class TestModel(Model):
            the_list = self.listtype
        self.TestModel = TestModel
        self.testmodel = TestModel()

    def testEmptyList(self):
        assert isinstance(self.testmodel.the_list, ListType.Proxy)

    def testProxyAppend(self):
        self.testmodel.the_list = [1,2]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        self.testmodel.the_list.append(3)
        self.assertEqual( len(self.testmodel.the_list), 3 )
        self.assertEqual( self.testmodel.the_list[2], 3 )

    def testProxyContains(self):
        self.testmodel.the_list = [1,2]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        self.assertTrue(1 in self.testmodel.the_list)

    def testProxyCount(self):
        self.testmodel.the_list = [1,2]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        self.assertEqual(0, self.testmodel.the_list.count(3))
        self.assertEqual(1, self.testmodel.the_list.count(1))

    def testProxyIndex(self):
        self.testmodel.the_list = [1,2]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        self.assertEqual(0, self.testmodel.the_list.index(1))
        self.assertRaises(ValueError, self.testmodel.the_list.index, 3)
     
    def testProxyRemove(self):
        self.testmodel.the_list = [1, 2]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        self.testmodel.the_list.remove(1)
        self.assertEqual( len(self.testmodel.the_list), 1 )

    def testProxyIter(self):
        self.testmodel.the_list = [1, 2]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        # TODO - load from db, test type from list

    def testProxyPop(self):
        self.testmodel.the_list = [1, 2]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        self.assertEqual(self.testmodel.the_list.pop(), 2) 
        self.assertEqual(len(self.testmodel.the_list), 1)

    def testProxySlice(self):
        self.testmodel.the_list = [1, 2, 3, 4, 5, 6]
        assert isinstance(self.testmodel.the_list, ListType.Proxy)
        ll = self.testmodel.the_list[1:3]
        self.assertEqual(len(ll), 2)
        self.assertEqual(ll[0], 2)
        self.testmodel.the_list[2:4] = [ i for i in range(6,8) ]
        self.assertEqual(self.testmodel.the_list[2], 6)
        del self.testmodel.the_list[3:]
        self.assertEqual(len(self.testmodel.the_list),3)

def suite():
    suite = unittest.TestSuite()
    return suite

if __name__ == '__main__':
    unittest.main()
