from six import iteritems

class BaseError(Exception):

    def __init__(self, messages):
        if not isinstance(messages, (list, tuple, dict)):
            messages = [messages]

        clean_messages = self.clean_messages(messages)

        Exception.__init__(self, clean_messages)
        self.messages = clean_messages

    def clean_messages(self, messages):
        if isinstance(messages, dict):
            clean_messages = {}
            for key, value in iteritems(messages):
                if isinstance(value, ValidationError):
                    value = value.messages
                clean_messages[key] = value
        else:
            clean_messages = []
            for message in messages:
                if isinstance(message, ValidationError):
                    message = message.messages
                clean_messages.append(message)

        return clean_messages


class ConversionError(BaseError, TypeError):

    """ Exception raised when data cannot be converted to the correct python type """
    pass


class ModelConversionError(ConversionError):
    def __init__(self, messages, partial_data=None):
        super(ModelConversionError, self).__init__(messages)
        self.partial_data = partial_data


class ValidationError(BaseError, ValueError):

    """Exception raised when invalid data is encountered."""
    pass


class ModelValidationError(ValidationError):
    pass


class StopValidation(ValidationError):

    """Exception raised when no more validation need occur."""
    pass


class MockCreationError(ValueError):
    """Exception raised when a mock value cannot be generated."""
    pass
