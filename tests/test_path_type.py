from schematics.models import Model
from schematics.types.path import PathType, ExecutablePathType
from schematics.validation import validate_instance

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
        result = validate_instance(foo)
        self.assertNotEqual(result.tag, 'OK')
            

    def test_path_isdir(self):
        class Foo(Model):
            path = PathType(isdir=True)

        foo = Foo(path="/tmp")
        validate_instance(foo)

        foo.path = "/etc/hosts"
        result = validate_instance(foo)
        self.assertNotEqual(result.tag, 'OK')

    def test_path_isfile(self):
        class Foo(Model):
            path = PathType(isfile=True)

        foo = Foo(path="/etc/hosts")
        validate_instance(foo)

        foo.path = "/tmp"
        result = validate_instance(foo)
        self.assertNotEqual(result.tag, 'OK')

    def test_path__can_create_or_write(self):
        class Foo(Model):
            path = PathType(can_create_or_write=True)

        foo = Foo(path="/tmp/file_that_doesnt_exist_but_can_be_created")
        result = validate_instance(foo)
        self.assertEqual(result.tag, 'OK')

        foo.path = "/tmp/dir_that_doesnt_exist/file_that_doesnt_exist"
        result = validate_instance(foo)
        self.assertNotEqual(result.tag, 'OK')

class ExecutablePathTestCase(unittest.TestCase):
    def setUp(self):
        import platform
        if platform.system() in ('Microsoft', 'Windows'):
            self.skipTest("cannot test on a non-UNIX platform")

    def test_path(self):
        class Foo(Model):
            path = ExecutablePathType()

        foo = Foo(path="/bin/sh")
        result = validate_instance(foo)
        self.assertEqual(result.tag, 'OK')

        foo.path = "/bin/file_that_doesnt_exist"
        result = validate_instance(foo)
        self.assertNotEqual(result.tag, 'OK')
