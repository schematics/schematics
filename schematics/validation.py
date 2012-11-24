from schematics.base import TypeException, ModelException


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
        raise ValueError('cls is not a Model instance')

    # Create function for handling exceptions
    exceptions = list()
    handle_exception = _gen_handle_exception(validate_all, exceptions)

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
            try:
                v.validate(datum)
            except TypeException, e:
                handle_exception(e)

    # Remove rogue fields
    if len(class_fields) > 0:  # if accumulation is not disabled
        palins = data_fields - set(class_fields)
        for rogue_field in palins:
            del values[rogue_field]

    # Reaches here only if exceptions are aggregated or validation passed
    if validate_all:
        return exceptions
    else:
        return True


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
            try:
                field._validate(value)
            except TypeException, e:
                err = e
            except (ValueError, AttributeError, AssertionError):
                err = TypeException('Invalid value', field.field_name,
                                    value)
        elif field.required:
            err = TypeException('Required field missing',
                                field.field_name,
                                value)
        # If validate_all, save errors to a list
        # Otherwise, throw the first error
        if err:
            errs.append(err)
        if err and not validate_all:
            # NB: raising a ModelException in this case would be more
            # consistent, but existing code might expect TypeException
            raise err

    if errs:
        raise ModelException(model._model_name, errs)
    return True


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
