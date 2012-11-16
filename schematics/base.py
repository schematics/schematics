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


# Only patch if we are using ujson
if json_is_ujson:
    json.dumps = _dumps

### End of UltraJSON patching


###
### Exceptions
###

#class InvalidShield(Exception):
class NotAModelException(Exception):    
    """A model has been put together incorrectly
    """
    pass


class NotATypeException(Exception):    
    """A schematics type was not used.
    """
    pass


#class ShieldException(Exception):
class TypeException(Exception):    
    """The field did not pass validation.
    """
    def __init__(self, reason, field_name, field_value, *args, **kwargs):
        super(TypeException, self).__init__(*args, **kwargs)
        self.reason = reason
        self.field_name = field_name
        self.field_value = field_value

    def __str__(self):
        return '%s - %s:%s' % (self.reason, self.field_name, self.field_value)


#class ShieldDocException(Exception):
class ModelException(Exception):
    """The Model did not pass validation and the errors have been
    accumulated into two variables: `doc` and `error_list`.
    
    `doc` is the name of the model that did not validate.
    `error_list` is the list of TypeExceptions that were found
    """
    def __init__(self, doc_name, error_list, *args, **kwargs):
        super(ModelException, self).__init__(*args, **kwargs)
        self.doc = doc_name
        self.error_list = error_list

    def __str__(self):
        return 'Model had %d errors - %s' % (len(self.error_list),
                [e.__str__() for e in self.error_list],)


def subclass_exception(name, parents, module):
    return type(name, parents, {'__module__': module})
