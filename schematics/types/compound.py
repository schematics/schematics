# -*- coding: utf-8 -*-

from __future__ import division

from collections import Iterable
import itertools

from ..exceptions import ValidationError, ConversionError, ModelValidationError, StopValidation
from ..transforms import export_loop, EMPTY_LIST, EMPTY_DICT
from .base import BaseType

from six import iteritems
from six import string_types as basestring
from six import text_type as unicode

class MultiType(BaseType):

    def validate(self, value):
        """Report dictionary of errors with lists of errors as values of each
        key. Used by ModelType and ListType.

        """
        errors = {}

        for validator in self.validators:
            try:
                validator(value)
            except ModelValidationError as exc:
                errors.update(exc.messages)
            except StopValidation as exc:
                errors.update(exc.messages)
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

    def __init__(self, model_class, **kwargs):
        self.model_class = model_class
        self.fields = self.model_class.fields

        validators = kwargs.pop("validators", [])
        self.strict = kwargs.pop("strict", True)

        def validate_model(model_instance):
            model_instance.validate()
            return model_instance

        super(ModelType, self).__init__(validators=[validate_model] + validators, **kwargs)

    def __repr__(self):
        return object.__repr__(self)[:-1] + ' for %s>' % self.model_class

    def to_native(self, value, mapping=None, context=None):
        # We have already checked if the field is required. If it is None it
        # should continue being None
        if mapping is None:
            mapping = {}
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
                                 strict=self.strict)

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

        if shaped and len(shaped) == 0 and self.allow_none():
            return shaped
        elif shaped:
            return shaped
        elif print_none:
            return shaped


class ListType(MultiType):

    def __init__(self, field, min_size=None, max_size=None, **kwargs):

        if not isinstance(field, BaseType):
            compound_field = kwargs.pop('compound_field', None)
            field = self.init_compound_field(field, compound_field, **kwargs)

        self.field = field
        self.min_size = min_size
        self.max_size = max_size

        validators = [self.check_length, self.validate_items] + kwargs.pop("validators", [])

        super(ListType, self).__init__(validators=validators, **kwargs)

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
                return [value[unicode(k)] for k in sorted(map(int, value.keys()))]

            return list(value)
        except TypeError:
            return [value]

    def to_native(self, value, context=None):
        items = self._force_list(value)

        return [self.field.to_native(item, context) for item in items]

    def check_length(self, value):
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

    def validate_items(self, items):
        errors = []
        for item in items:
            try:
                self.field.validate(item)
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
                feels_empty = shaped and len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            # Print if we want empty or found a value
            if feels_empty and self.field.allow_none():
                data.append(shaped)
            elif shaped is not None:
                data.append(shaped)
            elif print_none:
                data.append(shaped)

        # Return data if the list contains anything
        if len(data) > 0:
            return data
        elif len(data) == 0 and self.allow_none():
            return data
        elif print_none:
            return data


class DictType(MultiType):

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

    def to_native(self, value, safe=False, context=None):
        if value == EMPTY_DICT:
            value = {}

        value = value or {}

        if not isinstance(value, dict):
            raise ValidationError(u'Only dictionaries may be used in a DictType')

        return dict((self.coerce_key(k), self.field.to_native(v, context))
                    for k, v in iteritems(value))

    def validate_items(self, items):
        errors = {}
        for key, value in iteritems(items):
            try:
                self.field.validate(value)
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
                feels_empty = shaped and len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            if feels_empty and self.field.allow_none():
                data[key] = shaped
            elif shaped is not None:
                data[key] = shaped
            elif print_none:
                data[key] = shaped

        if len(data) > 0:
            return data
        elif len(data) == 0 and self.allow_none():
            return data
        elif print_none:
            return data


class PolyModelType(MultiType):

    def __init__(self, model_classes, **kwargs):

        if isinstance(model_classes, type) and issubclass(model_classes, Model):
            self.model_classes = (model_classes,)
            allow_subclasses = True
        elif isinstance(model_classes, Iterable) \
          and not isinstance(model_classes, basestring):
            self.model_classes = tuple(model_classes)
            allow_subclasses = False
        else:
            raise Exception("The first argument to PolyModelType.__init__() "
                            "must be a model or an iterable.")

        validators = kwargs.pop("validators", [])
        self.strict = kwargs.pop("strict", True)
        self.claim_function = kwargs.pop("claim_function", None)
        self.allow_subclasses = kwargs.pop("allow_subclasses", allow_subclasses)

        def validate_model(model_instance):
            model_instance.validate()
            return model_instance

        MultiType.__init__(self, validators=[validate_model] + validators, **kwargs)

    def __repr__(self):
        return object.__repr__(self)[:-1] + ' for %s>' % str(self.model_classes)

    def is_allowed_model(self, model_instance):
        if self.allow_subclasses:
            if isinstance(model_instance, self.model_classes):
                return True
        else:
            if model_instance.__class__ in self.model_classes:
                return True
        return False

    def to_native(self, value, mapping=None, context=None):

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
                                 strict=self.strict)

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

        if shaped and len(shaped) == 0 and self.allow_none():
            return shaped
        elif shaped:
            return shaped
        elif print_none:
            return shaped


from ..models import Model
