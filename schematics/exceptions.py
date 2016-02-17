from collections import Iterable

from six import iteritems

from .util import listify

try:
    basestring #PY2
    bytes = str
except NameError:
    basestring = str #PY3
    unicode = str


class ErrorMessage(object):

    def __init__(self, summary, info=None):
        self.type = None
        self.summary = summary
        self.info = info

    def __str__(self):
        return self.summary

    def __repr__(self):
        return '{0}("{1}", info={2})'.format(type(self).__name__, self.summary, self.info_repr)

    @property
    def info_repr(self):
        if self.info is None:
            return 'None'
        elif isinstance(self.info, int):
            return self.info
        elif isinstance(self.info, basestring):
            return '"{0}"'.format(self.info)
        else:
            return "<'{0}' object>".format(type(self.info).__name__)

    def __eq__(self, other):
        if isinstance(other, ErrorMessage):
            return self.__dict__ == other.__dict__
        elif isinstance(other, basestring):
            return self.summary == other
        else:
            return False


class BaseError(Exception):
    pass


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
            if isinstance(item, basestring):
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

        Exception.__init__(self, self.messages)

    def __eq__(self, other):
        if type(other) is type(self):
            return other.messages == self.messages
        elif type(other) is list:
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
            msg = self.messages[0]
            msg_repr = '"{0}", info={1}'.format(msg.summary, msg.info_repr)
        else:
            msg_repr = str.join(', ',
                                ('("{0}", {1})'.format(msg.summary, msg.info_repr)
                                 for msg in self.messages))
        return '{0}({1})'.format(type(self).__name__, msg_repr)

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
        Exception.__init__(self, self.messages)


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

