# -*- coding: utf-8 -*-

from __future__ import division

from collections import Iterable
import itertools
import functools

from ..exceptions import (ValidationError, ConversionError,
                          ModelValidationError, StopValidation,
                          MockCreationError)
from .base import BaseType, get_value_in

from six import iteritems
from six import string_types as basestring
from six import text_type as unicode
from six.moves import xrange


class MultiType(BaseType):

    def _setup(self, field_name, owner_model):
        # Recursively set up inner fields.
        if hasattr(self, 'field'):
            self.field._setup(None, owner_model)
        super(MultiType, self)._setup(field_name, owner_model)

    def validate(self, value, env=None):
        """Report dictionary of errors with lists of errors as values of each
        key. Used by ModelType and ListType.

        """
        errors = {}

        for validator in self.validators:
            try:
                validator(value, env=env)
            except ModelValidationError as exc:
                errors.update(exc.messages)
                if isinstance(exc, StopValidation):
                    break

        if errors:
            raise ValidationError(errors)

        return value

    def export_loop(self, shape_instance, field_converter,
                    role=None, print_none=False):
        raise NotImplementedError

    def init_compound_field(self, field, compound_field, **kwargs):
        """
        Some of non-BaseType fields requires `field` arg.
        Not avoid name conflict, provide it as `compound_field`.
        Example:

            comments = ListType(DictType, compound_field=StringType)
        """
        if compound_field:
            field = field(field=compound_field, **kwargs)
        else:
            field = field(**kwargs)
        return field


class ModelType(MultiType):
    """A field that can hold an instance of the specified model."""

    @property
    def fields(self):
        return self.model_class.fields

    def __init__(self, model_spec, **kwargs):

        if isinstance(model_spec, ModelMeta):
            self.model_class = model_spec
            self.model_name = self.model_class.__name__
        elif isinstance(model_spec, basestring):
            self.model_class = None
            self.model_name = model_spec
        else:
            raise TypeError("ModelType: Expected a model, got an argument "
                            "of the type '{}'.".format(model_spec.__class__.__name__))

        validators = kwargs.pop("validators", [])
        self.strict = kwargs.pop("strict", True)

        def validate_model(model_instance, env=None):
            model_instance.validate(env=env)
            return model_instance

        super(ModelType, self).__init__(validators=[validate_model] + validators, **kwargs)

    def __repr__(self):
        return object.__repr__(self)[:-1] + ' for %s>' % self.model_class

    def _mock(self, context=None):
        return self.model_class.get_mock_object(context)

    def _setup(self, field_name, owner_model):
        # Resolve possible name-based model reference.
        if not self.model_class:
            if self.model_name == owner_model.__name__:
                self.model_class = owner_model
            else:
                raise Exception("ModelType: Unable to resolve model '{}'.".format(self.model_name))
        super(ModelType, self)._setup(field_name, owner_model)

    def to_native(self, value, mapping=None, context=None, env=None):
        # We have already checked if the field is required. If it is None it
        # should continue being None
        mapping = mapping or {}
        if value is None:
            return None
        if isinstance(value, self.model_class):
            return value

        if not isinstance(value, dict):
            raise ConversionError(
                u'Please use a mapping for this field or {0} instance instead of {1}.'.format(
                    self.model_class.__name__,
                    type(value).__name__))

        # partial submodels now available with import_data (ht ryanolson)
        model = self.model_class()
        return model.import_data(value, mapping=mapping, context=context,
                                 strict=self.strict, env=env)

    def export_loop(self, model_instance, field_converter,
                    role=None, print_none=False):
        """
        Calls the main `export_loop` implementation because they are both
        supposed to operate on models.
        """
        if isinstance(model_instance, self.model_class):
            model_class = model_instance.__class__
        else:
            model_class = self.model_class

        shaped = export_loop(model_class, model_instance,
                             field_converter,
                             role=role, print_none=print_none)

        return shaped


