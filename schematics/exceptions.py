

class ValidationError(ValueError):
    """Exception raised when invalid data is encountered."""

    def __init__(self, messages):
        if not isinstance(messages, (list, tuple, dict)):
            messages = [messages]

        clean_messages = self.clean_messages(messages)

        Exception.__init__(self, clean_messages)
        self.messages = clean_messages

    def clean_messages(self, messages):
        if isinstance(messages, dict):
            clean_messages = {}
            for k, v in messages.iteritems():
                if isinstance(v, ValidationError):
                    v = v.messages
                clean_messages[k] = v
        else:
            clean_messages = []
            for v in messages:
                if isinstance(v, ValidationError):
                    v = v.messages
                clean_messages.append(v)

        return clean_messages

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
