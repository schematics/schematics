# encoding=utf-8

from .models import BaseModel, ModelMetaclass, ModelOptions
from .validation import validate_values, validate_partial
from .serialize import make_safe_json, to_json
from .exceptions import InvalidModel


class Model(BaseModel):

    __metaclass__ = ModelMetaclass
    __optionsclass__ = ModelOptions

    def to_json(self, role=None):
        """No filtering of output unless role is defined.

        """

        if role is None:
            return to_json(self, lambda k, v: False, encode=False)
        return make_safe_json(self.__class__, self, role, encode=False)

    @classmethod
    def validate(cls, items, partial=False, strict=False):
        """Validates incoming untrusted data. If `partial` is set it will allow
        partial data to validate, useful for PATCH requests. Returns a clean
        instance.

        """

        if partial:
            items, errors = validate_partial(cls, items, report_rogues=strict)
        else:
            items, errors = validate_values(cls, items, report_rogues=strict)

        if errors:
            raise InvalidModel(errors)

        return cls(**items)