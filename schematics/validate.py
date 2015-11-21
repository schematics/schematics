from .exceptions import BaseError, ValidationError, ModelConversionError


def validate(cls, instance_or_dict, partial=False, strict=False, trusted_data=None,
             app_data=None, context=None):
    """
    Validate some untrusted data using a model. Trusted data can be passed in
    the `trusted_data` parameter.

    :param cls:
        The model class to use as source for validation. If given an instance,
        will also run instance-level validators on the data.
    :param instance_or_dict:
        A ``dict`` or ``dict``-like structure for incoming data.
    :param partial:
        Allow partial data to validate; useful for PATCH requests.
        Essentially drops the ``required=True`` arguments from field
        definitions. Default: False
    :param strict:
        Complain about unrecognized keys. Default: False
    :param trusted_data:
        A ``dict``-like structure that may contain already validated data.

    :returns: data
        ``dict`` containing the valid raw_data plus ``trusted_data``.
        If errors are found, they are raised as a ValidationError with a list
        of errors attached.
    """
    data = {}
    errors = {}

    # Function for validating an individual field
    def field_converter(field, value, context):
        return field.validate(value, context)

    # Loop across fields and coerce values
    try:
        data = import_loop(cls, instance_or_dict, field_converter,
                           trusted_data=trusted_data, partial=partial, strict=strict,
                           app_data=app_data, context=context)
    except ModelConversionError as mce:
        errors = mce.messages

    # Check if unknown fields are present
    if strict:
        rogue_field_errors = _check_for_unknown_fields(cls, data)
        errors.update(rogue_field_errors)

    # Model level validation
    instance_errors = _validate_model(cls, data, context)
    errors.update(instance_errors)

    if errors:
        raise ValidationError(errors)

    return data


def _validate_model(cls, data, context):
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
    invalid_fields = []
    for field_name, field in cls._fields.iteritems():
        if field_name in cls._validator_functions and field_name in data:
            value = data[field_name]
            try:
                cls._validator_functions[field_name](cls, data, value, context)
            except BaseError as exc:
                field = cls._fields[field_name]
                serialized_field_name = field.serialized_name or field_name
                errors[serialized_field_name] = exc.messages
                invalid_fields.append(field_name)

    for field_name in invalid_fields:
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
    fields = set(getattr(cls, '_initial', {})) | set(data)
    rogues_found = fields - set(cls._fields)
    if rogues_found:
        for field_name in rogues_found:
            errors[field_name] = [u'%s is an illegal field.' % field_name]
    return errors


from .transforms import import_loop
