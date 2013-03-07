import itertools

from ..exceptions import ValidationError, StopValidation
from .base import BaseType
from .bind import _bind


class MultiType(BaseType):

    def validate(self, value):
        """Report dictionary of errors with lists of errors as values of each
        key. Used by ModelType and ListType.

        """

        errors = {}

        def aggregate_from_exception_errors(e):
            if e.args and e.args[0]:
                if not isinstance(e.args[0], dict):
                    # We have a field level error, not for the instances
                    raise e
                errors.update(e.args[0])

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
            except ValidationError, e:
                aggregate_from_exception_errors(e)
                if isinstance(e, StopValidation):
                    return False

        if errors:
            raise ValidationError(errors)

        return value


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
        if not isinstance(value, dict):
            raise ValidationError(u'Please use a mapping for this field')
        errors = {}
        result = {}
        for name, field in self.fields.iteritems():
            try:
                result[name] = field.validate(value.get(name))
            except ValidationError, e:
                errors[name] = e
        if errors:
            raise ValidationError(errors)
        return self.model_class(**result)

    def to_primitive(self, values):
        result = {}
        for key, field in self.fields.iteritems():
            result[key] = field.to_primitive(values[key])
        return result

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.fields = {}
        for key, field in self.model_class.fields.iteritems():
            rv.fields[key] = _bind(field, model, memo)
        return rv


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
                result.append(self.field(item))
            except ValidationError, e:
                errors['index-%s' % idx] = e
        if errors:
            raise ValidationError(errors)
        return result

    def to_primitive(self, value):
        return map(self.field.to_primitive, self._force_list(value))

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.field = _bind(self.field, model, memo)
        return rv
