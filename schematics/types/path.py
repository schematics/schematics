import os
from os import path

from .base import StringType, TypeException

class PathType(StringType):
    """
    A path field.
    You can use one or a combination of the following validation attributes to validate the path:
      * exists. Asserts that the path exists.
      * isfile. Asserts that if the path exists, it's a file.
      * isdir. Asserts that if the path exists, it's a directory.
      * access. Asserts that Python's os.access(path, access) == True. Use it to check for read/write/execute
      *         permissions.
      * can_create_or_write. Asserts that if the file exists it can be written to, and if it doesn't exist then its
      *                      parent directory exists and can be written to.
    """
    def __init__(self, access=None, exists=False, isdir=False, isfile=False, can_create_or_write=False, **kwargs):
        super(PathType, self).__init__(**kwargs)
        self.access = access
        self.exists = exists
        self.isdir = isdir
        self.isfile = isfile
        self.can_create_or_write = can_create_or_write

    def validate(self, value):
        if not isinstance(value, basestring):
            raise TypeException("value must be a string", self.field_name, value)

        realpath = path.realpath(value)
        path_exists = path.exists(realpath)

        if self.exists and not path_exists:
            raise TypeException("path does not exist", self.field_name, value)

        if self.can_create_or_write:
            if path_exists and not os.access(realpath, os.W_OK):
                raise TypeException("path is not writable", self.field_name, value)
            else:
                parent_dir = path.dirname(realpath)
                if not path.exists(path.dirname(realpath)):
                    raise TypeException("parent directory does not exist", self.field_name, value)
                if not path.isdir(parent_dir):
                    raise TypeException("parent directory is not a directory", self.field_name, value)
                if not os.access(parent_dir, os.W_OK):
                    raise TypeException("parent directory is not writable", self.field_name, value)

        if path_exists and self.isfile and not path.isfile(realpath):
            raise TypeException("path is not a file", self.field_name, value)

        if path_exists and self.isdir and not path.isdir(realpath):
            raise TypeException("path is not a directory", self.field_name, value)

        if self.access is not None:
            if not os.access(realpath, self.access):
                permissions = self._access_to_permission_list(self.access)
                raise TypeException("path does not have one or more of the following permissions: {}".format(
                        ", ".join(permissions)), self.field_name, value)

        return value

    def _access_to_permission_list(self, access):
        permissions = []
        if self.access & os.W_OK:
            permissions.append("writable")
        if self.access & os.R_OK:
            permissions.append("readable")
        if self.access & os.X_OK:
            permissions.append("executable")
        return permissions

class ExecutablePathType(PathType):
    """A field that stores a path to an executable file. It validates the path points to an existing file and that
    the file can be executed by the current user."""
    def __init__(self, **kwargs):
        super(ExecutablePathType, self).__init__(access=os.R_OK | os.X_OK, exists=True, isfile=True, **kwargs)
