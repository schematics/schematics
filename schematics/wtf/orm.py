"""
Tools for generating forms based on Schematics Models
"""
from operator import itemgetter
from schematics import public
from wtforms import fields as f, validators, Form

def converts(*args):
    def _inner(func):
        func._converter_for = frozenset(args)
        return func
    return _inner


class ModelConverter():

    def __init__(self, converters=None):

        if not converters:
            converters = {}

        for name in dir(self):
            obj = getattr(self, name)
            if hasattr(obj, '_converter_for'):
                for classname in obj._converter_for:
                    converters[classname] = obj

        self.converters = converters

    def convert(self, model, field, field_args):
        kwargs = {
            'label': getattr(field, 'verbose_name', field.field_name),
            'description': '',
            'validators': [],
            'filters': [],
            'default': field.default,
        }
        if field_args:
            kwargs.update(field_args)

        if field.required:
            kwargs['validators'].append(validators.Required())
        else:
            kwargs['validators'].append(validators.Optional())

        if field.choices:
            kwargs['choices'] = field.choices
            if kwargs.pop('multiple', False):
                return f.SelectMultipleField(**kwargs)
            return f.SelectField(**kwargs)

        ftype = type(field).__name__

        if hasattr(field, 'to_form_field'):
            return field.to_form_field(model, kwargs)

        if ftype in self.converters:
            return self.converters[ftype](model, field, kwargs)

    @classmethod
    def _string_common(cls, model, field, kwargs):
        if field.max_length or field.min_length:
            kwargs['validators'].append(
                validators.Length(max=field.max_length or - 1,
                                  min=field.min_length or - 1))

    @classmethod
    def _number_common(cls, model, field, kwargs):
        if field.max_value or field.min_value:
            kwargs['validators'].append(
                validators.NumberRange(max=field.max_value,
                                       min=field.min_value))

    @converts('StringType')
    def conv_String(self, model, field, kwargs):
        if field.regex:
            kwargs['validators'].append(validators.Regexp(regex=field.regex))
        self._string_common(model, field, kwargs)
        if 'password' in kwargs:
            if kwargs.pop('password'):
                return f.PasswordField(**kwargs)
        if field.max_length:
            return f.StringField(**kwargs)
        return f.TextAreaField(**kwargs)

    @converts('URLType')
    def conv_URL(self, model, field, kwargs):
        kwargs['validators'].append(validators.URL())
        self._string_common(model, field, kwargs)
        return f.StringField(**kwargs)

    @converts('EmailType')
    def conv_Email(self, model, field, kwargs):
        kwargs['validators'].append(validators.Email())
        self._string_common(model, field, kwargs)
        return NoneStringField(**kwargs)

    @converts('IntType')
    def conv_Int(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.IntegerField(**kwargs)

    @converts('FloatType')
    def conv_Float(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.FloatField(**kwargs)

    @converts('DecimalType')
    def conv_Decimal(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.DecimalField(**kwargs)

    @converts('BooleanType')
    def conv_Boolean(self, model, field, kwargs):
        return f.BooleanField(**kwargs)

    @converts('DateTimeType')
    def conv_DateTime(self, model, field, kwargs):
        return f.DateTimeField(**kwargs)

    @converts('BinaryType')
    def conv_Binary(self, model, field, kwargs):
        #TODO: may be set file field that will save file`s data to MongoDB
        if field.max_bytes:
            kwargs['validators'].append(validators.Length(max=field.max_bytes))
        return f.TextAreaField(**kwargs)

    @converts('DictType')
    def conv_Dict(self, model, field, kwargs):
        return DictField(**kwargs)

    @converts('ListType')
    def conv_List(self, model, field, kwargs):
        if isinstance(field.field, ReferenceField):
            return ModelSelectMultipleField(model=field.field.document_type, **kwargs)
        if field.field.choices:
            kwargs['multiple'] = True
            return self.convert(model, field.field, kwargs)
        unbound_field = self.convert(model, field.field, {})
        kwargs = {
            'validators': [],
            'filters': [],
        }
        return f.FieldList(unbound_field, min_entries=0, **kwargs)

    @converts('SortedListType')
    def conv_SortedList(self, model, field, kwargs):
        #TODO: sort functionality, may be need sortable widget
        return self.conv_List(model, field, kwargs)

    @converts('GeoLocationType')
    def conv_GeoLocation(self, model, field, kwargs):
        #TODO: create geo field and widget (also GoogleMaps)
        return

    @converts('ModelType')
    def conv_EmbeddedDocument(self, model, field, kwargs):
        kwargs = {
            'validators': [],
            'filters': [],
        }
        form_class = model_form(field.document_type_obj, field_args={})
        return f.FormField(form_class, **kwargs)

    @converts('ReferenceField')
    def conv_Reference(self, model, field, kwargs):
        return ModelSelectField(model=field.document_type, **kwargs)

    @converts('GenericReferenceField')
    def conv_GenericReference(self, model, field, kwargs):
        return


def model_fields(model, only=None, exclude=None, field_args=None, converter=None):
    """
    Generate a dictionary of fields for a given Django model.

    See `model_form` docstring for description of parameters.
    """
    from schematics.models import Model
    if not isinstance(model, Model):
        raise TypeError('model must be a schematics.Model schema')

    converter = converter or ModelConverter()
    field_args = field_args or {}

# -old-     names = ((k, v.creation_counter) for k, v in model._fields.iteritems())
# -old-     field_names = map(itemgetter(0), sorted(names, key=itemgetter(1)))
# -old- 
# -old-     if only:
# -old-         field_names = (x for x in field_names if x in only)
# -old-     elif exclude:
# -old-         field_names = (x for x in field_names if x not in exclude)
# -old- 
# -old-     field_dict = {}
# -old-     for name in field_names:
# -old-         model_field = model._fields[name]
# -old-         field = converter.convert(model, model_field, field_args.get(name))
# -old-         if field is not None:
# -old-             field_dict[name] = field

    field_dict = { }
    for field_name, field in model._fields.items():
       # todo - check only/excludes
       form_field = converter.convert(model, field, field_args.get(field_name))
       if form_field is not None:
          field_dict[field_name] = form_field

    return field_dict


@public
def model_form(model, base_class=Form, only=None, exclude=None, field_args=None, converter=None):
    """
    Create a wtforms Form for a given Schematic Model schema::

        from schematics.wtf import model_form
        from myproject.myapp.schemas import MyModel
        MyForm = model_form(MyModel)

    :param model:
        A Schematics Model schema class
    :param base_class:
        Base form class to extend from. Must be a ``wtforms.Form`` subclass.
    :param only:
        An optional iterable with the property names that should be included in
        the form. Only these properties will have fields.
    :param exclude:
        An optional iterable with the property names that should be excluded
        from the form. All other properties will have fields.
    :param field_args:
        An optional dictionary of field names mapping to keyword arguments used
        to construct each field object.
    :param converter:
        A converter to generate the fields based on the model properties. If
        not set, ``ModelConverter`` is used.
    """
    field_dict = model_fields(model, only, exclude, field_args, converter)
    field_dict['model_class'] = model
    return type(model.__class__.__name__ + 'Form', (base_class,), field_dict)
