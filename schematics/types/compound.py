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
            except ValidationError, e:
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

    @property
    def fields(self):
        return self.model_class._fields

    def convert(self, value):
        if isinstance(value, self._model_class):
            if value.errors:
                raise ValidationError(u'Please supply a clean model instance.')
            else:
                return value

        if not isinstance(value, dict):
            raise ValidationError(u'Please use a mapping for this field.')

        errors = {}
        result = {}
        for name, field in self.fields.iteritems():
            try:
                result[name] = field(value.get(name))
            except ValidationError, e:
                errors[name] = e
        if errors:
            raise ValidationError(errors)
        return self.model_class(**result)

    def to_primitive(self, value):
        result = {}
        for key, field in self.fields.iteritems():
            result[key] = field.to_primitive(value.get(key))
        return result


class ListType(MultiType):

    def __init__(self, field, min_size=None, max_size=None, **kwargs):
        if not isinstance(field, BaseType):
            field = field(**kwargs)

        self.field = field
        self.min_size = min_size
        self.max_size = max_size
        super(ListType, self).__init__(**kwargs)

        if min_size is not None:
            self.required = True

    @property
    def model_class(self):
        return self.field.model_class

    def _force_list(self, value):
        if value is None:
            return []
        try:
            if isinstance(value, basestring):
                raise TypeError()

            if isinstance(value, dict):
                return [value[str(k)] for k in sorted(map(int, value.keys()))]

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
                item = self.field(item)
            except ValidationError, e:
                errors[idx] = e
            else:
                result.append(item)

        if errors:
            raise ValidationError(errors)
        return result

    def to_primitive(self, value):
        return map(self.field.to_primitive, self._force_list(value))


class DictType(MultiType):

    def __init__(self, field, **kwargs):
        if not isinstance(field, BaseType):
            field = field(**kwargs)

        self.field = field

        super(DictType, self).__init__(**kwargs)

    @property
    def model_class(self):
        return self.field.model_class

    def convert(self, value):
        if not isinstance(value, dict):
            raise ValidationError('Only dictionaries may be used in a DictType')

        return value

    def lookup_member(self, member_name):
        return self.basecls(field_name=member_name)
