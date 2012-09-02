try:
    from itertools import filterfalse  # python3 wutwut
except:
    from itertools import ifilterfalse
from operator import itemgetter

from schematics.models import Model
from schematics.base import  TypeException
from schematics.types import BaseType, DictType
from schematics.datastructures import MultiValueDict


RECURSIVE_REFERENCE_CONSTANT = 'self'


class ListType(BaseType):
    """A list type that wraps a standard type, allowing multiple instances
    of the type to be used as a list in the model.
    """

    def __init__(self, fields, **kwargs):
        # Some helpful functions
        is_basetype = lambda tipe: isinstance(tipe, BaseType)
        is_model = lambda tipe: isinstance(tipe, ModelType)
        is_dicttype = lambda tipe: isinstance(tipe, DictType)

        # field instance
        if is_basetype(fields):
            if is_model(fields):
                kwargs.setdefault('primary_embedded', fields)
            fields = [fields]
        # something other than a list
        elif not isinstance(fields, list):
            raise TypeException('Argument to ListType constructor must be '
                                'a valid field or list of fields',
                                self.field_name, list)
        # some bad stuff in the list
        elif list(ifilterfalse(is_basetype, fields)):
            raise TypeException('Argument to ListType constructor must be '
                                'a valid field or list of valid fields',
                                self.field_name, list)
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

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a type in a model.
        """
        is_model = lambda tipe: isinstance(tipe, ModelType)
        model_fields = filter(is_model, self.fields)
        if self.primary_embedded:
            model_fields.remove(self.primary_embedded)
            model_fields.insert(0, self.primary_embedded)

        if value is None:
            value = []  # have to use a list

        if model_fields:
            list_of_models = list()
            for model in value:
                if isinstance(model, dict):
                    for model_field in model_fields:
                        model_obj = model_field.model_type_obj(**model)
                        model_obj.validate()
                        model = model_obj
                list_of_models.append(model)
            value = list_of_models
        instance._data[self.field_name] = value

    def _jsonschema_type(self):
        return 'array'

    @classmethod
    def _from_jsonschema_types(self):
        return ['array']

    @classmethod
    def _from_jsonschema_formats(self):
        return [None]

    def _jsonschema_items(self):
        return [field.for_jsonschema() for field in self.fields]

    def for_output_format(self, output_format_method_name, value):
        for item in value:
            for field in self.fields:
                try:
                    yield getattr(field, output_format_method_name)(item)
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
            raise TypeException(error_msg, self.field_name, value)

        if not self.fields:  # if we want everything to validate
            return

        for item in value:
            try:
                for field in self.fields:
                    field.validate(item)
            except Exception, e:
                raise TypeException('Invalid ListType item',
                                      self.field_name, str(item))
        return value

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
                raise TypeException('Invalid model class provided to an '
                                    'ModelType',
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
        return self.model_type.for_jsonschema()

    def for_python(self, value):
        return value.to_python()

    def for_json(self, value):
        return value.to_json(encode=False)

    def validate(self, value):
        """Make sure that the model instance is an instance of the
        Model subclass provided when the model was defined.
        """
        # Using isinstance also works for subclasses of self.model
        if not isinstance(value, self.model_type):
            raise TypeException('Invalid modeltype instance '
                                  'provided to an ModelType',
                                  self.field_name, value)
        self.model_type.validate(value)
        return value

    def lookup_member(self, member_name):
        return self.model_type._fields.get(member_name)


class MultiValueDictType(DictType):
    def __init__(self, basecls=None, *args, **kwargs):
        self.basecls = basecls or BaseType
        if not issubclass(self.basecls, BaseType):
            raise NotAModelException('basecls is not subclass of BaseType')
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
            raise TypeException('Only dictionaries or MultiValueDict may be '
                                  'used in a DictType', self.field_name,
                                  value)

        if any(('.' in k or '$' in k) for k in value):
            raise TypeException('Invalid dictionary key name - keys may not '
                                  'contain "." or "$" characters',
                                  self.field_name, value)
        return value

    def for_json(self, value):
        output = {}
        for key, values in value.iterlists():
            output[key] = values

        return output
