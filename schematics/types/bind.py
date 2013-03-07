

def _bind(field, model, memo):
    """Helper for the field binding.  This is inspired by the way `deepcopy`
    is implemented.
    """
    if memo is None:
        memo = {}

    field_id = id(field)
    if field_id in memo:
        return memo[field_id]

    rv = field._bind(model, memo)
    memo[field_id] = rv
    return rv
