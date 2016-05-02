# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import collections
import itertools
import operator
import types

from .common import * # pylint: disable=redefined-builtin
from .datastructures import Context
from .exceptions import *
from .undefined import Undefined
from .util import listify

try:
    from collections import OrderedDict
except ImportError:
    from .datastructures import OrderedDict



###
# Transform loops
###


def import_loop(cls, instance_or_dict, field_converter=None, trusted_data=None,
                mapping=None, partial=False, strict=False, init_values=False,
                apply_defaults=False, convert=True, validate=False, new=False,
                oo=False, recursive=False, app_data=None, context=None):
    """
    The import loop is designed to take untrusted data and convert it into the
    native types, as described in ``cls``.  It does this by calling
    ``field_converter`` on every field.

    Errors are aggregated and returned by throwing a ``ModelConversionError``.

    :param cls:
        The class for the model.
    :param instance_or_dict:
        A dict of data to be converted into types according to ``cls``.
    :param field_converter:
        This function is applied to every field found in ``instance_or_dict``.
    :param trusted_data:
        A ``dict``-like structure that may contain already validated data.
    :param partial:
        Allow partial data to validate; useful for PATCH requests.
        Essentially drops the ``required=True`` arguments from field
        definitions. Default: False
    :param strict:
        Complain about unrecognized keys. Default: False
    :param apply_defaults:
        Whether to set fields to their default values when not present in input data.
    :param app_data:
        An arbitrary container for application-specific data that needs to
        be available during the conversion.
    :param context:
        A ``Context`` object that encapsulates configuration options and ``app_data``.
        The context object is created upon the initial invocation of ``import_loop``
        and is then propagated through the entire process.
    """
    if instance_or_dict is None:
        got_data = False
    else:
        got_data = True

    if got_data and not isinstance(instance_or_dict, (cls, dict)):
        raise ConversionError('Model conversion requires a model or dict')

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

    instance_or_dict = context.field_converter.pre(cls, instance_or_dict, context)

    _field_converter = context.field_converter
    _model_mapping = context.mapping.get('model_mapping')

    data = dict(context.trusted_data) if context.trusted_data else {}
    errors = {}

    if got_data:
        # Determine all acceptable field input names
        all_fields = cls._valid_input_keys
        if context.mapping:
            mapped_keys = (set(itertools.chain(*(
                          listify(input_keys) for target_key, input_keys in context.mapping.items()
                          if target_key != 'model_mapping'))))
            all_fields = all_fields | mapped_keys
        if context.strict:
            # Check for rogues if strict is set
            rogue_fields = set(instance_or_dict) - all_fields
            if rogue_fields:
                for field in rogue_fields:
                    errors[field] = 'Rogue field'

    for field_name, field in cls._field_list:

        value = Undefined
        serialized_field_name = field.serialized_name or field_name

        if got_data:
            for key in field.get_input_keys(context.mapping):
                if key and key in instance_or_dict:
                    value = instance_or_dict[key]
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
                if isinstance(exc, DataError):
                    data[field_name] = exc.partial_data
                continue

        if value is Undefined:
            continue

        data[field_name] = value

    if errors:
        raise DataError(errors, data)

    data = context.field_converter.post(cls, data, context)

    return data


