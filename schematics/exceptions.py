# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .common import * # pylint: disable=redefined-builtin
from .util import listify


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
class FieldError(BaseError):

    type = None

    def __init__(self, *args, **kwargs):

        if type(self) is FieldError:
            raise NotImplementedError("Please raise either ConversionError or ValidationError.")
        if len(args) == 0:
            raise TypeError("Please provide at least one error or error message.")
        if kwargs:
            items = [ErrorMessage(*args, **kwargs)]
        elif len(args) == 1:
            items = listify(args[0])
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

    def __getitem__(self, key):
        return self.messages[key]

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

StopValidation = StopValidationError


class CompoundError(BaseError):

    def __init__(self, errors):
        if not isinstance(errors, dict):
            raise TypeError("Compound errors must be reported as a dictionary.")
        self.messages = {}
        for key, value in errors.items():
            if isinstance(value, CompoundError):
                self.messages[key] = value.messages
            else:
                self.messages[key] = value
        super(CompoundError, self).__init__(self.messages)


class DataError(CompoundError):

    def __init__(self, messages, partial_data=None):
        super(DataError, self).__init__(messages)
        self.partial_data = partial_data

ModelConversionError = DataError
ModelValidationError = DataError


class MockCreationError(ValueError):
    """Exception raised when a mock value cannot be generated."""
    pass


class MissingValueError(AttributeError, KeyError):
    """Exception raised when accessing an undefined value on an instance."""
    pass


class UnknownFieldError(KeyError):
    """Exception raised when attempting to set a nonexistent field using the subscription syntax."""
    pass


__all__ = module_exports(__name__)

