from .exceptions import BaseError, ValidationError


def validate(cls, raw_data, partial=False, strict=False, context=None):
    """
    Validate some untrusted data using a model. Trusted data can be passed in
    the `context` parameter.

    :param cls:
        The model class to use as source for validation. If given an instance,
        will also run instance-level validators on the data.
    :param raw_data:
        A ``dict`` or ``dict``-like structure for incoming data.
    :param partial:
        Allow partial data to validate; useful for PATCH requests.
        Essentially drops the ``required=True`` arguments from field
        definitions. Default: False
    :param strict:
        Complain about unrecognized keys. Default: False
    :param context:
        A ``dict``-like structure that may contain already validated data.

    :returns: data
        data dict contains the valid raw_data plus the context data.
        If errors are found, they are raised as a ValidationError with a list
        of errors attached.
    """
    data = dict(context) if context is not None else {}
    errors = {}

    # validate raw_data by the model fields
    for field_name, field in cls._fields.iteritems():
        serialized_field_name = field.serialized_name or field_name
        try:
            if serialized_field_name in raw_data:
                value = raw_data[serialized_field_name]
            else:
                value = raw_data[field_name]
        except KeyError:
            if data.get(field_name):
                # skip already validated data
                continue
            value = field.default

        if value is None:
            if field.required and not partial:
                errors[serialized_field_name] = [field.messages['required'], ]
        else:
            try:
                if value is not None:
                    value = field.convert(value)
                field.validate(value)
                data[field_name] = value
            except BaseError as e:
                errors[serialized_field_name] = e.messages

    if strict:
        rogue_field_errors = _check_for_unknown_fields(cls, data)
        errors.update(rogue_field_errors)

    # validate a model with its own validators
    instance_errors = _validate_model(cls, data)
    errors.update(instance_errors)

    if len(errors) > 0:
        raise ValidationError(errors)

    return data


def _validate_model(cls, data):
    """
    Validate data using model level methods.

    :param cls:
        The Model class to validate ``data`` against.

    :param data:
        A dict with data to validate. Invalid items are removed from it.

    :returns:
        Errors of the fields that did not pass validation.
    """
    errors = {}
    for field_name, value in data.items():
        if field_name in cls._validator_functions:
            try:
                context = data
                if hasattr(cls, '_data'):
                    context = dict(cls._data, **data)
                cls._validator_functions[field_name](cls, context, value)
            except BaseError as e:
                field = cls._fields[field_name]
                serialized_field_name = field.serialized_name or field_name
                errors[serialized_field_name] = e.messages
                data.pop(field_name, None)  # get rid of the invalid field
    return errors


def _check_for_unknown_fields(cls, data):
    """
    Checks for keys in a dictionary that don't exist as fields on a model.

    :param cls:
        The ``Model`` class to validate ``data`` against.

    :param data:
        A dict with keys to validate.

    :returns:
        Errors of the fields that were not present in ``cls``.
    """
    errors = {}
    rogues_found = set(data) - set(cls._fields)
    if len(rogues_found) > 0:
        for field_name in rogues_found:
            errors[field_name] = [u'%s is an illegal field.' % field_name]
    return errors
