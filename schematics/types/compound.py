try:
    from itertools import filterfalse  # python3 wutwut
except:
    from itertools import ifilterfalse
from operator import itemgetter

from schematics.models import Model
from schematics.types import BaseType, DictType
from schematics.datastructures import MultiValueDict
from schematics.serialize import to_python, to_json, for_jsonschema
from schematics.validation import (validate_instance, validate_values, OK,
                                   ERROR_FIELD_TYPE_CHECK, ERROR_FIELD_CONFIG,
                                   ModelResult, FieldResult)


RECURSIVE_REFERENCE_CONSTANT = 'self'


class ListType(BaseType):
    """A list type that wraps a standard type, allowing multiple instances
    of the type to be used as a list in the model.
    """

    def __init__(self, fields, **kwargs):
        ### Short hand
        is_basetype = lambda field: isinstance(field, BaseType)
        is_model = lambda field: isinstance(field, ModelType)
        is_dicttype = lambda field: isinstance(field, DictType)

        ### fields is a schematic Type
        if is_basetype(fields):
            if is_model(fields):
                kwargs.setdefault('primary_embedded', fields)
            fields = [fields]
        # something other than a list
        elif not isinstance(fields, list):
            error_msg = 'Argument to ListType constructor must be '
            error_msg = error_msg + 'a valid field or list of fields'
            
            return FieldResult(ERROR_FIELD_CONFIG, error_msg,
                               self.field_name, fields)
        # some bad stuff in the list
        elif list(ifilterfalse(is_basetype, fields)):
            error_msg = 'Argument to ListType constructor must be '
            error_msg = error_msg + 'a valid field or list of valid fields'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, fields)
        else:
            models = filter(is_model, fields)
            dicts = filter(is_dicttype, fields)
            if dicts:
                kwargs.setdefault('primary_embedded', None)
            if models:
                kwargs.setdefault('primary_embedded', models[0])

        self.fields = fields
        kwargs.setdefault('default', list)

        self.primary_embedded = kwargs.pop('primary_embedded', None)
        super(ListType, self).__init__(**kwargs)

    def __set__(self, instance, value_list):
        """Descriptor for assigning a value to a type in a model.
        """
        new_value = value_list

        is_model = lambda tipe: isinstance(tipe, ModelType)
        model_fields = filter(is_model, self.fields)
        
        if self.primary_embedded:
            model_fields.remove(self.primary_embedded)
            model_fields.insert(0, self.primary_embedded)

        if value_list is None:
            value_list = []  # have to use a list

        errors_found = False
        if model_fields:
            new_data = list()
            for datum in value_list:
                datum_instance = datum
                is_dict = False

                ### if `datum` is dict, attempt conversion
                if isinstance(datum, dict):
                    is_dict = True
                    ### Find a model that matches
                    for model_field in model_fields:
                        ### TODO Validate SMARTER
                        datum_instance = model_field.model_type_obj(**datum)

                #import pdb; pdb.set_trace()
                result = validate_instance(datum_instance)
            
                if result.tag == OK:
                    ### Remove double instantiation
                    for model_field in model_fields:
                        ### TODO Validate SMARTER
                        datum_instance = model_field.model_type_obj(**result.value)
                    #new_data.append(datum_instance)
                    new_data.append(datum_instance)
                else:
                    errors_found = True
                    
            new_value = new_data

        if not errors_found:
            instance._data[self.field_name] = new_value

    def _jsonschema_type(self):
        return 'array'

    @classmethod
    def _from_jsonschema_types(self):
        return ['array']


    @classmethod
    def _from_jsonschema_formats(self):
        return [None]

    def _jsonschema_items(self):
        return [for_jsonschema(field) for field in self.fields]

    def for_output_format(self, output_format_method_name, value):
        for item in value:
            for field in self.fields:
                try:
                    value = getattr(field, output_format_method_name)(item)
                    yield value
                except ValueError:
                    continue

    def for_python(self, value):
        return list(self.for_output_format('for_python', value))

    def for_json(self, value):
        """for_json must be careful to expand modeltypes into Python,
        not JSON.
        """
        return list(self.for_output_format('for_json', value))

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (list, tuple)):
            error_msg = 'Only lists and tuples may be used in a list field'
            raise FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                              self.field_name, value)

        if not self.fields:  # empty list
            return FieldResult(OK, 'success', self.field_name, value)

        errors = []
        good_data = []
        for item in value:
            for field in self.fields:
                result = field.validate(item)
                if result.tag == OK:
                    good_data.append(result.value)
                else:
                    errors.append(result)

        if len(errors) > 0:
            error_msg = 'Invalid ListType item'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, errors)
        
        return FieldResult(OK, 'success', self.field_name, good_data)

    def _set_owner_model(self, owner_model):
        for field in self.fields:
            field.owner_model = owner_model
        self._owner_model = owner_model

    def _get_owner_model(self, owner_model):
        self._owner_model = owner_model

    owner_model = property(_get_owner_model, _set_owner_model)


