# encoding=utf-8

from .exceptions import StopValidation, ValidationError
from .models import BaseModel


def _is_empty(field_value):
    if field_value is None:
        return True
    return False


def _validate(cls, needs_check, values, report_rogues=True):
    """Loops across the fields in a Model definition, `cls`, and attempts
    validation on any fields that require a check, as signalled by the
    `needs_check` function.

    The basis for validation is `cls`, so fields are located in `cls` and
    mapped to an entry in `values`.  This entry is then validated against the
    field's validation function.

    A (data, errors) tuple is returned::

        >>> items, errors = _validate(MyModel, lambda: True, foreign_data)
        >>> if not errors:
        >>>     model = MyModel(**items)
        >>> else:
        >>>     abort(422, errors=errors)
        >>>

    """

    if isinstance(cls, BaseModel):
        cls = cls.__class__

    assert issubclass(cls, BaseModel)

    data = {}
    errors = {}
    missing_error = u"This field is required"

    # Validate data based on cls's structure
    for field_name, field in cls._fields.items():
        # Rely on parameter for whether or not we should check value
        if needs_check(field_name, field):
            field_value = values.get(field_name)

            # If field is required and empty, set error
            if _is_empty(field_value):
                if field.required and (not field.dirty or not field._is_set):
                    errors[field_name] = [missing_error]
                    continue
                elif field.dirty or not field._is_set:
                    continue

            # Validate field value via call to BaseType._validate
            if field.validate(field_value):
                data[field_name] = field.clean
            else:
                errors[field_name] = field.errors

    # Report rogue fields as errors if `report_rogues`
    if report_rogues:
        rogues_found = set(values) - set(cls._fields)  # set takes iterables, iterating over keys in this instance
        if len(rogues_found) > 0:
            for field_name in rogues_found:
                errors[field_name] = [u'%s is an illegal field' % field_name]

    return data, errors


def validate_values(cls, values, report_rogues=True):
    """Validates `values` against a `class` definition or instance.  It takes
    care to ensure require fields are present and pass validation and
    """
    needs_check = lambda k, v: v.required or k in values
    return _validate(cls, needs_check, values, report_rogues=report_rogues)


def validate_instance(model, report_rogues=True):
    """Extracts the values from the model and validates them via a call to
    `validate_values`.
    """
    values = model._data
    needs_check = lambda k, v: v.required or k in values
    return _validate(model, needs_check, values, report_rogues=report_rogues)


def validate_partial(cls, values, report_rogues=True):
    """This function will validate values against fields of the same name in
    the model.  No checks for required fields are performed.

    The idea here is you might validate subcomponents of a document and then
    merge them later.
    """
    needs_check = lambda k, v: k in values
    return _validate(cls, needs_check, values, report_rogues=report_rogues)
