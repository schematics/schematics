try:
    from itertools import filterfalse  # python3 wutwut
except:
    from itertools import ifilterfalse
from operator import itemgetter

from dictshield.document import EmbeddedDocument
from dictshield.base import  ShieldException, InvalidShield
from dictshield.fields import BaseField, DictField
from dictshield.datastructures import MultiValueDict


RECURSIVE_REFERENCE_CONSTANT = 'self'


class ListField(BaseField):
    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the model.
    """

    def __init__(self, fields, **kwargs):
        # Some helpful functions
        is_basefield = lambda field: isinstance(field, BaseField)
        is_embeddeddoc = lambda field: isinstance(field, EmbeddedDocumentField)
        is_dictfield = lambda field: isinstance(field, DictField)

        # field instance
        #if isinstance(fields, BaseField):
        if is_basefield(fields):
            #if isinstance(fields, EmbeddedDocumentField):
            if is_embeddeddoc(fields):
                kwargs.setdefault('primary_embedded', fields)
            fields = [fields]
        # something other than a list
        elif not isinstance(fields, list):
            raise InvalidShield('Argument to ListField constructor must be '
                                'a valid field or list of fields')
        # some bad stuff in the list
        elif list(ifilterfalse(is_basefield, fields)):
            raise InvalidShield('Argument to ListField constructor must be '
                                'a valid field or list of valid fields')
        else:
            docs = filter(is_embeddeddoc, fields)
            dicts = filter(is_dictfield, fields)
            if dicts:
                kwargs.setdefault('primary_embedded', None)
            if docs:
                kwargs.setdefault('primary_embedded', docs[0])
        self.fields = fields
        kwargs.setdefault('default', list)

        self.primary_embedded = kwargs.pop('primary_embedded', None)
        super(ListField, self).__init__(**kwargs)

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document.
        """
        is_embeddeddoc = lambda field: isinstance(field, EmbeddedDocumentField)
        embedded_fields = filter(is_embeddeddoc, self.fields)
        if self.primary_embedded:
            embedded_fields.remove(self.primary_embedded)
            embedded_fields.insert(0, self.primary_embedded)

        if value is None:
            value = []  # have to use a list

        if embedded_fields:
            list_of_docs = list()
            for doc in value:
                if isinstance(doc, dict):
                    for embedded_field in embedded_fields:
                        doc_obj = embedded_field.document_type_obj(**doc)
                        try:
                            doc_obj.validate()
                        except ShieldException:
                            continue
                        doc = doc_obj
                        break
                list_of_docs.append(doc)
            value = list_of_docs
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
        """for_json must be careful to expand embedded documents into Python,
        not JSON.
        """
        return list(self.for_output_format('for_json', value))

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (list, tuple)):
            error_msg = 'Only lists and tuples may be used in a list field'
            raise ShieldException(error_msg, self.field_name, value)

        if not self.fields:  # if we want everything to validate
            return

        for item in value:
            try:
                for field in self.fields:
                    field.validate(item)
            except Exception, e:
                raise ShieldException('Invalid ListField item',
                                      self.field_name, str(item))
        return value

    def _set_owner_document(self, owner_document):
        for field in self.fields:
            field.owner_document = owner_document
        self._owner_document = owner_document

    def _get_owner_document(self, owner_document):
        self._owner_document = owner_document

    owner_document = property(_get_owner_document, _set_owner_document)


class SortedListField(ListField):
    """A ListField that sorts the contents of its list before writing to
    the database in order to ensure that a sorted list is always
    retrieved.
    """

    _ordering = None

    def __init__(self, field, **kwargs):
        if 'ordering' in kwargs.keys():
            self._ordering = kwargs.pop('ordering')
        super(SortedListField, self).__init__(field, **kwargs)

    def for_thing(self, value, meth):
        unsorted = getattr(super(SortedListField, self), meth)(value)
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
### Sub structures
###

class EmbeddedDocumentField(BaseField):
    """An embedded document field. Only valid values are subclasses of
    :class:`~dictshield.EmbeddedDocument`.
    """
    def __init__(self, document_type, **kwargs):
        is_embeddable = lambda dt: issubclass(dt, EmbeddedDocument)
        if not isinstance(document_type, basestring):
            if not document_type or not is_embeddable(document_type):
                raise ShieldException('Invalid embedded document class '
                                      'provided to an EmbeddedDocumentField',
                                      self.field_name, document_type)
        self.document_type_obj = document_type
        super(EmbeddedDocumentField, self).__init__(**kwargs)

    def __set__(self, instance, value):
        if value is None:
            return
        if not isinstance(value, self.document_type):
            value = self.document_type(**value)
        instance._data[self.field_name] = value

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, basestring):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def _jsonschema_type(self):
        return 'object'

    @classmethod
    def _from_jsonschema_types(self):
        return ['object']

    @classmethod
    def _from_jsonschema_formats(self):
        return [None]

    def for_jsonschema(self):
        return self.document_type.for_jsonschema()

    def for_python(self, value):
        return value.to_python()

    def for_json(self, value):
        return value.to_json(encode=False)

    def validate(self, value):
        """Make sure that the document instance is an instance of the
        EmbeddedDocument subclass provided when the document was defined.
        """
        # Using isinstance also works for subclasses of self.document
        if not isinstance(value, self.document_type):
            raise ShieldException('Invalid embedded document instance '
                                  'provided to an EmbeddedDocumentField',
                                  self.field_name, value)
        self.document_type.validate(value)
        return value

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)


class MultiValueDictField(DictField):
    def __init__(self, basecls=None, *args, **kwargs):
        self.basecls = basecls or BaseField
        if not issubclass(self.basecls, BaseField):
            raise InvalidShield('basecls is not subclass of BaseField')
        kwargs.setdefault('default', lambda: MultiValueDict())
        super(MultiValueDictField, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, MultiValueDict):
            value = MultiValueDict(value)

        super(MultiValueDictField, self).__set__(instance, value)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (dict, MultiValueDict)):
            raise ShieldException('Only dictionaries or MultiValueDict may be '
                                  'used in a DictField', self.field_name,
                                  value)

        if any(('.' in k or '$' in k) for k in value):
            raise ShieldException('Invalid dictionary key name - keys may not '
                                  'contain "." or "$" characters',
                                  self.field_name, value)
        return value

    def for_json(self, value):
        output = {}
        for key, values in value.iterlists():
            output[key] = values

        return output
