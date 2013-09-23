==========
Validation
==========

To validate data in Schematics is to have both a data model and some input
data.  The data model describes what valid data looks like in different forms.

Here's a quick glance and some of the ways you can tweak validation.

::

  >>> from schematics.models import Model
  >>> from schematics.types import StringType
  >>> class Person(Model):
  ...     name = StringType()
  ...     bio = StringType(required=True)
  ...
  >>> p = Person()
  >>> p.name = 'Paul Eipper'
  >>> p.validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'bio': [u'This field is required.']}


Validation Errors
=================

Validation failures throw an exception called ``ValidationError``.  A
description of what failed is stored in ``messages``, which is a dictionary
keyed by the field name with a list of reasons the field failed.

::

  >>> from schematics.exceptions import ValidationError
  >>> try:
  ...     p.validate()
  ... except ValidationError, e:
  ...    print e.messages
  {'bio': [u'This field is required.']}


Extending Validation
====================

Validation for both types and models can be extended.  Whatever validation
system you require is probably expressable via Schematics..


Type-level Validation
---------------------

Here is a function that checks if a string is uppercase and throws a
``ValidationError`` if it is not.

::

  >>> from schematics.exceptions import ValidationError
  >>> def is_uppercase(value):
  ...     if value.upper() != value:
  ...         raise ValidationError(u'Please speak up!')
  ...     return value
  ...

And we can attach it to our StringType like this:

::

  >>> class Person(Model):
  ...     name = StringType(validators=[is_uppercase])
  ...

Using it is built into validation.

  >>> me = Person({'name': u'Jökull'})
  >>> me.validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'name': [u'Please speak up!']}

It is also possible to define new types with custom validation by subclassing a
type, like ``BaseType``, and implementing instance methods that start with
``validate_``.

::

  >>> from schematics.exceptions import ValidationError
  >>> class UppercaseType(StringType):
  ...     def validate_uppercase(self, value):
  ...         if value.upper() != value:
  ...             raise ValidationError("Value must be uppercase!")
  ...

Just like before, using it is now built in.

  >>> class Person(Model):
  ...     name = UppercaseType()
  ...
  >>> me = Person({'name': u'Jökull'})
  >>> me.validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'name': ['Value must be uppercase!']}


Model-level Validation
----------------------

What about field validation based on other model data? The order whith which
fields are declared is preserved inside the model. So if the validity of a field
depends on another field’s value, just make sure to declare it below its
dependencies:

::

  >>> from schematics.models import Model
  >>> from schematics.types import StringType, BooleanType
  >>> from schematics.exceptions import ValidationError
  >>>
  >>> class Signup(Model):
  ...     name = StringType()
  ...     call_me = BooleanType(default=False)
  ...     def validate_call_me(self, data, value):
  ...         if data['name'] == u'Brad' and data['call_me'] is True:
  ...             raise ValidationError(u'He prefers email.')
  ...         return value
  ...
  >>> Signup({'name': u'Brad'}).validate()
  >>> Signup({'name': u'Brad', 'call_me': True}).validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'call_me': [u'He prefers email.']}


More Information
~~~~~~~~~~~~~~~~

To learn more about **Validation**, visit the :ref:`Validation API <api_doc_validation>`
