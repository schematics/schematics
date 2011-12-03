from base import (BaseDocument,
                  ShieldException,
                  DocumentMetaclass,
                  TopLevelDocumentMetaclass,
                  QueryableTopLevelDocumentMetaclass)

from base import json

__all__ = ['Document', 'EmbeddedDocument', 'ShieldException']


###
### Model Manipulation Functions
###

def _swap_field(klass, new_field, fields):
    """This function takes an existing class definition `klass` and create a
    new version of the structure with the fields in `fields` converted to
    `field` instances.

    Effectively doing this:

        class.field_name = id_field()  # like ObjectIdField, perhaps

    Returns the class for compatibility, making it compatible with a decorator.
    """
    ### The metaclass attributes will fake not having inheritance
    cn = klass._class_name
    sc = klass._superclasses
    klass_name = klass.__name__

    ### Generate the id_fields for each field we're updating. Mark the actual
    ### id_field as the uniq_field named '_id'
    fields_dict = dict()
    for f in fields:
        if f is klass._meta['id_field']:
            fields_dict[f] = new_field(uniq_field='_id')
        else:
            fields_dict[f] = new_field()
        
    ### Generate new class
    new_klass = type(klass_name, (klass,), fields_dict)

    ### Meta attributes act like it never happened. :)
    new_klass._class_name = cn
    new_klass._superclasses = sc
    
    return new_klass


def diff_id_field(id_field, field_list, *arg):
    """This function is a decorator that takes an id field, like ObjectIdField,
    and replaces the fields in `field_list` to use `id_field` instead.

    Wrap a class definition and it will apply the field swap in an simply and
    expressive way.

    The function can be used as a decorator OR the adjusted class can be passed
    as an optional third argument.
    """
    if len(arg) == 1:
        return _swap_field(arg[0], id_field, field_list)
    
    def wrap(klass):
        klass = _swap_field(klass, id_field, field_list)
        return klass
    return wrap


###
### Documents Models
###

