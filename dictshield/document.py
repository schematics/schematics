from base import (BaseDocument, DictPunch, DocumentMetaclass, TopLevelDocumentMetaclass)

from base import json

__all__ = ['Document', 'EmbeddedDocument', 'DictPunch']


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

    @classmethod
    def _safe_data_from_input(cls, fun, data):
        """Helper function for handling variable inputs to make_json_*safe
        functions.

        Returns a safe doc if given one element.

        Returns an list if given a list. Can handle a list of dicts or
        list of docs.
        """
        # single cls instance
        if isinstance(data, cls):
            return fun(data.to_python())

        # single dict instance
        elif isinstance(data, dict):
            return fun(data)

        # list of cls instances or list of dicts
        elif isinstance(data, list):
            if len(data) < 1:
                return list()
            elif isinstance(data[0], dict):
                pass # written for clarity
            elif isinstance(data[0], cls):
                data = [d.to_python() for d in data]
            return map(fun, data)

    @classmethod
    def make_ownersafe(cls, doc_dict_or_dicts):
        """This function removes internal fields and handles any steps
        required for making the data stucture (list, dict or Document)
        safe for transmission to the owner of the data.

        It also knows to check for EmbeddedDocument's which contain their own
        private/public data.

        It attempts to handle multiple inputs types to avoid as many
        translation steps as possible.
        """
        internal_fields = cls._get_internal_fields()

        # This `handle_doc` implementation behaves as a blacklist
        containers = (list, dict)
        def handle_doc(doc_dict):
            for k,v in doc_dict.items():
                if k in internal_fields:
                    del doc_dict[k]
                elif isinstance(v, EmbeddedDocument):
                    doc_dict[k] = v.make_ownersafe(v.to_python())
                elif isinstance(v, containers) and len(v) > 0:
                    if isinstance(v[0], EmbeddedDocument):
                        doc_dict[k] = [doc.make_ownersafe(doc.to_python())
                                       for doc in v]
            return doc_dict

        trimmed = cls._safe_data_from_input(handle_doc, doc_dict_or_dicts)
        return trimmed

    @classmethod
    def make_json_ownersafe(cls, doc_dict_or_dicts):
        """Trims the object using make_ownersafe and dumps to JSON
        """
        trimmed = cls.make_ownersafe(doc_dict_or_dicts)
        return json.dumps(trimmed)
    
    @classmethod
    def make_publicsafe(cls, doc_dict_or_dicts):
        """This funciton ensures found_data only contains the keys as
        listed in cls._public_fields.

        It also knows to check for EmbeddedDocument's which contain their own
        private/public data.

        This function can be safely called without calling make_json_ownersafe
        first because it treats cls._public_fields as a whitelist and
        removes anything not listed.
        """
        if cls._public_fields is None:
            return cls.make_ownersafe(doc_dict_or_dicts)
        
        # This `handle_doc` implementation behaves as a whitelist
        containers = (list, dict)
        def handle_doc(doc_dict):
            for k,v in doc_dict.items():
                if k not in cls._public_fields:
                    del doc_dict[k]
                elif isinstance(v, EmbeddedDocument):
                    doc_dict[k] = v.make_publicsafe(v.to_python())
                elif isinstance(v, containers) and len(v) > 0:
                    if isinstance(v[0], EmbeddedDocument):
                        doc_dict[k] = [doc.make_publicsafe(doc.to_python())
                                       for doc in v]
            return doc_dict
        
        trimmed = cls._safe_data_from_input(handle_doc, doc_dict_or_dicts)
        return trimmed

    @classmethod
    def make_json_publicsafe(cls, doc_dict_or_dicts):
        """Trims the object using make_publicsafe and dumps to JSON
        """
        trimmed = cls.make_publicsafe(doc_dict_or_dicts)
        return json.dumps(trimmed)

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
                    e = DictPunch('Overwrite of internal fields attempted', k, v)
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
                except DictPunch, e:
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

