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
you must then handle the error.  I like this model significantly better than an
exception oriented mechanism.

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

from collections import namedtuple


OK = 'OK'

###
### If an unusual case is found, the result passes back the data that attempted
### validation in addition to a list of the found errors.
###
ERROR_INVALID_TYPE = 'ERROR_INVALID_TYPE'  # NotATypeException
ERROR_FIELD_TYPE_CHECK = 'ERROR_FIELD_TYPE_CHECK'  # TypeException
ERROR_MODEL_TYPE_CHECK = 'ERROR_MODEL_TYPE_CHECK'  # ModelException


### Containers
ConversionResult = namedtuple('ConversionResult', 'tag message')
ModelResult = namedtuple('ModelResult', 'tag message model value')
TypeResult = namedtuple('TypeResult', 'tag message name value')


###
### Validation Functions
###

def _gen_handle_exception(validate_all, exception_list):
    """Generates a function for either raising exceptions or collecting
    them in a list.
    """
    if validate_all:
        def handle_exception(e):
            exception_list.append(e)
    else:
        def handle_exception(e):
            raise e

    return handle_exception


def _gen_handle_class_field(delete_rogues, field_list):
    """Generates a function that either accumulates observed fields or
    makes no attempt to collect them.

    The case where nothing accumulates is to prevent growing data
    schematics unnecessarily.
    """
    if delete_rogues:
        def handle_class_field(cf):
            field_list.append(cf)
    else:
        def handle_class_field(cf):
            pass

    return handle_class_field


def _validate_helper(cls, field_inspector, values, validate_all=False,
                     delete_rogues=True):
    """This is a convenience function that loops over the given values
    and attempts to validate them against the class definition. It only
    validates the data in values and does not guarantee a complete model
    is present.

    'not present' is defined as not having a value OR having '' (or u'')
    as a value.
    """
    if not hasattr(cls, '_fields'):
        error_msg = 'cls is not a Model instance'
        return ModelResult(ERROR_MODEL_TYPE_CHECK, error_msg, cls, values)

    # Create function for handling exceptions
    errors = list()
    handle_exception = _gen_handle_exception(validate_all, errors)

    # Create function for handling a flock of frakkin palins (rogue fields)
    data_fields = set(values.keys())
    class_fields = list()
    handle_class_field = _gen_handle_class_field(delete_rogues,
                                                 class_fields)

    # Loop across fields present in model
    for k, v in cls._fields.items():

        handle_class_field(k)

        if field_inspector(k, v):
            datum = values[k]
            # if datum is None, skip  ### TODO makea parameter
            if datum is None:
                continue
            # treat empty strings as empty values and skip
            if isinstance(datum, (str, unicode)) and \
                   len(datum.strip()) == 0:
                continue
            result = v.validate(datum)
            if result.tag != OK:
                handle_exception(result)

    # Remove rogue fields
    if len(class_fields) > 0:  # if accumulation is not disabled
        palins = data_fields - set(class_fields)
        for rogue_field in palins:
            del values[rogue_field]

    # Reaches here only if exceptions are aggregated or validation passed
    if len(errors) > 0:
        error_msg = 'Multiple validation errors'
        return ModelResult(ERROR_MODEL_TYPE_CHECK, error_msg, cls, errors)
    else:
        return ModelResult(OK, 'success', cls, values)


def validate_instance(model, validate_all=False):
    """Ensure that all fields' values are valid and that required fields
    are present.

    Throws a ModelException if Model is invalid
    """
    # Get a list of tuples of field names and their current values
    fields = [(field, getattr(model, name))
              for name, field in model._fields.items()]

    # Ensure that each field is matched to a valid value
    errs = []
    for field, value in fields:
        err = None
        # treat empty strings as nonexistent
        if value is not None and value != '':
            result = field._validate(value)
            if result.tag != OK:
                err = result
        elif field.required:
            error_msg = 'Required field missing'
            err = TypeResult(ERROR_MODEL_TYPE_CHECK, error_msg,
                             field.field_name, value)

        # If validate_all, save errors to a list
        if err and validate_all:
            errs.append(err)
            
        # Otherwise, throw the first error
        elif err:
            return err

    if errs:
        error_msg = 'Errors in fields found',
        return ModelResult(ERROR_MODEL_TYPE_CHECK, error_msg, model, errs)
    
    return ModelResult(OK, 'success', model, None)


def validate_class_fields(cls, values, validate_all=False):
    """This is a convenience function that loops over _fields in
    cls to validate them. If the field is not required AND not present,
    it is skipped.
    """
    fun = lambda k, v: v.required or k in values
    return _validate_helper(cls, fun, values, validate_all=validate_all)


def validate_class_partial(cls, values, validate_all=False):
    """This is a convenience function that loops over _fields in
    cls to validate them. This function is a partial validatation
    only, meaning the values given and does not check if the model
    is complete.
    """
    fun = lambda k, v: k in values
    return _validate_helper(cls, fun, values, validate_all=validate_all)

