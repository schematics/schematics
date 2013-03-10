"""
"""

from exceptions import ValidationError


def _is_empty(field_value):
    ### TODO if field_value is None, skip  ### TODO makea parameter
    if field_value is None:
        return True
    # treat empty strings as empty values and skip
    if isinstance(field_value, (str, unicode)) and \
           len(field_value.strip()) == 0:
        return True
    return False


def _validate(cls, needs_check, values, report_rogues=False):
    """TODO
    """
    ### Reject model if _fields isn't present
    if not hasattr(cls, '_fields'):
        error_msg = 'cls is not a Model instance'
        raise ValidationError(error_msg)

    ### Containers for results
    new_data = {}
    errors = []

    ### Validate data based on cls's structure
    for field_name, field in cls._fields.items():
        ### Rely on parameter for whether or not we should check value
        if needs_check(field_name, field):
            try:
                field_value = values[field_name]
            except KeyError:
                field_value = None

            ### TODO - this will be the new validation system soon
            if _is_empty(field_value):
                if field.required:
                    error_msg = "Required field (%s) not found" % field_name
                    errors.append(error_msg)
                continue

            ### Validate field value via call to BaseType._validate
            try:
                field._validate(field_value)
                ### TODO clean this
                result = field.for_python(field_value)
                new_data[field_name] = result
            except ValidationError, ve:
                errors.append(ve.messages)

    ### Report rogue fields as errors if `report_rogues`
    if report_rogues:
        class_fields = cls._fields.keys()
        rogues_found = set(values.keys()) - set(class_fields)
        if len(rogues_found) > 0:
            for field_name in rogues_found:
                error_msg = 'Unknown field found'
                field_value = values[field_name]
                errors.append(error_msg)

    ### Return on if errors were found
    if len(errors) > 0:
        error_msg = 'Model validation errors'
        raise ValidationError(error_msg)

    return new_data


def validate_values(cls, values):
    """Validates `values` against a `class` definition or instance.  It takes
    care to ensure require fields are present and pass validation and
    """
    needs_check = lambda k, v: v.required or k in values
    return _validate(cls, needs_check, values)


def validate_instance(model):
    """Extracts the values from the model and validates them via a call to
    `validate_values`.
    """
    values = model._data if hasattr(model, '_data') else {}
    needs_check = lambda k, v: v.required or k in values
    return _validate(model, needs_check, values)


def validate_partial(cls, values):
    """This function will validate values against fields of the same name in
    the model.  No checks for required fields are performed.

    The idea here is you might validate subcomponents of a document and then
    merge them later.
    """
    needs_check = lambda k, v: k in values
    return _validate(cls, needs_check, values)
