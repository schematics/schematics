# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import itertools
import types
from collections import OrderedDict

from .common import *
from .datastructures import Context
from .exceptions import *
from .undefined import Undefined
from .util import listify
from .iteration import atoms, atom_filter
from .role import Role

from typing import *

if False:
    from .types.base import BaseType
    from .models import Model
    from .schema import Schema
    from .util import Constant

P = TypeVar('P')
N = TypeVar('N')

__all__ = []  # type: List[str]


###
# Transform loops
###


def import_loop(schema, mutable, raw_data=None, field_converter=None, trusted_data=None,
                mapping=None, partial=False, strict=False, init_values=False,
                apply_defaults=False, convert=True, validate=False, new=False,
                oo=False, recursive=False, app_data=None, context=None):
    # type: (Schema, Union[Model, MutableMapping], Optional[Mapping], Union[Converter, Callable], Optional[Mapping], Mapping[str, Union[str, List[str]]], bool, bool, Any, bool, Any, Any, Any, Any, Any, Optional[Any], Optional[Context]) -> Any
    """
    The import loop is designed to take untrusted data and convert it into the
    native types, as described in ``schema``.  It does this by calling
    ``field_converter`` on every field.

    Errors are aggregated and returned by throwing a ``ModelConversionError``.

    :param schema:
        The Schema to use as source for validation.
    :type schema: Schema

    :param mutable:
        A mapping or instance that can be changed during validation by Schema
        functions.
    :type mutable: Union[Model, MutableMapping]

    :param raw_data:
        A mapping to be converted into types according to ``schema``.
    :type raw_data: Optional[Mapping]

    :param field_converter:
        This function is applied to every field found in ``instance_or_dict``.
    :type field_converter: Union[Converter, Callable]

    :param trusted_data:
        A ``dict``-like structure that may contain already validated data.
    :type trusted_data: Optional[Mapping]

    :type mapping: Mapping[str, Union[str, List[str]]]

    :param partial:
        Allow partial data to validate; useful for PATCH requests.
        Essentially drops the ``required=True`` arguments from field
        definitions. Default: False
    :type partial: bool

    :param strict:
        Complain about unrecognized keys. Default: False
    :type strict: bool

    :param apply_defaults:
        Whether to set fields to their default values when not present in input data.
    :type apply_defaults: bool

    :param app_data:
        An arbitrary container for application-specific data that needs to
        be available during the conversion.
    :type app_data: Optional[Any]

    :param context:
        A ``Context`` object that encapsulates configuration options and ``app_data``.
        The context object is created upon the initial invocation of ``import_loop``
        and is then propagated through the entire process.
    :type context: Optional[Context]

    :rtype: Any
    """
    if raw_data is None:
        raw_data = mutable
    got_data = raw_data is not None

    context = Context._make(context)
    try:
        context.initialized
    except:
        if type(field_converter) is types.FunctionType:
            field_converter = BasicConverter(field_converter)
        context._setdefaults({
            'initialized': True,
            'field_converter': field_converter,
            'trusted_data': trusted_data or {},
            'mapping': mapping or {},
            'partial': partial,
            'strict': strict,
            'init_values': init_values,
            'apply_defaults': apply_defaults,
            'convert': convert,
            'validate': validate,
            'new': new,
            'oo': oo,
            'recursive': recursive,
            'app_data': app_data if app_data is not None else {}
        })

    raw_data = context.field_converter.pre(schema, raw_data, context)

    _field_converter = context.field_converter
    _model_mapping = context.mapping.get('model_mapping')

    data = dict(context.trusted_data) if context.trusted_data else {}
    errors = {}  # type: Dict[str, Union[str, FieldError, CompoundError]]

    if got_data and context.validate:
        errors = _mutate(schema, mutable, raw_data, context)

    if got_data:
        # Determine all acceptable field input names
        all_fields = schema.valid_input_keys
        if context.mapping:
            mapped_keys = (set(itertools.chain(*(
                          listify(input_keys) for target_key, input_keys in context.mapping.items()
                          if target_key != 'model_mapping'))))
            all_fields = all_fields | mapped_keys
        if context.strict:
            # Check for rogues if strict is set
            rogue_fields = set(raw_data) - all_fields
            if rogue_fields:
                for field in rogue_fields:
                    errors[field] = 'Rogue field'

    atoms_filter = None
    if not context.validate:
        # optimization: convert without validate doesn't require to touch setters
        atoms_filter = atom_filter.not_setter
    for field_name, field, value in atoms(schema, raw_data, filter=atoms_filter):
        serialized_field_name = field.serialized_name or field_name

        if got_data and value is Undefined:
            for key in field.get_input_keys(context.mapping):
                if key and key != field_name and key in raw_data:
                    value = raw_data[key]
                    break

        if value is Undefined:
            if field_name in data:
                continue
            if context.apply_defaults:
                value = field.default
        if value is Undefined and context.init_values:
            value = None

        if got_data:
            if field.is_compound:
                if context.trusted_data and context.recursive:
                    td = context.trusted_data.get(field_name)
                    if not all(hasattr(td, attr) for attr in ('keys', '__getitem__')):
                        td = {field_name: td}
                else:
                    td = {}
                if _model_mapping:
                    submap = _model_mapping.get(field_name)
                else:
                    submap = {}
                field_context = context._branch(trusted_data=td, mapping=submap)
            else:
                field_context = context
            try:
                value = _field_converter(field, value, field_context)
            except (FieldError, CompoundError) as exc:
                errors[serialized_field_name] = exc
                if context.apply_defaults:
                    value = field.default
                    if value is not Undefined:
                        data[field_name] = value
                if isinstance(exc, DataError):
                    data[field_name] = exc.partial_data
                continue

        if value is Undefined:
            continue

        data[field_name] = value

    if not context.validate:
        for field_name, field, value in atoms(schema, raw_data, filter=atom_filter.has_setter):
            data[field_name] = value

    if errors:
        raise DataError(errors, data)

    data = context.field_converter.post(schema, data, context)

    return data


