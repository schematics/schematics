

def _bind(obj, form, memo):
    """Helper for the field binding.  This is inspired by the way `deepcopy`
    is implemented.
    """
    if memo is None:
        memo = {}
    obj_id = id(obj)
    if obj_id in memo:
        return memo[obj_id]
    rv = obj._bind(form, memo)
    memo[obj_id] = rv
    return rv
