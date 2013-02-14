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

from collections import namedtuple


###
### Result Handlilng
###

OK = 'OK'

### Type Handling
TypeResult = namedtuple('TypeResult', 'tag message value')
#ERROR_INVALID_TYPE
ERROR_TYPE_COERCION = 'ERROR_TYPE_COERCION'  # type coercion failed

### Field Handling
FieldResult = namedtuple('FieldResult', 'tag message name value')
ERROR_FIELD_TYPE_CHECK = 'ERROR_FIELD_TYPE_CHECK'  # field failed type check
ERROR_FIELD_CONFIG = 'ERROR_FIELD_CONFIG'  # bad type instance config
ERROR_FIELD_REQUIRED = 'ERROR_FIELD_REQUIRED'  # required field not found 
ERROR_FIELD_BAD_CHOICE = 'ERROR_FIELD_BAD_CHOICE'  # bad type instance config

### Model Handling
ModelResult = namedtuple('ModelResult', 'tag message model value')
ERROR_MODEL_INVALID = 'ERROR_MODEL_INVALID'  # data is not a schematics model
ERROR_MODEL_TYPE_CHECK = 'ERROR_MODEL_TYPE_CHECK'  # model failed type check
ERROR_MODEL_ROGUE_FIELD = 'ERROR_MODEL_ROGUE_FIELD'  # field not found in model


###
### Validation Functions
###

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
    """Loops across the fields in a Model definition, `cls`, and attempts
    validation on any fields that require a check, as signalled by the
    `needs_check` function.

    The basis for validation is `cls`, so fields are located in `cls` and
    mapped to an entry in `values`.  This entry is then validated against the
    field's validation function.

    If errors are found they are accumulated in `errors` and return with a tag
    signalling an error.

    If validation passes, the values are returned with all the values coerced
    to their appropriate type, as specificed in the field's `validate`
    function.
    """
    ### Reject model if _fields isn't present
    if not hasattr(cls, '_fields'):
        error_msg = 'cls is not a Model instance'
        return ModelResult(ERROR_MODEL_INVALID, error_msg, cls, values)

    ### Containers for results
    new_data = {}
    errors = []

    ### Validate data based on cls's structure
    for field_name, field in cls._fields.items():
        ### Rely on parameter for whether or not we should check value 
        if needs_check(field_name, field):
            field_value = values[field_name]

            ### Don't validate nones or empty values  # TODO makea parameter
            if _is_empty(field_value):
               if field.required:
                  errors.append(FieldResult(ERROR_FIELD_REQUIRED, "required field was empty",
                                field_name, field_value))
            continue

            ### Validate field value via call to BaseType._validate
            result = field._validate(field_value)
            if result.tag != OK:
                errors.append(result)
            else:
                new_data[field_name] = result.value

    ### Report rogue fields as errors if `report_rogues`
    if report_rogues:
        class_fields = cls._fields.keys()
        rogues_found = set(values.keys()) - set(class_fields)
        if len(rogues_found) > 0:
            for field_name in rogues_found:
                error_msg = 'Unknown field found'
                field_value = values[field_name]
                result = FieldResult(ERROR_MODEL_ROGUE_FIELD, error_msg,
                                    field_name, field_value)
                errors.append(result)
                    
    ### Return on if errors were found
    if len(errors) > 0:
        error_msg = 'Model validation errors'
        return ModelResult(ERROR_MODEL_TYPE_CHECK, error_msg, cls, errors)

    return ModelResult(OK, 'success', cls, new_data)


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
    if '_data' in model:
        values = model._data
        needs_check = lambda k, v: v.required or k in values
        return _validate(model, needs_check, values)
    return ModelResult(OK, 'No Model to Validate Against', None, None)
    

def validate_partial(cls, values):
    """This function will validate values against fields of the same name in
    the model.  No checks for required fields are performed.

    The idea here is you might validate subcomponents of a document and then
    merge them later.
    """
    needs_check = lambda k, v: k in values
    return _validate(cls, needs_check, values)