class SafeableMixin:
    """A `SafeableMixin` is used to add unix style permissions to fields in a
    `Document`. It creates this by using a black list and a white list in the
    form of three lists called `_internal_fields`, `_private_fields` and
    `_public_fields`.

    `_internal_fields` is used to list fields which are private and not meant
    to leave the system. This generally consists of `_id`, `_cls` and `_types`
    but a user can extend the list of internal fields by defining a class level
    list field called _private_fields. Any field listed here will be removed
    with any call to a make*safe method.

    `make_json_ownersafe` is defined to remove the keys listed in both
    fields, making it our blacklist.

    If `_public_fields` is defined, `make_json_publicsafe` can be used to create
    a structure made of only the fields in this list, making it our white list.
    """
    _internal_fields = [
        '_id', 'id', '_cls', '_types',
    ]

    _public_fields = None

    @classmethod
    def _get_internal_fields(cls):
        """Helper function that determines the union of :attr:`_internal_fields`
        and :attr:`_private_fields`, else returns just :attr:`_internal_fields`.
        """
        internal_fields = set(cls._internal_fields)
        if hasattr(cls, '_private_fields'):
            private_fields = set(cls._private_fields)
            internal_fields = internal_fields.union(private_fields)
        return internal_fields


    ###
    ### Make Safe Functions
    ###
        
    @classmethod
    def make_safe(cls, doc_dict_or_dicts, field_converter, doc_converter,
                  doc_encoder, field_list=None, white_list=True):
        """This function is the building block of the safe mechanism. This
        class method takes a doc, dict or dicts and converts them into the
        equivalent structure with three basic rules applied.

          1. The fields must be converted from the model into a type. This is
             currently scene as calling `for_python()` or `for_json()` on fields.

          2. A function that knows how to handle `EmbeddedDocument` instances,
             using the same security parameters as the caller; this function.

          3. The field list that acts as either a white list or a black list. A
             white list preserves only the keys explicitly listed. A black list
             preserves any keys not explicitly listed.
          
        """
        ### Field list defaults to `_internal_fields` + `_public_fields`
        if field_list is None:
            field_list = cls._get_internal_fields()

        ### Setup white or black list detection
        gottago = lambda k: k not in field_list
        if not white_list:
            gottago = lambda k: k in field_list

        if isinstance(doc_dict_or_dicts, BaseDocument):
            doc_dict = dict((f, doc_dict_or_dicts[f]) for f in doc_dict_or_dicts)
        else:
            doc_dict = doc_dict_or_dicts

        ### Transform each field (Docs implement dictionary-style field access)
        for k,v in doc_dict.items():
            if gottago(k):
                del doc_dict[k]
            elif isinstance(v, EmbeddedDocument):
                doc_dict[k] = doc_converter(v)
            elif isinstance(v, list) and len(v) > 0:
                if isinstance(v[0], EmbeddedDocument):
                    doc_dict[k] = [doc_converter(vi) for vi in v]
            else:
                doc_dict[k] = field_converter(k, v)
                    
        return doc_dict


    @classmethod
    def make_ownersafe(cls, doc_dict_or_dicts):
        field_converter = lambda f, v: v
        doc_encoder = lambda d: d.to_python()
        doc_converter = lambda d: d.make_ownersafe(d)
        field_list = cls._get_internal_fields()
        white_list = False

        return cls.make_safe(doc_dict_or_dicts, field_converter, doc_converter,
                             doc_encoder, field_list=field_list,
                             white_list=white_list)

    @classmethod
    def make_json_ownersafe(cls, doc_dict_or_dicts, encode=True):
        field_converter = lambda f, v: cls._fields[f].for_json(v)
        doc_encoder = lambda d: d.to_json(encode=False)
        doc_converter = lambda d: d.make_json_ownersafe(d, encode=False)
        field_list = cls._get_internal_fields()
        white_list = False

        safed = cls.make_safe(doc_dict_or_dicts, field_converter, doc_converter,
                              doc_encoder, field_list=field_list,
                              white_list=white_list)
        if encode:
            return json.dumps(safed)
        else:
            return safed
    
    @classmethod
    def make_publicsafe(cls, doc_dict_or_dicts):
        field_converter = lambda f, v: v
        doc_encoder = lambda d: d.to_python()
        doc_converter = lambda d: d.make_publicsafe(d)
        field_list = cls._public_fields
        white_list = True

        return cls.make_safe(doc_dict_or_dicts, field_converter, doc_converter,
                             doc_encoder,  field_list=cls._public_fields,
                             white_list=white_list)

    @classmethod
    def make_json_publicsafe(cls, doc_dict_or_dicts, encode=True):
        field_converter = lambda f, v: cls._fields[f].for_json(v)
        doc_encoder = lambda d: d.to_json(encode=False)
        doc_converter = lambda d: d.make_json_publicsafe(d, encode=False)
        field_list = cls._public_fields
        white_list = True

        safed = cls.make_safe(doc_dict_or_dicts, field_converter, doc_converter,
                              doc_encoder, field_list=field_list,
                              white_list=white_list)
        if encode:
            return json.dumps(safed)
        else:
            return safed


    ###
    ### Validation
    ###

    @classmethod
    def _gen_handle_exception(cls, validate_all, exception_list):
        """Generates a function for either raising exceptions or collecting them
        in a list.
        """
        if validate_all:
            def handle_exception(e):
                exception_list.append(e)
        else:
            def handle_exception(e):
                raise e

        return handle_exception

    @classmethod
    def _gen_handle_class_field(cls, delete_rogues, field_list):
        """Generates a function that either accumulates observed fields or
        makes no attempt to collect them.

        The case where nothing accumulates is to prevent growing data structures
        unnecessarily.
        """
        if delete_rogues:
            def handle_class_field(cf):
                field_list.append(cf)
        else:
            def handle_class_field(cf):
                pass

        return handle_class_field

    @classmethod
    def _validate_helper(cls, field_inspector, values, validate_all=False,
                         delete_rogues=True):
        """This is a convenience function that loops over the given values
        and attempts to validate them against the class definition. It only
        validates the data in values and does not guarantee a complete document
        is present.

        'not present' is defined as not having a value OR having '' (or u'')
        as a value.
        """
        if not hasattr(cls, '_fields'):
            raise ValueError('cls is not a Document instance')

        internal_fields = cls._get_internal_fields()

        # Create function for handling exceptions
        exceptions = list()
        handle_exception = cls._gen_handle_exception(validate_all, exceptions)

        # Create function for handling a flock of frakkin palins (rogue fields)
        data_fields = set(values.keys())
        class_fields = list()
        handle_class_field = cls._gen_handle_class_field(delete_rogues,
                                                         class_fields)

        # Loop across fields present in model
        for k,v in cls._fields.items():

            # handle common id name
            if k is 'id': k = '_id'

            handle_class_field(k)

            # we don't accept internal fields from users
            if k in internal_fields and k in values:
                value_is_default = (values[k] is v.default)
                if not value_is_default:
                    e = ShieldException('Overwrite of internal fields attempted', k, v)
                    handle_exception(e)
                    continue

            if field_inspector(k, v):
                datum = values[k]
                # if datum is None, skip
                if datum is None:
                    continue
                # treat empty strings as empty values and skip
                if isinstance(datum, (str, unicode)) and len(datum.strip()) == 0:
                    continue
                try:
                    v.validate(datum)
                except ShieldException, e:
                    handle_exception(e)

        # Remove rogue fields
        if len(class_fields) > 0: # if accumulation is not disabled
            palins = data_fields - set(class_fields)
            for rogue_field in palins:
                del values[rogue_field]

        # Reaches here only if exceptions are aggregated or validation passed
        if validate_all:
            return exceptions
        else:
            return True

    @classmethod
    def validate_class_fields(cls, values, validate_all=False):
        """This is a convenience function that loops over _fields in
        cls to validate them. If the field is not required AND not present,
        it is skipped.
        """
        fun = lambda k,v: v.required or k in values
        return cls._validate_helper(fun, values, validate_all=validate_all)

    @classmethod
    def validate_class_partial(cls, values, validate_all=False):
        """This is a convenience function that loops over _fields in
        cls to validate them. This function is a partial validatation
        only, meaning the values given and does not check if the document
        is complete.
        """
        fun = lambda k,v: k in values
        return cls._validate_helper(fun, values, validate_all=validate_all)


