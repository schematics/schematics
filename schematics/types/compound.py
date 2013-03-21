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
                    break

        if errors:
            raise ValidationError(errors)

        return value

    def filter_by_role(self, clean_value, primitive_value, role, raise_error_on_role=False):
        raise NotImplemented()


class ModelType(MultiType):
    def __init__(self, model_class, **kwargs):
        self.model_class = model_class
        self.fields = self.model_class.fields
        super(ModelType, self).__init__(**kwargs)

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.fields = {}
        for key, field in self.model_class.fields.iteritems():
            rv.fields[key] = _bind(field, model, memo)
        return rv

    def __repr__(self):
        return object.__repr__(self)[:-1] + ' for %s>' % self.model_class

    def convert(self, value):
        if value is None:  # We have already checked if the field is required. If it is None it should continue being None
            return None

        if isinstance(value, self.model_class):
            if value.errors:
                raise ValidationError(u'Please supply a clean model instance.')
            else:
                return value

        if not isinstance(value, dict):
            raise ValidationError(u'Please use a mapping for this field or {} instance instead of {}.'.format(
                self.model_class.__name__,
                type(value).__name__))

        # We don't allow partial submodels because that is just complex and
        # not obviously useful
        return self.model_class(value, partial=False)

    def to_primitive(self, model_instance, include_serializables=True):
        primitive_data = {}
        for field_name, field, value in model_instance.iter(include_serializables):
            serialized_name = field.serialized_name or field_name

            if value is None:
                if field.serialize_when_none:
                    primitive_data[serialized_name] = None
            else:
                primitive_data[serialized_name] = field.to_primitive(value)

        return primitive_data

    def filter_by_role(self, model_instance, primitive_data, role, raise_error_on_role=False):
        if model_instance is None:
            return primitive_data

        gottago = lambda k, v: False
        if role in self.model_class._options.roles:
            gottago = self.model_class._options.roles[role]
        elif role and raise_error_on_role:
            raise ValueError(u'%s Model has no role "%s"' % (
                self.model_class.__name__, role))

        for field_name, field, value in model_instance:
            serialized_name = field.serialized_name or field_name

            if gottago(field_name, value):
                primitive_data.pop(serialized_name)
            elif isinstance(field, MultiType):
                primitive_value = primitive_data.get(serialized_name, None)
                if primitive_value:
                    field.filter_by_role(
                        value,
                        primitive_value,
                        role
                    )

        return primitive_data


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

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.field = _bind(self.field, model, memo)
        return rv

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

    def to_primitive(self, value):
        return map(self.field.to_primitive, value)

    def filter_by_role(self, clean_list, primitive_list, role, raise_error_on_role=False):
        if isinstance(self.field, MultiType):
            for clean_value, primitive_value in zip(clean_list, primitive_list):
                self.field.filter_by_role(clean_value, primitive_value, role)

        return primitive_list


EMPTY_DICT = "{}"


class DictType(MultiType):

    def __init__(self, field, coerce_key=None, **kwargs):
        if not isinstance(field, BaseType):
            field = field(**kwargs)

        self.coerce_key = coerce_key or str
        self.field = field

        super(DictType, self).__init__(**kwargs)

    def _bind(self, model, memo):
        rv = BaseType._bind(self, model, memo)
        rv.field = _bind(self.field, model, memo)
        return rv

    def convert(self, value):
        if value == EMPTY_DICT:
            value = {}

        value = value or {}

        if not isinstance(value, dict):
            raise ValidationError(u'Only dictionaries may be used in a DictType')

        return dict((self.coerce_key(k), self.field(v))
                    for k, v in value.iteritems())

    def to_primitive(self, value):
        return dict((unicode(k), self.field.to_primitive(v)) for k, v in value.iteritems())

    def filter_by_role(self, clean_data, primitive_data, role, raise_error_on_role=False):
        if clean_data is None:
            return primitive_data

        if isinstance(self.field, MultiType):
            for key, clean_value in clean_data.iteritems():
                primitive_value = primitive_data[unicode(key)]

                self.field.filter_by_role(clean_value, primitive_value, role)

        return primitive_data