def _mutate(schema, mutable, raw_data, context):
    """
    Mutates the converted data before validation. Allows Schema fields to modify
    and create data values on mutable.
    """
    errors = {}
    for field_name, field, value in atoms(schema, raw_data, filter=atom_filter.has_setter):
        if value is Undefined:
            continue
        try:
            value = context.field_converter(field, value, context)
            field.__set__(mutable, value)
        except (FieldError, CompoundError) as exc:
            serialized_field_name = field.serialized_name or field_name
            errors[serialized_field_name] = exc
            continue
        except AttributeError:
            pass
    raw_data.update((key, mutable[key]) for key in mutable)
    return errors


def export_loop(schema, instance_or_dict, field_converter=None, role=None, raise_error_on_role=True,
                export_level=None, app_data=None, context=None):
    # type: (Schema, Union[Model, Mapping], Union[Converter, Callable], Optional[str], bool, Any, Optional[Any], Optional[Context]) -> Dict[str, Any]
    """
    The export_loop function is intended to be a general loop definition that
    can be used for any form of data shaping, such as application of roles or
    how a field is transformed.

    :param schema:
        The Schema to use as source for validation.
    :type schema: Schema

    :param instance_or_dict:
        The structure where fields from schema are mapped to values. The only
        expectation for this structure is that it implements a ``dict``
        interface.
    :type instance_or_dict: Union[Model, Mapping]

    :param field_converter:
        This function is applied to every field found in ``instance_or_dict``.
    :type field_converter: Union[Converter, Callable]

    :param role:
        The role used to determine if fields should be left out of the
        transformation.
    :type role: Optional[str]

    :param raise_error_on_role:
        This parameter enforces strict behavior which requires substructures
        to have the same role definition as their parent structures.
    :type raise_error_on_role: bool

    :param export_level:
    :type export_level: Optional[Constant]

    :param app_data:
        An arbitrary container for application-specific data that needs to
        be available during the conversion.
    :type app_data: Optional[Any]

    :param context:
        A ``Context`` object that encapsulates configuration options and ``app_data``.
        The context object is created upon the initial invocation of ``import_loop``
        and is then propagated through the entire process.
    :type context: Optional[Context]

    :rtype: Dict[str, Any]
    """
    context = Context._make(context)
    try:
        context.initialized
    except:
        if type(field_converter) is types.FunctionType:
            field_converter = BasicConverter(field_converter)
        context._setdefaults({
            'initialized': True,
            'field_converter': field_converter,
            'role': role,
            'raise_error_on_role': raise_error_on_role,
            'export_level': export_level,
            'app_data': app_data if app_data is not None else {}
        })

    instance_or_dict = context.field_converter.pre(schema, instance_or_dict, context)

    if schema.options.export_order:
        data = OrderedDict()
    else:
        data = {}

    filter_func = (context.role if callable(context.role) else
        schema._options.roles.get(context.role))
    if filter_func is None:
        if context.role and context.raise_error_on_role:
            error_msg = '%s Model has no role "%s"'
            raise ValueError(error_msg % (schema.__name__, context.role))
        else:
            filter_func = schema.options.roles.get("default")

    _field_converter = context.field_converter

    for field_name, field, value in atoms(schema, instance_or_dict):
        serialized_name = field.serialized_name or field_name

        if filter_func is not None and filter_func(field_name, value):
            continue

        _export_level = field.get_export_level(context)

        if _export_level == DROP:
            continue

        elif value is not None and value is not Undefined:
            value = _field_converter(field, value, context)

        if value is Undefined:
            if _export_level <= DEFAULT:
                continue
        elif value is None:
            if _export_level <= NOT_NONE:
                continue
        elif field.is_compound and len(value) == 0:
            if _export_level <= NONEMPTY:
                continue

        if value is Undefined:
            value = None

        data[serialized_name] = value

    data = context.field_converter.post(schema, data, context)

    return data


