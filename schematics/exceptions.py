class ValidationError(ValueError):
    """Exception raised when invalid data is encountered."""

    def __init__(self, messages):
        if not isinstance(messages, (list, tuple, dict)):
            messages = [messages]
        # make all items in the list unicode
        Exception.__init__(self, self.to_primary(messages))
        self.messages = messages

    def to_primary(self, messages):
        if isinstance(messages, dict):
            msgs_ = {}
            for index, errors in messages.iteritems():
                # Expand values to primary
                for msg in self.to_primary(errors):
                    msgs_.setdefault(index, []).extend(msg)
            return msgs_
        return list(messages)


class StopValidation(ValidationError):
    """Exception raised when no more validation need occur."""
    pass
