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

    def to_primitive(self, value, model_converter=None):
        raise NotImplemented()


class ModelType(MultiType):
    def __init__(self, model_class, **kwargs):
        self._model_class = model_class
        self.fields = self.model_class.fields
        super(ModelType, self).__init__(**kwargs)

    @property
    def model_class(self):
        return self._model_class

    def convert(self, value):
        if isinstance(value, self.model_class):
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
                result[name] = field.validate(value.get(name))
            except ValidationError, e:
                errors[name] = e
        if errors:
            raise ValidationError(errors)
        return self.model_class(result)

    def to_primitive(self, values, model_converter=None):
        result = {}
        for key, field in self.fields.iteritems():
            value = values[key]
            if isinstance(field, MultiType):
                result[key] = model_converter(value)
            else:
                result[key] = field.to_primitive(value)

        return result

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.fields = {}
        for key, field in self.model_class.fields.iteritems():
            rv.fields[key] = _bind(field, model, memo)
        return rv

    def __repr__(self):
        return object.__repr__(self)[:-1] + ' for %s>' % self._model_class


EMPTY_LIST = "[]"
# Serializing to flat dict needs to output purely primitive key value types that
# can be safely put into e.g. redis. An empty list poses a problem as we cant
# set None as the field can be none


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
        if value is None or value == EMPTY_LIST:
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
                result.append(self.field(item))
            except ValidationError, e:
                errors['index_%s' % idx] = e
        if errors:
            raise ValidationError(sorted(errors.items()))
        return result

    def to_primitive(self, value, model_converter):
        if model_converter and isinstance(self.field, MultiType):
            convert = model_converter
        else:
            convert = lambda v: self.field.to_primitive(v)

        return map(convert, self._force_list(value))

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.field = _bind(self.field, model, memo)
        return rv


EMPTY_DICT = "{}"


class DictType(MultiType):

    def __init__(self, field, coerce_key=None, **kwargs):
        if not isinstance(field, BaseType):
            field = field(**kwargs)

        self.coerce_key = coerce_key or str
        self.field = field

        super(DictType, self).__init__(**kwargs)

    @property
    def model_class(self):
        return self.field.model_class

    def convert(self, value):
        if value == EMPTY_DICT:
            value = {}

        value = value or {}

        if not isinstance(value, dict):
            raise ValidationError(u'Only dictionaries may be used in a DictType')

        return dict((self.coerce_key(k), self.field(v))
                    for k, v in value.iteritems())

    def to_primitive(self, value, model_converter=None):
        if model_converter and isinstance(self.field, MultiType):
            convert = model_converter
        else:
            convert = lambda v: self.field.to_primitive(v)

        return dict((unicode(k), convert(v)) for k, v in value.iteritems())

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.field = _bind(self.field, model, memo)
        return rv
