# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import inspect
import functools

from .common import *
from .datastructures import Context
from .exceptions import FieldError, DataError
from .transforms import import_loop, validation_converter
from .undefined import Undefined
from .iteration import atoms

if False:
    from typing import *
    from .models import Model
    from .schema import Schema
    from .exceptions import ErrorMessage

__all__ = []  # type: List[str]

# FIXME: validators with different signature are expected in different contexts.  determine where.
ValidatorType = 'Callable[[Any, Context], Any]'
# ValidatorType3 = 'Callable[[Any, 'Context'], Any]'
ValidatorType4 = 'Callable[[MutableMapping[str, Any], Mapping[str, Any], Any, Context], Any]'


def validate(schema, mutable, raw_data=None, trusted_data=None,
             partial=False, strict=False, convert=True, context=None, **kwargs):
    # type: (Union[Type[Model], Schema], MutableMapping[str, Any], Mapping[str, Any], Mapping[str, Any], bool, bool, bool, Any, Any) -> Dict
    """
    Validate some untrusted data using a model. Trusted data can be passed in
    the `trusted_data` parameter.

    :param schema:
        The Schema to use as source for validation.
    :type schema: Union[Type[Model], Schema]

    :param mutable:
        A mapping or instance that can be changed during validation by Schema
        functions.
    :type mutable: Union[MutableMapping, Model]

    :param raw_data:
        A mapping or instance containing new data to be validated.
    :type raw_data: Union[Mapping, Model]

    :param partial:
        Allow partial data to validate; useful for PATCH requests.
        Essentially drops the ``required=True`` arguments from field
        definitions. Default: False
    :type partial: bool

    :param strict:
        Complain about unrecognized keys. Default: False
    :type strict: bool

    :param trusted_data:
        A ``dict``-like structure that may contain already validated data.
    :type trusted_data: Mapping[str, Any]

    :param convert:
        Controls whether to perform import conversion before validating.
        Can be turned off to skip an unnecessary conversion step if all values
        are known to have the right datatypes (e.g., when validating immediately
        after the initial import). Default: True
    :type convert: bool

    :returns: data
        ``dict`` containing the valid raw_data plus ``trusted_data``.
        If errors are found, they are raised as a ValidationError with a list
        of errors attached.
    :rtype: Dict
    """
    if raw_data is None:
        raw_data = mutable

    context = context or get_validation_context(partial=partial, strict=strict,
        convert=convert)

    errors = {}  # type: Dict[str, List[ErrorMessage]]
    try:
        data = import_loop(schema, mutable, raw_data, trusted_data=trusted_data,
            context=context, **kwargs)
    except DataError as exc:
        errors = dict(exc.errors)
        data = exc.partial_data

    errors.update(_validate_model(schema, mutable, data, context))

    if errors:
        raise DataError(errors, data)

    return data


def _validate_model(schema, mutable, data, context):
    # type: (Union[Type[Model], Schema], MutableMapping[str, Any], MutableMapping[str, Any], Context) -> Dict[str, List[ErrorMessage]]
    """
    Validate data using model level methods.

    :param schema:
        The Schema to validate ``data`` against.
    :type schema: Schema

    :param mutable:
        A mapping or instance that will be passed to the validator containing
        the original data and that can be mutated.
    :type mutable: Union[MutableMapping, Model]

    :param data:
        A dict with data to validate. Invalid items are removed from it.

    :returns:
        Errors of the fields that did not pass validation.
    :rtype: Dict[str, List[ErrorMessage]]
    """
    from .models import Model
    if isinstance(schema, type) and issubclass(schema, Model):
        schema = schema._schema

    errors = {}
    invalid_fields = []  # type: List[str]

    has_validator = lambda atom: (
        atom.value is not Undefined and
        atom.name in schema.validators
    )
    for field_name, field, value in atoms(schema, data, filter=has_validator):
        try:
            schema.validators[field_name](mutable, data, value, context)
        except (FieldError, DataError) as exc:
            serialized_field_name = field.serialized_name or field_name
            errors[serialized_field_name] = exc.errors
            invalid_fields.append(field_name)

    for field_name in invalid_fields:
        # FIXME: consider `del data[field_name]` to simplify the protocol requirement for data
        data.pop(field_name)

    return errors


def get_validation_context(**options):
    validation_options = {
        'field_converter': validation_converter,
        'partial': False,
        'strict': False,
        'convert': True,
        'validate': True,
        'new': False,
    }
    validation_options.update(options)
    return Context(**validation_options)


def prepare_validator(func, argcount):
    # type: (Callable, int) -> Callable
    if isinstance(func, classmethod):
        func = func.__get__(object).__func__
    if len(inspect.getargspec(func).args) < argcount:
        @functools.wraps(func)
        def newfunc(*args, **kwargs):
            if not kwargs or kwargs.pop('context', 0) is 0:
                args = args[:-1]
            return func(*args, **kwargs)
        return newfunc
    return func
