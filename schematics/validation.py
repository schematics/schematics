"""Validation

Validation is performed in a way that does not rely on Exceptions.  This means
the return values have significance, but they are easy enough to check.  The
goal of the validation system working this way is to increase awareness for how
success and errors are handled.

A structure inspired by Erlang's tagged tuples is used.  Schematics has a few
structures that represent inspection results that are implemented as
namedtuples.  Every tuple contains a `tag` and a `message`.  If more values are
stored, that is a detail of the implementation.

The tag itself is a mechanism for explicitly saying something happened.  Match
the 'OK' tag in an if statement and continue your flow.  If you don't have OK,
you must then handle the error.

I like this model significantly better than an exception oriented mechanism
exactly because the error handling is more explicit.

Validation now looks like this:

    result = validate_instance(some_instance)
    if result.tag == OK:
        print 'OK:', result.value
    else:
        print 'ERROR:', result.message
        handle_error(result)

Error cases will return a text representation of what happened for the message
value. This value will always be log-friendly.
"""

from .models import Model
from .exceptions import StopValidation, ValidationError


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

    if isinstance(cls, Model):
        cls = cls.__class__

    assert issubclass(cls, Model)

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
