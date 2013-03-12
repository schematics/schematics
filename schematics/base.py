import functools


### UltraJSON is really, really fast. It's so fast that we favor it over other
### implementations, in spite of it not having a useful function for testing,
### key sorting.
###
### The code below monkey patches ujson to ignore the `sort_keys` keyword that
### other implementations support.
###
### It is believed that the only place where sorting the keys is desirable over
### serialization speed is in testing frameworks, thus the fast solution of
### monkey patching with an explaination.

json_is_ujson = True
try:
    import ujson as json
except ImportError:
    import json
    json_is_ujson = False


json_dumps = json.dumps
@functools.wraps(json.dumps)
def _dumps(*args, **kwargs):
    """Wrapper for ujson.dumps which removes the 'sort_keys' kwarg. Regular
    json.dumps supports sort_keys but ujson.dumps does not.
    """
    kwargs.pop('sort_keys', None)
    return json_dumps(*args, **kwargs)


if json_is_ujson:
    json.dumps = _dumps

### End of UltraJSON patching