class ListType(MultiType):
    """A field for storing a list of items, all of which must conform to the type
    specified by the ``field`` parameter.
    """

    def __init__(self, field, min_size=None, max_size=None, **kwargs):

        if not isinstance(field, BaseType):
            compound_field = kwargs.pop('compound_field', None)
            field = self.init_compound_field(field, compound_field, **kwargs)

        self.field = field
        self.min_size = min_size
        self.max_size = max_size

        validators = [self.check_length] + kwargs.pop("validators", [])

        super(ListType, self).__init__(validators=validators, **kwargs)

    @property
    def model_class(self):
        return self.field.model_class

    def _mock(self, context=None):
        min_size = self.min_size or 1
        max_size = self.max_size or 1
        if min_size > max_size:
            message = u'Minimum list size is greater than maximum list size.'
            raise MockCreationError(message)
        random_length = get_value_in(min_size, max_size)

        return [self.field._mock(context) for _ in xrange(random_length)]

    def _force_list(self, value):
        if value is None or value == EMPTY_LIST:
            return []

        try:
            if isinstance(value, basestring):
                raise TypeError()

            if isinstance(value, dict):
                return [value[unicode(k)] for k in sorted(map(int, value.keys()))]

            return list(value)
        except TypeError:
            return [value]

    def to_native(self, value, context=None, env=None):
        items = self._force_list(value)
        if isinstance(self.field, MultiType):
            to_native = functools.partial(self.field.to_native, env=env)
        else:
            to_native = self.field.to_native

        return [to_native(item, context) for item in items]

    def check_length(self, value, env=None):
        list_length = len(value) if value else 0

        if self.min_size is not None and list_length < self.min_size:
            message = ({
                True: u'Please provide at least %d item.',
                False: u'Please provide at least %d items.',
            }[self.min_size == 1]) % self.min_size
            raise ValidationError(message)

        if self.max_size is not None and list_length > self.max_size:
            message = ({
                True: u'Please provide no more than %d item.',
                False: u'Please provide no more than %d items.',
            }[self.max_size == 1]) % self.max_size
            raise ValidationError(message)

    def validate_items(self, items, env=None):
        if isinstance(self.field, MultiType):
            validate = functools.partial(self.field.validate, env=env)
        else:
            validate = self.field.validate
        errors = []
        for item in items:
            try:
                validate(item)
            except ValidationError as exc:
                errors.append(exc.messages)
        if errors:
            raise ValidationError(errors)

    def export_loop(self, list_instance, field_converter,
                    role=None, print_none=False):
        """Loops over each item in the model and applies either the field
        transform or the multitype transform.  Essentially functions the same
        as `transforms.export_loop`.
        """
        data = []
        for value in list_instance:
            if hasattr(self.field, 'export_loop'):
                shaped = self.field.export_loop(value, field_converter,
                                                role=role)
                feels_empty = shaped is None or len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            # Print if we want empty or found a value
            if feels_empty:
                if self.field.allow_none() or print_none:
                    data.append(shaped)
            elif shaped is not None:
                data.append(shaped)

        return data


class DictType(MultiType):
    """A field for storing a mapping of items, the values of which must conform to the type
    specified by the ``field`` parameter.
    """

    def __init__(self, field, coerce_key=None, **kwargs):
        if not isinstance(field, BaseType):
            compound_field = kwargs.pop('compound_field', None)
            field = self.init_compound_field(field, compound_field, **kwargs)

        self.coerce_key = coerce_key or unicode
        self.field = field

        validators = [self.validate_items] + kwargs.pop("validators", [])

        super(DictType, self).__init__(validators=validators, **kwargs)

    @property
    def model_class(self):
        return self.field.model_class

    def to_native(self, value, safe=False, context=None, env=None):
        if value == EMPTY_DICT:
            value = {}
        value = value or {}
        if not isinstance(value, dict):
            raise ConversionError(u'Only dictionaries may be used in a DictType')

        if isinstance(self.field, MultiType):
            to_native = functools.partial(self.field.to_native, env=env)
        else:
            to_native = self.field.to_native

        return dict((self.coerce_key(k), to_native(v, context))
                    for k, v in iteritems(value))

    def validate_items(self, items, env=None):
        if isinstance(self.field, MultiType):
            validate = functools.partial(self.field.validate, env=env)
        else:
            validate = self.field.validate
        errors = {}
        for key, value in iteritems(items):
            try:
                validate(value)
            except ValidationError as exc:
                errors[key] = exc

        if errors:
            raise ValidationError(errors)

    def export_loop(self, dict_instance, field_converter,
                    role=None, print_none=False):
        """Loops over each item in the model and applies either the field
        transform or the multitype transform.  Essentially functions the same
        as `transforms.export_loop`.
        """
        data = {}

        for key, value in iteritems(dict_instance):
            if hasattr(self.field, 'export_loop'):
                shaped = self.field.export_loop(value, field_converter,
                                                role=role)
                feels_empty = shaped is None or len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            if feels_empty:
                if self.field.allow_none() or print_none:
                    data[key] = shaped
            elif shaped is not None:
                data[key] = shaped

        return data


