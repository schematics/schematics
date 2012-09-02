#!/usr/bin/env python


### ultra json is really fast
try:
    import ujson as json
except:
    import json


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
