#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from ..exceptions import ValidationError, ConversionError, ModelValidationError, StopValidation
from .base import BaseType


class MultiType(BaseType):

    def validate(self, value):
        """Report dictionary of errors with lists of errors as values of each
        key. Used by ModelType and ListType.

        """
        errors = {}

        for validator in self.validators:
            try:
                validator(value)
            except ModelValidationError, e:
                errors.update(e.messages)

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

        validators = kwargs.pop("validators", [])

        def validate_model(model_instance):
            model_instance.validate()
            return model_instance

        super(ModelType, self).__init__(validators=[validate_model] + validators,  **kwargs)

    def __repr__(self):
        return object.__repr__(self)[:-1] + ' for %s>' % self.model_class

    def convert(self, value):
        if value is None:  # We have already checked if the field is required. If it is None it should continue being None
            return None

        if isinstance(value, self.model_class):
            return value

        if not isinstance(value, dict):
            raise ConversionError(u'Please use a mapping for this field or {} instance instead of {}.'.format(
                self.model_class.__name__,
                type(value).__name__))

        # We don't allow partial submodels because that is just complex and
        # not obviously useful
        return self.model_class(value)

    def to_primitive(self, model_instance, include_serializables=True):
        primitive_data = {}
        for field_name, field, value in model_instance.atoms(include_serializables):
            serialized_name = field.serialized_name or field_name

            if value is None:
                if field.serialize_when_none or (field.serialize_when_none is None and self.model_class._options.serialize_when_none):
                    primitive_data[serialized_name] = None
            else:
                primitive_data[serialized_name] = field.to_primitive(value)

        return primitive_data

    def filter_by_role(self, model_instance, primitive_data, role, raise_error_on_role=False, include_serializables=True):
        if model_instance is None:
            return primitive_data

        gottago = lambda k, v: False
        if role in self.model_class._options.roles:
            gottago = self.model_class._options.roles[role]
        elif role and raise_error_on_role:
            raise ValueError(u'%s Model has no role "%s"' % (
                self.model_class.__name__, role))

        for field_name, field, value in model_instance.atoms(include_serializables):
            serialized_name = field.serialized_name or field_name
            if not serialized_name in primitive_data:
                continue

            if gottago(field_name, value):
                primitive_data.pop(serialized_name)
            elif isinstance(field, MultiType):
                primitive_value = primitive_data.get(serialized_name)
                if primitive_value:
                    field.filter_by_role(
                        value,
                        primitive_value,
                        role
                    )
                if not primitive_value:
                    if not (field.serialize_when_none or
                        (field.serialize_when_none is None and self.model_class._options.serialize_when_none)):
                        primitive_data.pop(serialized_name)

        return primitive_data if len(primitive_data) > 0 else None
        

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
                return [value[str(k)] for k in sorted(map(int, value.keys()))]

            return list(value)
        except TypeError:
            return [value]

    def convert(self, value):
        items = self._force_list(value)

        return map(self.field.convert, items)

    def check_length(self, value):
        list_length = len(value) if value else 0

        if self.min_size is not None and list_length < self.min_size:
            message = ({
                True: u'Please provide at least %d item.',
                False: u'Please provide at least %d items.'}[self.min_size == 1]
            ) % self.min_size
            raise ValidationError(message)

        if self.max_size is not None and list_length > self.max_size:
            message = ({
                True: u'Please provide no more than %d item.',
                False: u'Please provide no more than %d items.'}[self.max_size == 1]
            ) % self.max_size
            raise ValidationError(message)

    def validate_items(self, items):
        errors = []
        for idx, item in enumerate(items, 1):
            try:
                self.field.validate(item)
            except ValidationError, e:
                errors.append(e.message)

        if errors:
            raise ValidationError(errors)

    def to_primitive(self, value):
        return map(self.field.to_primitive, value)

    def filter_by_role(self, clean_list, primitive_list, role, raise_error_on_role=False):
        if isinstance(self.field, MultiType):
            for clean_value, primitive_value in zip(clean_list, primitive_list):
                self.field.filter_by_role(clean_value, primitive_value, role)
                if not primitive_value:
                    if not (self.field.serialize_when_none or
                        (self.field.serialize_when_none is None and self.model_class._options.serialize_when_none)):
                        primitive_list.remove(primitive_value)

        return primitive_list if len(primitive_list) > 0 else None

EMPTY_DICT = "{}"


class DictType(MultiType):

    def __init__(self, field, coerce_key=None, **kwargs):
        if not isinstance(field, BaseType):
            field = field(**kwargs)

        self.coerce_key = coerce_key or str
        self.field = field

        validators = [self.validate_items] + kwargs.pop("validators", [])

        super(DictType, self).__init__(validators=validators, **kwargs)

    @property
    def model_class(self):
        return self.field.model_class

    def convert(self, value, safe=False):
        if value == EMPTY_DICT:
            value = {}

        value = value or {}

        if not isinstance(value, dict):
            raise ValidationError(u'Only dictionaries may be used in a DictType')

        return dict((self.coerce_key(k), self.field.convert(v))
                    for k, v in value.iteritems())

    def validate_items(self, items):
        errors = {}
        for key, value in items.iteritems():
            try:
                self.field.validate(value)
            except ValidationError, e:
                errors[key] = e

        if errors:
            raise ValidationError(errors)

    def to_primitive(self, value):
        return dict((unicode(k), self.field.to_primitive(v)) for k, v in value.iteritems())

    def filter_by_role(self, clean_data, primitive_data, role, raise_error_on_role=False):
        if clean_data is None:
            return primitive_data

        if isinstance(self.field, MultiType):
            for key, clean_value in clean_data.iteritems():
                primitive_value = primitive_data[unicode(key)]

                self.field.filter_by_role(clean_value, primitive_value, role)

                if not primitive_value:
                    if not (self.field.serialize_when_none or
                        (self.field.serialize_when_none is None and self.model_class._options.serialize_when_none)):
                        primitive_data.pop(unicode(key))

        return primitive_data if len(primitive_data) > 0 else None
