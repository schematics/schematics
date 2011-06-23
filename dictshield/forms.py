"""This module attempts to offer new serialization / formatted output options,
with emphasis on usability in HTML forms.

Using it looks a bit like this:

    # Basic Document
    class Something(Document):
        owner = ObjectIdField()
        user = StringField()
        title = StringField(max_length=40)
        password = StringField(max_length=128)
        _private_fields = ['owner']

    # A second Document to demonstrate how things can fail
    class SomethingElse(Document):
        o = ObjectIdField()
        u = StringField()
        t = StringField(max_length=40)
    
    # Instantiate both
    s = Something()
    s.title = 'Misc something'
    se = SomethingElse()
    se.t = 'Misc something'

    # Bind a Form instance to Something
    f = Form(Something)

    # The formatting calls adhere to internal fields and know not to print them

    # Print a blank form.
    print f.as_div()

    # Print a form, prepopulated with values from `s`
    print f.as_div(s)
    
    # This call would throw an error as f is bound to `Something` because `se`
    # is a `SomethingElse` instance.
    print f.as_div(se)
"""


from dictshield.base import TopLevelDocumentMetaclass
from dictshield.base import BaseField


default_field_map = {
    'BooleanField': 'radio',
}

default_name_map = {
    'password': 'password',
}


class FormPunch(Exception):
    """Is Wayne Brady gonna have to choke a Dict?
    """
    pass


class Form(object):
    """This is the frame of a car with no doors, a seat for the driver and a
    steering wheel and two gears: div and paragraph
    """
    def __init__(self, model, field_map=default_field_map,
                 name_map=default_name_map):
        if not isinstance(model, TopLevelDocumentMetaclass):
            error_msg = '<model> argument must be top level DictShield class'
            raise FormPunch(error_msg)

        # Model should be a dictshield document
        self._model = model

        # The name of the class
        self._class_name = model._class_name

        # Field Maps allow mapping fields to input types
        self._field_map = field_map

        # Override field maps by class name of field
        self._name_map = name_map
            

    ###
    ### Formatting Helpers
    ###

    def _included_fields(self):
        """A generator that provides a collection of data per iteration for use
        in a formatting outputter, like `as_p`.
        """
        for name, field in self._model._fields.items():
            if field.field_name: # field itself must be correct
                if field.field_name in self._model._get_internal_fields():
                    continue

                # Human representation of the name
                name = name.replace('_', ' ')
                name = name.title()

                # These values are keys in override maps
                field_name = field.field_name
                field_class = field.__class__.__name__
                
                # If field is named in _name_map, use that field
                if field_name in self._name_map:
                    field_type = self._name_map[field_name]
                # If field not in _name_map, check for override in field_map
                elif field_class in self._field_map:
                    field_type = self._field_map[field_class]
                # Default to text input
                else:
                    field_type = 'text'            

                yield (name, field_type, field.field_name)


    def _format_loop(self, format_str, values):
        """The fundamental loop for generating a formatted output string for
        html forms. Takes a format string `format_str` and applies the list of
        values to it.

        Allows passing in a `DictShield` instance or a dictionary. Anything
        else throws an error.

        The `DictShield` instance will be converted to a dictionary using a call
        to `.to_python()`.
        """
        # Inspect the values given for adherence to self._model's design
        if values is None:
            values = dict()
        elif isinstance(values, self._model):
            if values.__class__.__name__ == self._class_name:
                values = values.to_python()
            else:
                error_str = '<values> argument doesn\'t match self._class_name'
                raise FormPunch(error_str)
        elif not isinstance(values, dict):
            error_str = '<values> argument must match self._model or be a dict'
            raise FormPunch(error_str)

        # Loop around the fields and print a formatted output string for each
        formatted = []
        for (name, type, field) in self._included_fields():
            value = values.get(field, None)
            if value:
                value_str = self._value_str(value)
            else:
                value_str = ''

            args = {
                'name': name,
                'type': type,
                'field': field,
                'value_str': value_str,
            }
            formatted.append(format_str % args)

        # we's done, dawg
        return '\n'.join(formatted)


    def _value_str(self, value):
        """An internal function for printing a value= attribute string as
        commonly found in html output.
        """
        # value is a Class 
        if isinstance(value, BaseField):
            return ''

        # value is not a class
        if value:
            return 'value="%s" ' % value
        else:
            return ''


    ###
    ### Form Generation
    ###

    def as_p(self, values=dict()):
        s = '<p>%(name)s: <input type="%(type)s" name="%(field)s" %(value_str)s /></p>'
        return self._format_loop(s, values)


    def as_div(self, values=dict()):
        s = """<div>
    <label>%(name)s:</label>
    <input type="%(type)s" name="%(field)s" %(value_str)s />
</div>
"""
        return self._format_loop(s, values)
