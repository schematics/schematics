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


def validate(cls, values, partial=False, strict=False):
    ### Reject model if _fields isn't present
    if not hasattr(cls, '_fields'):
        error_msg = 'cls is not a Model instance'
        raise ValidationError(error_msg)

    ### Containers for results
    new_data = {}
    errors = {}

    if partial:
        needs_check = lambda k, v: k in values
    else:
        needs_check = lambda k, v: v.required or k in values

    ### Validate data based on cls's structure
    for field_name, field in cls._fields.items():
        ### Rely on parameter for whether or not we should check value
        if needs_check(field_name, field):
            try:
                field_value = values[field_name]
            except KeyError:
                field_value = None

            ### TODO - this will be the new validation system soon
            if _is_empty(field_value) and field.required:
                errors[field_name] = [u"This field is required"]
                continue

            ### Validate field value via call to BaseType._validate
            elif not _is_empty(field_value):
                try:
                    ### TODO incorrectly handling None ModelType values
                    field._validate(field_value)
                    ### TODO clean this
                    result = field.for_python(field_value)
                    new_data[field_name] = result
                except ValidationError, ve:
                    errors[field_name] = ve.messages
                    raise ve
    
    ### Report rogue fields as errors if `strict`
    if strict:
        class_fields = cls._fields.keys()
        rogues_found = set(values.keys()) - set(class_fields)
        if len(rogues_found) > 0:
            for field_name in rogues_found:
                error_msg = 'Unknown field found'
                field_value = values[field_name]
                errors[field_name] = error_msg

    ### Return on if errors were found
    if len(errors) > 0:
        raise ValidationError(errors)

    return new_data
