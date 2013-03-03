# encoding=utf-8

from .models import Model
from .validation import validate_values, validate_partial
from .serialize import make_safe_json, to_json


class InvalidForm(Exception):
    def __init__(self, errors):
        self.errors = errors


class Form(Model):
    """
    A batteries included version of `Model`. Validation and serialization are
    implemented as instance or class methods.

    """

    def to_json(self, role=None):
        if role:
            return make_safe_json(self.__class__, self, role, encode=False)
        return to_json(self, encode=False)

    @classmethod
    def from_json(cls, items, partial=False, strict=False):
        """Validates incoming untrusted data. If `partial` is set it will allow
        partial data to validate, useful for PATCH requests. Returns a clean
        instance.

        """

        if partial:
            items, errors = validate_partial(cls, items, report_rogues=strict)
        else:
            items, errors = validate_values(cls, items, report_rogues=strict)

        if errors:
            raise InvalidForm(errors)

        return cls(**items)
