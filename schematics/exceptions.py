# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from collections import Sequence

from .common import *


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


class BaseError(Exception):
    pass


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
        self.messages = []
        for item in items:
            if isinstance(item, string_type):
                self.messages.append(ErrorMessage(item))
            elif isinstance(item, tuple):
                self.messages.append(ErrorMessage(*item))
            elif isinstance(item, ErrorMessage):
                self.messages.append(item)
            elif isinstance(item, self.__class__):
                self.messages.extend(item.messages)
            else:
                raise TypeError("'{0}()' object is neither a {1} nor an error message."\
                                .format(type(item).__name__, type(self).__name__))
        for message in self.messages:
            message.type = self.type or type(self)

        super(FieldError, self).__init__(self.messages)

    def __eq__(self, other):
        if type(other) is type(self):
            return other.messages == self.messages
        elif isinstance(other, list):
            return other == self.messages
        return False

    def __contains__(self, value):
        return value in self.messages

    def __getitem__(self, index):
        return self.messages[index]

    def __iter__(self):
        return iter(self.messages)

    def __len__(self):
        return len(self.messages)

    def __repr__(self):
        if len(self.messages) == 1:
            msg_repr = str(self.messages[0])
        else:
            msg_repr = '[' + str.join(', ', map(str, self.messages)) + ']'
        return '%s(%s)' % (self.__class__.__name__, msg_repr)

    __str__ = __repr__

    def pop(self, *args):
        return self.messages.pop(*args)


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
        self.errors = {}
        for key, value in errors.items():
            if isinstance(value, CompoundError):
                self.errors[key] = value.errors
            else:
                self.errors[key] = value
        self.messages = self.errors # v1
        super(CompoundError, self).__init__(self.errors)


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
