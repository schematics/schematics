# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import copy

from collections import Sequence

from .common import *


@str_compat
class BaseError(Exception):

    def __init__(self, message, errors=None, *args):
        """
        The base class for all Schematics errors.

        message should be a human-readable message,
        while errors is a machine-readable list, or dictionary.

        if None is passed as the message, and error is populated,
        the primitive representation will be serialized.

        the Python logging module expects exceptions to be hashable
        and therefore immutable. As a result, it is not possible to
        mutate BaseError's error list or dict after initialization.
        """
        if message is None and errors is not None:
            message = str(self._to_primitive(errors))
        super(BaseError, self).__init__(message)
        self._errors = errors

    @property
    def errors(self):
        return copy.deepcopy(self._errors)

    @property
    def messages(self):
        """ an alias for errors, provided for compatibility with V1. """
        return self.errors

    def to_primitive(self):
        """
        converts the errors dict to a primitive representation of dicts,
        list and strings.
        """
        return self._to_primitive(self._errors)

    @classmethod
    def _to_primitive(cls, obj):
        """ recursive to_primitive for basic data types. """
        if isinstance(obj, list):
            return [cls._to_primitive(e) for e in obj]
        elif isinstance(obj, dict):
            return dict(
                (k, cls._to_primitive(v)) for k, v in obj.items()
            )
        else:
            return str(obj)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            if isinstance(self._errors, list):
                self._hash = hash(tuple(self._errors))
            if isinstance(self._errors, dict):
                dict_as_tuple = tuple([
                    (k, self._errors[k]) for k in sorted(self._errors)
                ])
                self._hash = hash(dict_as_tuple)
        return self._hash


@str_compat
class ErrorMessage(object):

    def __init__(self, summary, info=None):
        self.type = None
        self.summary = summary
        self.info = info

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    def __str__(self):
        if self.info:
            return '("%s", %s)' % (self.summary, self._info_as_str())
        else:
            return '"%s"' % self.summary

    def _info_as_str(self):
        if isinstance(self.info, int):
            return str(self.info)
        elif isinstance(self.info, string_type):
            return '"%s"' % self.info
        else:
            return "<'%s' object>" % self.info.__class__.__name__

    def __eq__(self, other):
        if isinstance(other, ErrorMessage):
            return self.__dict__ == other.__dict__
        elif isinstance(other, string_type):
            return self.summary == other
        else:
            return False

    def __hash__(self):
        return hash((self.summary, self.type, self.info))


@str_compat
class FieldError(BaseError, Sequence):

    type = None

    def __init__(self, *args, **kwargs):

        if type(self) is FieldError:
            raise NotImplementedError("Please raise either ConversionError or ValidationError.")
        if len(args) == 0:
            raise TypeError("Please provide at least one error or error message.")
        if kwargs:
            items = [ErrorMessage(*args, **kwargs)]
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, list):
                items = list(arg)
            else:
                items = [arg]
        else:
            items = args
        errors = []
        for item in items:
            if isinstance(item, string_type):
                errors.append(ErrorMessage(item))
            elif isinstance(item, tuple):
                errors.append(ErrorMessage(*item))
            elif isinstance(item, ErrorMessage):
                errors.append(item)
            elif isinstance(item, self.__class__):
                errors.extend(item.errors)
            else:
                raise TypeError("'{0}()' object is neither a {1} nor an error message."\
                                .format(type(item).__name__, type(self).__name__))
        for error in errors:
            error.type = self.type or type(self)

        super(FieldError, self).__init__(None, errors=errors)

    def __eq__(self, other):
        if type(other) is type(self):
            return other.errors == self.errors
        elif isinstance(other, list):
            return other == self.errors
        return False

    def __hash__(self):
        return super(FieldError, self).__hash__()

    def __contains__(self, value):
        return value in self.errors

    def __getitem__(self, index):
        return self.errors[index]

    def __iter__(self):
        return iter(self.errors)

    def __len__(self):
        return len(self.errors)

    def __repr__(self):
        if len(self.errors) == 1:
            msg_repr = str(self.errors[0])
        else:
            msg_repr = '[' + str.join(', ', map(str, self.errors)) + ']'
        return '%s(%s)' % (self.__class__.__name__, msg_repr)

    __str__ = __repr__


class ConversionError(FieldError, TypeError):
    """ Exception raised when data cannot be converted to the correct python type """
    pass


class ValidationError(FieldError, ValueError):
    """Exception raised when invalid data is encountered."""
    pass


class StopValidationError(ValidationError):
    """Exception raised when no more validation need occur."""
    type = ValidationError

StopValidation = StopValidationError # v1


class CompoundError(BaseError):

    def __init__(self, errors):
        if not isinstance(errors, dict):
            raise TypeError("Compound errors must be reported as a dictionary.")
        for key, value in errors.items():
            if isinstance(value, CompoundError):
                errors[key] = value.errors
            else:
                errors[key] = value
        super(CompoundError, self).__init__(None, errors)


class DataError(CompoundError):

    def __init__(self, errors, partial_data=None):
        super(DataError, self).__init__(errors)
        self.partial_data = partial_data

ModelConversionError = DataError # v1
ModelValidationError = DataError # v1


class MockCreationError(ValueError):
    """Exception raised when a mock value cannot be generated."""
    pass


class UndefinedValueError(AttributeError, KeyError):
    """Exception raised when accessing a field with an undefined value."""
    def __init__(self, model, name):
        msg = "'%s' instance has no value for field '%s'" % (model.__class__.__name__, name)
        super(UndefinedValueError, self).__init__(msg)


class UnknownFieldError(KeyError):
    """Exception raised when attempting to access a nonexistent field using the subscription syntax."""
    def __init__(self, model, name):
        msg = "Model '%s' has no field named '%s'" % (model.__class__.__name__, name)
        super(UnknownFieldError, self).__init__(msg)


__all__ = module_exports(__name__)