def export_loop(cls, instance_or_dict, field_converter=None, role=None, raise_error_on_role=True,
                export_level=None, app_data=None, context=None):
    """
    The export_loop function is intended to be a general loop definition that
    can be used for any form of data shaping, such as application of roles or
    how a field is transformed.

    :param cls:
        The model definition.
    :param instance_or_dict:
        The structure where fields from cls are mapped to values. The only
        expectionation for this structure is that it implements a ``dict``
        interface.
    :param field_converter:
        This function is applied to every field found in ``instance_or_dict``.
    :param role:
        The role used to determine if fields should be left out of the
        transformation.
    :param raise_error_on_role:
        This parameter enforces strict behavior which requires substructures
        to have the same role definition as their parent structures.
    :param app_data:
        An arbitrary container for application-specific data that needs to
        be available during the conversion.
    :param context:
        A ``Context`` object that encapsulates configuration options and ``app_data``.
        The context object is created upon the initial invocation of ``import_loop``
        and is then propagated through the entire process.
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

    instance_or_dict = context.field_converter.pre(cls, instance_or_dict, context)

    if cls._options.export_order:
        data = OrderedDict()
    else:
        data = {}

    filter_func = cls._options.roles.get(context.role)
    if filter_func is None:
        if context.role and context.raise_error_on_role:
            error_msg = '%s Model has no role "%s"'
            raise ValueError(error_msg % (cls.__name__, context.role))
        else:
            filter_func = cls._options.roles.get("default")

    _field_converter = context.field_converter

    for field_name, field, value in atoms(cls, instance_or_dict):
        serialized_name = field.serialized_name or field_name

        if filter_func is not None and filter_func(field_name, value):
            continue

        _export_level = field.get_export_level(context)

        if _export_level == DROP:
            continue

        elif value not in (None, Undefined):
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

    data = context.field_converter.post(cls, data, context)

    return data


def atoms(cls, instance_or_dict):
    """
    Iterator for the atomic components of a model definition and relevant
    data that creates a 3-tuple of the field's name, its type instance and
    its value.

    :param cls:
        The model definition.
    :param instance_or_dict:
        The structure where fields from cls are mapped to values. The only
        expectation for this structure is that it implements a ``Mapping``
        interface.
    """
    field_getter = serializable_getter = instance_or_dict.get
    try:
        field_getter = instance_or_dict._data.get
    except AttributeError:
        pass

    sequences = ((cls._field_list, field_getter),
                 (cls._serializables.items(), serializable_getter))
    for sequence, get in sequences:
        for field_name, field in sequence:
            yield (field_name, field, get(field_name, Undefined))



###
# Field filtering
###

@str_compat
class Role(collections.Set):

    """
    A ``Role`` object can be used to filter specific fields against a sequence.

    The ``Role`` is two things: a set of names and a function.  The function
    describes how filter taking a field name as input and then returning either
    ``True`` or ``False``, indicating that field should or should not be
    skipped.

    A ``Role`` can be operated on as a ``Set`` object representing the fields
    is has an opinion on.  When Roles are combined with other roles, the
    filtering behavior of the first role is used.
    """

    def __init__(self, function, fields):
        self.function = function
        self.fields = set(fields)

    def _from_iterable(self, iterable):
        return Role(self.function, iterable)

    def __contains__(self, value):
        return value in self.fields

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def __eq__(self, other):
        return (self.function.__name__ == other.function.__name__ and
                self.fields == other.fields)

    def __str__(self):
        return '%s(%s)' % (self.function.__name__,
                           ', '.join("'%s'" % f for f in self.fields))

    def __repr__(self):
        return '<Role %s>' % str(self)

    # edit role fields
    def __add__(self, other):
        fields = self.fields.union(other)
        return self._from_iterable(fields)

    def __sub__(self, other):
        fields = self.fields.difference(other)
        return self._from_iterable(fields)

    # apply role to field
    def __call__(self, name, value):
        return self.function(name, value, self.fields)

    # static filter functions
    @staticmethod
    def wholelist(name, value, seq):
        """
        Accepts a field name, value, and a field list.  This functions
        implements acceptance of all fields by never requesting a field be
        skipped, thus returns False for all input.

        :param name:
            The field name to inspect.
        :param value:
            The field's value.
        :param seq:
            The list of fields associated with the ``Role``.
        """
        return False

    @staticmethod
    def whitelist(name, value, seq):
        """
        Implements the behavior of a whitelist by requesting a field be skipped
        whenever it's name is not in the list of fields.

        :param name:
            The field name to inspect.
        :param value:
            The field's value.
        :param seq:
            The list of fields associated with the ``Role``.
        """

        if seq is not None and len(seq) > 0:
            return name not in seq
        return True

    @staticmethod
    def blacklist(name, value, seq):
        """
        Implements the behavior of a blacklist by requesting a field be skipped
        whenever it's name is found in the list of fields.

        :param k:
            The field name to inspect.
        :param v:
            The field's value.
        :param seq:
            The list of fields associated with the ``Role``.
        """
        if seq is not None and len(seq) > 0:
            return name in seq
        return False


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
    return field.export(value, NATIVE, context)


@BasicConverter
def to_primitive_converter(field, value, context):
    return field.export(value, PRIMITIVE, context)



###
# Standard import converters
###


@BasicConverter
def import_converter(field, value, context):
    field.check_required(value, context)
    if value in (None, Undefined):
        return value
    return field.convert(value, context)


@BasicConverter
def validation_converter(field, value, context):
    field.check_required(value, context)
    if value in (None, Undefined):
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


def convert(cls, instance_or_dict, **kwargs):
    return import_loop(cls, instance_or_dict, import_converter, **kwargs)


def to_native(cls, instance_or_dict, **kwargs):
    return export_loop(cls, instance_or_dict, to_native_converter, **kwargs)


def to_primitive(cls, instance_or_dict, **kwargs):
    return export_loop(cls, instance_or_dict, to_primitive_converter, **kwargs)



__all__ = module_exports(__name__)