class SortedListType(ListType):
    """A ListType that sorts the contents of its list before writing to
    the database in order to ensure that a sorted list is always
    retrieved.
    """

    _ordering = None

    def __init__(self, field, **kwargs):
        if 'ordering' in kwargs.keys():
            self._ordering = kwargs.pop('ordering')
        super(SortedListType, self).__init__(field, **kwargs)

    def for_thing(self, value, meth):
        unsorted = getattr(super(SortedListType, self), meth)(value)
        if self._ordering is not None:
            return sorted(unsorted, key=itemgetter(self._ordering))
        return sorted(unsorted)

    def for_python(self, value):
        return self.for_thing(value, 'for_python')

    def for_json(self, value):
        return self.for_thing(value, 'for_json')

    @classmethod
    def _from_jsonschema_types(self):
        return []

    @classmethod
    def _from_jsonschema_formats(self):
        return []


###
### Sub schematics
###

class ModelType(BaseType):
    """A model field. Only valid values are subclasses of `schematics.Model`.
    """
    def __init__(self, model_type, **kwargs):
        is_embeddable = lambda dt: issubclass(dt, Model)
        if not isinstance(model_type, basestring):
            if not model_type or not is_embeddable(model_type):
                error_msg = 'Invalid model class provided to an ModelType'
                return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                   self.field_name, model_type)
        self.model_type_obj = model_type
        super(ModelType, self).__init__(**kwargs)

    def __set__(self, instance, value):
        if value is None:
            return
        if not isinstance(value, self.model_type):
            value = self.model_type(**value)
        instance._data[self.field_name] = value

    @property
    def model_type(self):
        if isinstance(self.model_type_obj, basestring):
            if self.model_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.model_type_obj = self.owner_model
            else:
                self.model_type_obj = get_model(self.model_type_obj)
        return self.model_type_obj

    def _jsonschema_type(self):
        return 'object'

    @classmethod
    def _from_jsonschema_types(self):
        return ['object']

    @classmethod
    def _from_jsonschema_formats(self):
        return [None]

    def for_jsonschema(self):
        return for_jsonschema(self.model_type)

    def for_python(self, value):
        return to_python(value)

    def for_json(self, value):
        return to_json(value, encode=False)

    def validate(self, value):
        """Make sure that the model instance is an instance of the
        Model subclass provided when the model was defined.
        """
        # Using isinstance also works for subclasses of self.model
        if not isinstance(value, self.model_type):
            error_msg = 'Invalid modeltype instance provided to an ModelType'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)

        return validate_instance(value)

    def lookup_member(self, member_name):
        return self.model_type._fields.get(member_name)


class MultiValueDictType(DictType):
    def __init__(self, basecls=None, *args, **kwargs):
        self.basecls = basecls or BaseType
        
        if not issubclass(self.basecls, BaseType):
            error_msg = 'basecls is not subclass of BaseType'
            return FieldResult(ERROR_FIELD_CONFIG, error_msg,
                               self.field_name, fields)
        
        kwargs.setdefault('default', lambda: MultiValueDict())
        super(MultiValueDictType, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, MultiValueDict):
            value = MultiValueDict(value)

        super(MultiValueDictType, self).__set__(instance, value)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (dict, MultiValueDict)):
            error_msg = 'Only dictionaries or MultiValueDict may be used in a '
            error_msg = error_msg + 'DictType'
            return  FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                                self.field_name, value)

        ### TODO get rid of this
        if any(('.' in k or '$' in k) for k in value):
            error_msg = 'Invalid dictionary key name - keys may not contain '
            error_msg = error_msg + '"." or "$" characters'
            return FieldResult(ERROR_FIELD_TYPE_CHECK, error_msg,
                               self.field_name, value)
        
        return FieldResult(OK, 'success', self.field_name, value)

    def for_json(self, value):
        output = {}
        for key, values in value.iterlists():
            output[key] = values

        return output
