#!/usr/bin/env python

"""This module puts the basic framework for the Document and it's Metaclass
together. The Metaclass attribute `_fields`_ informs the validation system
about *what* to validate. `_fields` is also used for mapping inputs and outputs
to corresponding members of the Document, fascilitating easy document validating
like:

    d = Document(**key_map)
    try:
        d.validate()
    except:
        handler_validation_fail()

It also provides the basic framework for throwing errors when input doesn't
match expected patterns, as we see with the exception handling.

A `DictPunch` exception is thrown when validation fails.

An `InvalidShield` exception is thrown when the input data can't be mapped
to a `Document`.
"""

### If you're using Python 2.6, you should use simplejson
try:
    import simplejson as json
except:
    import json

### If you wear a diaper, you can't use ObjectIdFields
try:
    import bson
except:
    pass

_document_registry = {}

def get_document(name):
    return _document_registry[name]


###
### Exceptions
###

class InvalidShield(Exception):
    """A shield has been put together incorrectly
    """
    pass

class DictPunch(Exception):
    """Wayne Brady's gonna have to punch someone in the dict when Wayne Brady's
    gotta deal with some bs input. Wayne Brady DOES NOT like bs input.
    """
    def __init__(self, reason, field_name, field_value, *args, **kwargs):
        super(DictPunch, self).__init__(*args, **kwargs)
        self.reason = reason
        self.field_name = field_name
        self.field_value = field_value

    def __str__(self):
        return '%s - %s(%s)' % (self.reason,
                                self.field_name,
                                self.field_value)


###
### Fields
###

