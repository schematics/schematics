import itertools

from ..exceptions import ValidationError, StopValidation
from .base import BaseType


class MultiType(BaseType):

    def validate(self, value):
        """Report dictionary of errors with lists of errors as values of each
        key. Used by ModelType and ListType.

        """

        try:
            del self.errors
            del self.clean
        except AttributeError:
            pass

        self.errors = {}

        def aggregate_from_exception_errors(e):
            if e.args and e.args[0]:
                if not isinstance(e.args[0], dict):
                    return BaseType.validate(self, value)
                self.errors.update(e.args[0])

        validator_chain = itertools.chain(
            [
                self.required_validation,
                self.convert,
            ],
            self.validators or []
        )

        for validator in validator_chain:
            try:
                value = validator(value)
            except ValueError, e:
                aggregate_from_exception_errors(e)
                if isinstance(e, StopValidation):
                    return False

        if self.errors:
            return False

        self.clean = value
        return True


class ModelType(MultiType):
    def __init__(self, model_class, **kwargs):
        self._model_class = model_class
        super(ModelType, self).__init__(**kwargs)

    @property
    def model_class(self):
        if self._model_class == "self":
            return self.owner_model
        return self._model_class

    def convert(self, value):
        if hasattr(value, "to_dict"):
            value = value.to_dict()
        if not isinstance(value, dict):
            raise StopValidation(u'Please provide a mapping with keys: %s'
                                    % u', '.join(self.model_class.fields))
        return self.model_class(**value)

    def to_primitive(self, value):
        if isinstance(value, dict):
            return value
        return value.data


class ListType(MultiType):

    def __init__(self, field, min_size=None, max_size=None, **kwargs):
        if not isinstance(field, BaseType):
            field = field(**kwargs)
        self.field = field
        self.min_size = min_size
        self.max_size = max_size
        super(ListType, self).__init__(**kwargs)

    @property
    def model_class(self):
        return self.field.model_class

    def _force_list(self, value):
        if value is None:
            return []
        try:
            if isinstance(value, (dict, basestring)):
                raise TypeError()
            return list(value)
        except TypeError:
            return [value]

    def convert(self, value):
        value = self._force_list(value)
        if self.min_size is not None and len(value) < self.min_size:
            message = ({
                True: u'Please provide at least %d item.',
                False: u'Please provide at least %d items.'}[self.min_size == 1]
            ) % self.min_size
            raise ValidationError(message)
        if self.max_size is not None and len(value) > self.max_size:
            message = ({
                True: u'Please provide no more than %d item.',
                False: u'Please provide no more than %d items.'}[self.max_size == 1]
            ) % self.max_size
            raise ValidationError(message)
        result = []
        errors = {}
        # Aggregate errors
        for idx, item in enumerate(value, 1):
            try:
                item = self.field.required_validation(item)
                item = self.field.convert(item)
            except ValueError, e:
                errors[idx] = e
            else:
                result.append(item)
        if errors:
            raise ValidationError(errors)
        return result

    def to_primitive(self, value):
        return map(self.field.to_primitive, self._force_list(value))
