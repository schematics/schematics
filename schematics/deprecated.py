
import warnings
import functools

from collections import OrderedDict

from .types.serializable import Serializable
from . import transforms


class SchematicsDeprecationWarning(DeprecationWarning):
    pass


def deprecated(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn(
            "Call to deprecated function {0}.".format(func.__name__),
            category=SchematicsDeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return new_func

class BaseErrorV1Mixin:

    @property
    @deprecated
    def messages(self):
        """ an alias for errors, provided for compatibility with V1. """
        return self.errors


def patch_schema():
    global schema_Schema
    from . import schema
    schema_Schema = schema.Schema
    class Schema(SchemaCompatibilityMixin, schema.Schema):
        __doc__ = schema.Schema.__doc__
    schema.Schema = Schema


def patch_exceptions():
    from . import exceptions
    exceptions.BaseError.messages = BaseErrorV1Mixin.messages
    exceptions.ModelConversionError = exceptions.DataError  # v1
    exceptions.ModelValidationError = exceptions.DataError  # v1
    exceptions.StopValidation = exceptions.StopValidationError  # v1


def patch_all():
    patch_exceptions()
