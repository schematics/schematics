from schematics.models import Model
from schematics.types.path import PathType, ExecutablePathType
from schematics.validation import validate_instance
from schematics.exceptions import ValidationError

import unittest

class PathTypeTestCase(unittest.TestCase):
    def setUp(self):
        import platform
        if platform.system() in ('Microsoft', 'Windows'):
            self.skipTest("cannot test on a non-UNIX platform")

    def test_path_exists(self):
        class Foo(Model):
            path = PathType(exists=True)

        foo = Foo(path="/tmp")
        validate_instance(foo)
        
        foo.path = "/tmp/this_file_doesnt_exist_with_some_random_digits_13467487681356573"
        fun = lambda: validate_instance(foo)
        self.assertRaises(ValidationError, fun)
        
            
    def test_path_isdir(self):
        class Foo(Model):
            path = PathType(isdir=True)

        foo = Foo(path="/tmp")
        validate_instance(foo)

        foo.path = "/etc/hosts"
        fun = lambda: validate_instance(foo)
        self.assertRaises(ValidationError, fun)
        

    def test_path_isfile(self):
        class Foo(Model):
            path = PathType(isfile=True)

        foo = Foo(path="/etc/hosts")
        validate_instance(foo)

        foo.path = "/tmp"
        fun = lambda: validate_instance(foo)
        self.assertRaises(ValidationError, fun)


    def test_path__can_create_or_write(self):
        class Foo(Model):
            path = PathType(can_create_or_write=True)

        foo = Foo(path="/tmp/file_that_doesnt_exist_but_can_be_created")
        validate_instance(foo)

        foo.path = "/tmp/dir_that_doesnt_exist/file_that_doesnt_exist"
        fun = lambda: validate_instance(foo)
        self.assertRaises(ValidationError, fun)


class ExecutablePathTestCase(unittest.TestCase):
    def setUp(self):
        import platform
        if platform.system() in ('Microsoft', 'Windows'):
            self.skipTest("cannot test on a non-UNIX platform")

    def test_path(self):
        class Foo(Model):
            path = ExecutablePathType()

        foo = Foo(path="/bin/sh")
        validate_instance(foo)

        foo.path = "/bin/file_that_doesnt_exist"
        fun = lambda: validate_instance(foo)
        self.assertRaises(ValidationError, fun)        