class PolyModelType(MultiType):
    """A field that accepts an instance of any of the specified models."""

    def __init__(self, model_spec, **kwargs):

        if isinstance(model_spec, (ModelMeta, basestring)):
            self.model_classes = (model_spec,)
            allow_subclasses = True
        elif isinstance(model_spec, Iterable):
            self.model_classes = tuple(model_spec)
            allow_subclasses = False
        else:
            raise Exception("The first argument to PolyModelType.__init__() "
                            "must be a model or an iterable.")

        validators = kwargs.pop("validators", [])
        self.strict = kwargs.pop("strict", True)
        self.claim_function = kwargs.pop("claim_function", None)
        self.allow_subclasses = kwargs.pop("allow_subclasses", allow_subclasses)

        def validate_model(model_instance, env=None):
            model_instance.validate(env=env)
            return model_instance

        MultiType.__init__(self, validators=[validate_model] + validators, **kwargs)

    def __repr__(self):
        return object.__repr__(self)[:-1] + ' for %s>' % str(self.model_classes)

    def _setup(self, field_name, owner_model):
        # Resolve possible name-based model references.
        resolved_classes = []
        for m in self.model_classes:
            if isinstance(m, basestring):
                if m == owner_model.__name__:
                    resolved_classes.append(owner_model)
                else:
                    raise Exception("PolyModelType: Unable to resolve model '{}'.".format(m))
            else:
                resolved_classes.append(m)
        self.model_classes = tuple(resolved_classes)
        super(PolyModelType, self)._setup(field_name, owner_model)

    def is_allowed_model(self, model_instance):
        if self.allow_subclasses:
            if isinstance(model_instance, self.model_classes):
                return True
        else:
            if model_instance.__class__ in self.model_classes:
                return True
        return False

    def to_native(self, value, mapping=None, context=None, env=None):

        if mapping is None:
            mapping = {}
        if value is None:
            return None
        if self.is_allowed_model(value):
            return value
        if not isinstance(value, dict):
            if len(self.model_classes) > 1:
                instanceof_msg = 'one of: {}'.format(', '.join(
                    cls.__name__ for cls in self.model_classes))
            else:
                instanceof_msg = self.model_classes[0].__name__
            raise ConversionError(u'Please use a mapping for this field or '
                                    'an instance of {}'.format(instanceof_msg))

        model_class = self.find_model(value)
        model = model_class()
        return model.import_data(value, mapping=mapping, context=context,
                                 strict=self.strict, env=env)

    def find_model(self, data):
        """Finds the intended type by consulting potential classes or `claim_function`."""

        chosen_class = None
        if self.claim_function:
            chosen_class = self.claim_function(self, data)
        else:
            candidates = self.model_classes
            if self.allow_subclasses:
                candidates = itertools.chain.from_iterable(
                                 ([m] + m._subclasses for m in candidates))
            fallback = None
            matching_classes = []
            for cls in candidates:
                match = None
                if '_claim_polymorphic' in cls.__dict__:
                    match = cls._claim_polymorphic(data)
                elif not fallback: # The first model that doesn't define the hook
                    fallback = cls # can be used as a default if there's no match.
                if match:
                    matching_classes.append(cls)
            if not matching_classes and fallback:
                chosen_class = fallback
            elif len(matching_classes) == 1:
                chosen_class = matching_classes[0]
            else:
                raise Exception("Got ambiguous input for polymorphic field")
        if chosen_class:
            return chosen_class
        else:
            raise Exception("Input for polymorphic field did not match any model")

    def export_loop(self, model_instance, field_converter,
                    role=None, print_none=False):

        model_class = model_instance.__class__
        if not self.is_allowed_model(model_instance):
            raise Exception("Cannot export: {} is not an allowed type".format(model_class))

        shaped = export_loop(model_class, model_instance,
                             field_converter,
                             role=role, print_none=print_none)

        return shaped


from ..models import Model, ModelMeta
from ..transforms import export_loop, EMPTY_LIST, EMPTY_DICT
