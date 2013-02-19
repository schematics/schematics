import unittest

from schematics.models import Model
from schematics.forms import Form
from schematics.types.base import *
from schematics.validation import validate_instance
from schematics.serialize import to_json, to_python
from schematics.wtf import model_form

class Test(Model):
    n = StringType()
    i = IntType()

class TestForms(unittest.TestCase):

    def testForm(self):

        f = Form(Test)
        print f.as_p()

class TestWTForms(unittest.TestCase):

    def testMakeForm(self):
        f = model_form(Test())
        print vars(f)

if __name__ == '__main__':
   unittest.main()
