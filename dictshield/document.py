from base import (BaseDocument, DictPunch, DocumentMetaclass, TopLevelDocumentMetaclass)

__all__ = ['Document', 'EmbeddedDocument', 'DictPunch']


class EmbeddedDocument(BaseDocument):
    """A :class:`~dictshield.Document` that isn't stored in its own
    collection.  :class:`~dictshield.EmbeddedDocument`\ s should be used as
    fields on :class:`~dictshield.Document`\ s through the
    :class:`~dictshield.EmbeddedDocumentField` field type.
    """

    __metaclass__ = DocumentMetaclass


class Document(BaseDocument):
    """The base class used for defining the structure and properties of
    collections of documents stored in MongoDB. Inherit from this class, and
    add fields as class attributes to define a document's structure.
    Individual documents may then be created by making instances of the
    :class:`~dictshield.Document` subclass.

    A :class:`~dictshield.Document` subclass may be itself subclassed, to
    create a specialised version of the document that can be stored in the
    same collection. To facilitate this behaviour, `_cls` and `_types`
    fields are added to documents to specify the install class and the types
    in the Document class hierarchy. To disable this behaviour and remove
    the dependence on the presence of `_cls` and `_types`, set
    :attr:`allow_inheritance` to ``False`` in the :attr:`meta` dictionary.

    :attr:`_internal_fields` class field is used to list fields which are
    private and not meant to leave the system. This consists of `_id`, `_cls`
    and `_types` but a user can extend the lis of internal fields by defining
    a class level list field called _private_fields.

    If :attr:`_public_fields` is defined, the `make_json_publicsafe` method
    will use it as a whitelist for which fields to not erase.
    """

    __metaclass__ = TopLevelDocumentMetaclass

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
            return fun(data.to_mongo())

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
                data = [d.to_mongo() for d in data]
            return map(fun, data)

    @classmethod
    def make_json_ownersafe(cls, doc_dict_or_dicts):
        """This function removes internal fields and handles any steps
        required for making the data stucture (list, dict or Document)
        safe for transmission to the owner of the data.

        It attempts to handle multiple inputs types to avoid as many
        translation steps as possible.
        """
        internal_fields = cls._get_internal_fields()

        def handle_doc(data):
            # internal_fields is a blacklist
            for f in internal_fields:
                if data.has_key(f):
                    del data[f]
            return data

        return cls._safe_data_from_input(handle_doc, doc_dict_or_dicts)
        
    
    @classmethod
    def make_json_publicsafe(cls, doc_dict_or_dicts):
        """This funciton ensures found_data only contains the keys as
        listed in cls._public_fields.

        This function can be safely called without calling make_json_ownersafe
        first because it treats cls._public_fields as a whitelist and
        removes anything not listed.
        """
        if cls._public_fields is None:
            raise DictPunch('make_json_publicsafe called cls with no _public_fields')
        
        def handle_doc(doc):
            # public_fields is a whitelist
            for f in doc.keys():
                if f not in cls._public_fields:
                    del doc[f]
            return doc
        
        return cls._safe_data_from_input(handle_doc, doc_dict_or_dicts)


    @classmethod
    def _validate_helper(cls, fun, values, validate_all=False):
        """This is a convenience function that loops over the given values
        and attempts to validate them against the class definition. It only
        validates the data in values and does not guarantee a complete document
        is present.

        'not present' is defined as not having a value OR having '' (or u'')
        as a value.
        """
        if not hasattr(cls, '_fields'):
            raise ValueError('cls is not a DictShield')
        
        internal_fields = cls._get_internal_fields()

        if validate_all:
            exceptions = list()
            handle_exception = lambda e: exceptions.append(e)
        else:
            def handle_exception(e):
                raise e

        for k,v in cls._fields.items():
            # handle common id name
            if k is 'id': 
                k = '_id'

            # we don't accept internal fields from users
            if k in internal_fields and k in values:
                value_is_default = (values[k] is v.default)
                if not value_is_default:
                    e = DictPunch('Overwrite of internal fields attempted', k, v)
                    handle_exception(e)
                    continue

            if fun(k, v):
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