###
# Field filtering
###


def wholelist(*field_list):
    """
    Returns a function that evicts nothing. Exists mainly to be an explicit
    allowance of all fields instead of a using an empty blacklist.
    """
    return Role(Role.wholelist, field_list)


def whitelist(*field_list):
    """
    Returns a function that operates as a whitelist for the provided list of
    fields.

    A whitelist is a list of fields explicitly named that are allowed.
    """
    return Role(Role.whitelist, field_list)


def blacklist(*field_list):
    """
    Returns a function that operates as a blacklist for the provided list of
    fields.

    A blacklist is a list of fields explicitly named that are not allowed.
    """
    return Role(Role.blacklist, field_list)


###
# Field converter interface
###


class Converter(object):

    def __call__(self, field, value, context):
        # type: (BaseType, Any, Context) -> Any
        raise NotImplementedError

    def pre(self, model_class, instance_or_dict, context):
        return instance_or_dict

    def post(self, model_class, data, context):
        return data


class BasicConverter(Converter):

    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        return self.func(*args)


###
# Standard export converters
###


@BasicConverter
def to_native_converter(field, value, context):
    # type: (BaseType[P, N], Any, Context) -> N
    return field.export(value, NATIVE, context)


@BasicConverter
def to_primitive_converter(field, value, context):
    # type: (BaseType[P, N], Any, Context) -> P
    return field.export(value, PRIMITIVE, context)


###
# Standard import converters
###


@BasicConverter
def import_converter(field, value, context):
    # type: (BaseType, Any, Context) -> Any
    field.check_required(value, context)
    if value is None or value is Undefined:
        return value
    return field.convert(value, context)


@BasicConverter
def validation_converter(field, value, context):
    # type: (BaseType, Any, Context) -> Any
    field.check_required(value, context)
    if value is None or value is Undefined:
        return value
    return field.validate(value, context)


###
# Context stub factories
###


def get_import_context(field_converter=import_converter, **options):
    import_options = {
        'field_converter': field_converter,
        'partial': False,
        'strict': False,
        'convert': True,
        'validate': False,
        'new': False,
        'oo': False
    }
    import_options.update(options)
    return Context(**import_options)


def get_export_context(field_converter=to_native_converter, **options):
    export_options = {
        'field_converter': field_converter,
        'export_level': None
    }
    export_options.update(options)
    return Context(**export_options)


###
# Import and export functions
###


def convert(cls, mutable, raw_data=None, **kwargs):
    return import_loop(cls, mutable, raw_data, import_converter, **kwargs)


def to_native(cls, instance_or_dict, **kwargs):
    return export_loop(cls, instance_or_dict, to_native_converter, **kwargs)


def to_primitive(cls, instance_or_dict, **kwargs):
    return export_loop(cls, instance_or_dict, to_primitive_converter, **kwargs)