class BaseField(object):
    """A base class for fields in a DictShield document. Instances of this class
    may be added to subclasses of `Document` to define a document's schema.
    """

    def __init__(self, uniq_field=None, field_name=None, required=False,
                 default=None, id_field=False, validation=None, choices=None):
        
        self.uniq_field = '_id' if id_field else uniq_field or field_name
        self.field_name = field_name
        self.required = required
        self.default = default
        self.validation = validation
        self.choices = choices
        self.id_field = id_field

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a document. Do 
        any necessary conversion between Python and `DictShield` types.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = instance._data.get(self.field_name)

        if value is None:
            value = self.default
            # Allow callable default values
            if callable(value):
                value = value()
        return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document.
        """
        instance._data[self.field_name] = value

    def for_python_dict(self, value):
        """Convert a DictShield type into native Python value
        """
        return self.for_python(value)

    def for_python(self, value):
        """Convert a DictShield type into native Python value
        """
        return value

    def for_json(self, value):
        """Convert a DictShield type into a value safe for JSON encoding
        """
        return self.for_python(value)

    def validate(self, value):
        """Perform validation on a value.
        """
        pass

    def _validate(self, value):
        # check choices
        if self.choices is not None:
            if value not in self.choices:
                raise DictPunch("Value must be one of %s."
                    % unicode(self.choices))

        # check validation argument
        if self.validation is not None:
            if callable(self.validation):
                if not self.validation(value):
                    raise DictPunch('Value does not match custom' \
                                          'validation method.')
            else:
                raise ValueError('validation argument must be a callable.')

        self.validate(value)

class ObjectIdField(BaseField):
    """A basic abstraction for ObjectId's. Users of `ObjectIdField` are
    expected to provide value safe for unicode.
    """
    def for_python(self, value):
        try:
            return bson.objectid.ObjectId(unicode(value))
        except Exception, e:
            raise InvalidShield(unicode(e))

    def for_json(self, value):
        return str(value)

    def validate(self, value):
        try:
            bson.objectid.ObjectId(unicode(value))
        except Exception, e:
            raise DictPunch('Invalid ObjectId', self.field_name, value)

###
### Metaclass design
###
        
class DocumentMetaclass(type):
    """Metaclass for all documents.
    """

    def __new__(cls, name, bases, attrs):
        metaclass = attrs.get('__metaclass__')
        super_new = super(DocumentMetaclass, cls).__new__
        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(cls, name, bases, attrs)

        doc_fields = {}
        class_name = [name]
        superclasses = {}
        simple_class = True
        for base in bases:
            # Include all fields present in superclasses
            if hasattr(base, '_fields'):
                doc_fields.update(base._fields)
                class_name.append(base._class_name)
                # Get superclasses from superclass
                superclasses[base._class_name] = base
                superclasses.update(base._superclasses)

            if hasattr(base, '_meta'):
                # Ensure that the Document class may be subclassed - 
                # inheritance may be disabled to remove dependency on 
                # additional fields _cls and _types
                if base._meta.get('allow_inheritance', True) == False:
                    raise ValueError('Document %s may not be subclassed' %
                                     base.__name__)
                else:
                    simple_class = False

        meta = attrs.get('_meta', attrs.get('meta', {}))

        if 'allow_inheritance' not in meta:
            meta['allow_inheritance'] = True

        # Only simple classes - direct subclasses of Document - may set
        # allow_inheritance to False
        if not simple_class and not meta['allow_inheritance']:
            raise ValueError('Only direct subclasses of Document may set '
                             '"allow_inheritance" to False')
        attrs['_meta'] = meta

        attrs['_class_name'] = '.'.join(reversed(class_name))
        attrs['_superclasses'] = superclasses

        # Add the document's fields to the _fields attribute
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, "__class__") and \
               issubclass(attr_value.__class__, BaseField):
                attr_value.field_name = attr_name
                if not attr_value.uniq_field:
                    attr_value.uniq_field = attr_name
                doc_fields[attr_name] = attr_value
        attrs['_fields'] = doc_fields

        new_class = super_new(cls, name, bases, attrs)
        for field in new_class._fields.values():
            field.owner_document = new_class

        return new_class

    def add_to_class(self, name, value):
        setattr(self, name, value)


class TopLevelDocumentMetaclass(DocumentMetaclass):
    """Metaclass for top-level documents (i.e. documents that have their own
    collection in the database.
    """

    def __new__(cls, name, bases, attrs):
        super_new = super(TopLevelDocumentMetaclass, cls).__new__
        # Classes defined in this package are abstract and should not have 
        # their own metadata with DB collection, etc.
        # __metaclass__ is only set on the class with the __metaclass__ 
        # attribute (i.e. it is not set on subclasses). This differentiates
        # 'real' documents from the 'Document' class
        if attrs.get('__metaclass__') == TopLevelDocumentMetaclass:
            return super_new(cls, name, bases, attrs)

        collection = name.lower()
        id_field = None

        base_meta = {}

        # Subclassed documents inherit collection from superclass
        for base in bases:
            if hasattr(base, '_meta'):
                if 'collection' in base._meta:
                    collection = base._meta['collection']
                id_field = id_field or base._meta.get('id_field')

        meta = {
            'collection': collection,
            'max_documents': None,
            'max_size': None,
            'id_field': id_field,            
        }
        meta.update(base_meta)

        # Apply document-defined meta options
        meta.update(attrs.get('meta', {}))
        attrs['_meta'] = meta

        # Set up collection manager, needs the class to have fields so use
        # DocumentMetaclass before instantiating CollectionManager object
        new_class = super_new(cls, name, bases, attrs)

        for field_name, field in new_class._fields.items():
            # Check for custom id key
            if field.id_field:
                current_id = new_class._meta['id_field']
                if current_id and current_id != field_name:
                    raise ValueError('Cannot override id_field')

                new_class._meta['id_field'] = field_name
                # Make 'Document.id' an alias to the real primary key field
                new_class.id = field

        if not new_class._meta['id_field']:
            new_class._meta['id_field'] = 'id'
            new_class._fields['id'] = ObjectIdField(uniq_field='_id')
            new_class.id = new_class._fields['id']

        return new_class

        
###
### Document structures
###

class BaseDocument(object):

    def __init__(self, **values):
        self._data = {}
        # Assign default values to instance
        for attr_name, attr_value in self._fields.items():
            # Use default value if present
            value = getattr(self, attr_name, None)
            setattr(self, attr_name, value)

        # Assign initial values to instance
        for attr_name,attr_value in values.items():
            try:
                setattr(self, attr_name, attr_value)
            # Put a diaper on the keys that don't belong and send 'em home
            except AttributeError:
                pass

    def validate(self):
        """Ensure that all fields' values are valid and that required fields
        are present.
        """
        # Get a list of tuples of field names and their current values
        fields = [(field, getattr(self, name)) 
                  for name, field in self._fields.items()]

        # Ensure that each field is matched to a valid value
        for field, value in fields:
            if value is not None and value != '': # treat empty strings is nonexistent
                try:
                    field._validate(value)
                except (ValueError, AttributeError, AssertionError):
                    raise DictPunch('Invalid value for field of type "%s": %s'
                                    % (field.__class__.__name__, value),
                                    field.field_name, value)
            elif field.required:
                raise DictPunch('Required field missing',
                                field.field_name, value)

    @classmethod
    def _get_subclasses(cls):
        """Return a dictionary of all subclasses (found recursively).
        """
        try:
            subclasses = cls.__subclasses__()
        except:
            subclasses = cls.__subclasses__(cls)

        all_subclasses = {}
        for subclass in subclasses:
            all_subclasses[subclass._class_name] = subclass
            all_subclasses.update(subclass._get_subclasses())
        return all_subclasses

    def __iter__(self):
        return iter(self._fields)

    def __getitem__(self, name):
        """Dictionary-style field access, return a field's value if present.
        """
        try:
            if name in self._fields:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        """Dictionary-style field access, set a field's value.
        """
        # Ensure that the field exists before settings its value
        if name not in self._fields:
            raise KeyError(name)
        return setattr(self, name, value)

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return u'<%s: %s>' % (self.__class__.__name__, u)

    def __str__(self):
        if hasattr(self, '__unicode__'):
            return unicode(self).encode('utf-8')
        return '%s object' % self.__class__.__name__

    ###
    ### Serialization
    ###

    def _to_fields(self, field_converter):
        """Returns a Python dictionary representing the Document's metastructure
        and values.
        """
        data = {}

        # First map the subclasses of BaseField
        for field_name, field in self._fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
                #data[field.uniq_field] = field.for_python(value)
                data[field.uniq_field] = field_converter(field, value)
                
        # Only add _cls and _types if allow_inheritance is not False
        if not (hasattr(self, '_meta') and
                self._meta.get('allow_inheritance', True) == False):
            data['_cls'] = self._class_name
            data['_types'] = self._superclasses.keys() + [self._class_name]
            
        if data.has_key('_id') and not data['_id']:
            del data['_id']
            
        return data

    def to_python_dict(self):
        """Returns a Python dictionary representing the Document's metastructure
        and values.
        """
        fun = lambda f, v: f.for_python_dict(v)
        data = self._to_fields(fun)
        return data

    def to_python(self):
        """Returns a Python dictionary representing the Document's metastructure
        and values.
        """
        fun = lambda f, v: f.for_python(v)
        data = self._to_fields(fun)
        return data

    def to_json(self):
        """Return data encoded as JSON.
        """
        #data = self.to_python()
        fun = lambda f, v: f.for_json(v)
        data = self._to_fields(fun)
        return json.dumps(data)

    @classmethod
    def _from_son(cls, son): # TODO rename to json 
        """Create an instance of a Document (subclass) from a BSON.
        """
        # get the class name from the document, falling back to the given
        # class if unavailable
        class_name = son.get(u'_cls', cls._class_name)
        
        data = dict((str(key), value) for key, value in son.items())

        if '_types' in data:
            del data['_types']

        if '_cls' in data:
            del data['_cls']
        # Return correct subclass for document type
        if class_name != cls._class_name:
            subclasses = cls._get_subclasses()
            if class_name not in subclasses:
                # Type of document is probably more generic than the class
                # that has been queried to return this SON
                return None
            cls = subclasses[class_name]

        present_fields = data.keys()
        #BUGFIX: changed fb_field to field_name and to_python to for_python
        for field_name, field in cls._fields.items():
            if field.field_name in data:
                value = data[field.uniq_field]
                data[field_name] = (value if value is None
                                    else field.for_python(value))

        obj = cls(**data)
        obj._present_fields = present_fields
        return obj

    def __eq__(self, other):
        if isinstance(other, self.__class__) and hasattr(other, 'id'):
            if self.id == other.id:
                return True
        return False


def subclass_exception(name, parents, module):
    return type(name, parents, {'__module__': module})