class EmbeddedDocument(BaseDocument, SafeableMixin):
    """A :class:`~dictshield.Document` that isn't stored in its own
    collection.  :class:`~dictshield.EmbeddedDocument`\ s should be used as
    fields on :class:`~dictshield.Document`\ s through the
    :class:`~dictshield.EmbeddedDocumentField` field type.
    """

    __metaclass__ = DocumentMetaclass


class Document(BaseDocument, SafeableMixin):
    """The base class used for defining the structure and properties of
    collections of documents modeled in DictShield. Inherit from this class,
    and add fields as class attributes to define a document's structure.
    Individual documents may then be created by making instances of the
    :class:`~dictshield.Document` subclass.

    A :class:`~dictshield.Document` subclass may be itself subclassed, to
    create a specialised version of the document that can be stored in the
    same collection. To facilitate this behaviour, `_cls` and `_types`
    fields are added to documents to specify the install class and the types
    in the Document class hierarchy. To disable this behaviour and remove
    the dependence on the presence of `_cls` and `_types`, set
    :attr:`allow_inheritance` to ``False`` in the :attr:`meta` dictionary.
    """

    __metaclass__ = TopLevelDocumentMetaclass


class QueryableDocument(BaseDocument, SafeableMixin):

    __metaclass__ = QueryableTopLevelDocumentMetaclass
