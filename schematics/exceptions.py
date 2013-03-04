class ValidationError(Exception):
    pass

class StopValidation(Exception):
    pass

class InvalidModel(Exception):
    def __init__(self, errors):
        self.errors = errors