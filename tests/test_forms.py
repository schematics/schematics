import unittest

from schematics.models import Model
from schematics.types.base import *
from schematics.validation import validate_instance
from schematics.serialize import to_json, to_python
from schematics.wtf import model_form

from pprint import pprint

class Test(Model):
    pk = StringType(required=True)
    name = StringType()
    age = IntType()
    country = StringType(default='US', choices=['US','UK'])
    date = DateType()
    time = TimeType()

class TestWTForms(unittest.TestCase):

    def testMakeForm(self):
        f = model_form(Test())
        myform = f()
        assert 'pk' in myform
        assert 'name' in myform
        assert 'age' in myform
        assert 'date' in myform
        assert 'time' in myform
        assert 'required' in  myform.pk.flags

    def testModelFormOnly(self):
        f = model_form(Test(), only=['name', 'age'])
        myform = f()
        assert 'pk' not in myform
        assert 'name' in myform
        assert 'age' in myform
        assert 'date' not in myform
        assert 'time' not in myform
        
    def testModelFormExclude(self):
        f = model_form(Test(), exclude=['pk'])
        myform = f()
        assert 'pk' not in myform
        assert 'name' in myform
        assert 'age' in myform
        assert 'date' in myform
        assert 'time' in myform
        
    def testModelFormHidden(self):
        f = model_form(Test(), hidden=['pk'])
        myform = f()
        assert 'hidden' in unicode(myform.pk)
        
    def testModelFormWithData(self):
        f = model_form(Test(name="Dude",age=35,pk="saweet",date="2013-12-25",time="9:30 PM"), hidden=['pk'])
        myform = f()
        assert 'hidden' in unicode(myform.pk)
        assert 'Dude' in unicode(myform.name) 
        assert '35' in unicode(myform.age)
        assert 'saweet' in unicode(myform.pk)
        assert '2013-12-25' in unicode(myform.date)
        assert '9:30 PM' in  unicode(myform.time)
        assert myform.validate()

if __name__ == '__main__':
   unittest.main()
