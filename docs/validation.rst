Validation
==========


``Schematics`` is very useful for validating data structures, e.g. validation untrusted json in a REST API.

.. doctest:: validation

  >>> from schematics.models import Model
  >>> from schematics.types import StringType
  >>> class Person(Model):
  ...     name = StringType(required=True)
  ...     bio = StringType(required=True)
  ...
  >>> p = Person()
  >>> p.validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'bio': [u'This field is required.'], 'name': [u'This field is required.']}

``ModelValidationError.messages`` contains a dictionary of messages that can be used to
display friendly error messages to end users.

.. doctest:: validation

  >>> from schematics.exceptions import ValidationError
  >>> try:
  ...     p.validate()
  ... except ValidationError, e:
  ...    print e.messages
  {'bio': [u'This field is required.'], 'name': [u'This field is required.']}

Custom validation per field is achieved using callables in ``BaseType.validators``.

.. doctest::

  >>> from schematics.exceptions import ValidationError
  >>> def is_uppercase(value):
  ...     if value.upper() != value:
  ...         raise ValidationError(u'Please speak up!')
  ...     return value
  ...
  >>> class Person(Model):
  ...     name = StringType(validators=[is_uppercase])
  ...
  >>> me = Person({'name': u'Jökull'})
  >>> me.validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'name': [u'Please speak up!']}

It is also possible to define new types with custom validation by subclassing ``BaseType`` and
implementing instance methods that start with ``validate__``

.. doctest::

  >>> from schematics.exceptions import ValidationError
  >>> class UppercaseType(StringType):
  ...     def validate_uppercase(self, value):
  ...         if value.upper() != value:
  ...             raise ValidationError("Value must be uppercase!")
  ...
  >>> class Person(Model):
  ...     name = UppercaseType()
  ...
  >>> me = Person({'name': u'Jökull'})
  >>> me.validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'name': ['Value must be uppercase!']}

What about field validation based on other model data? The order whith which
fields are declared is preserved inside the model. So if the validity of a field
depends on another field’s value, just make sure to declare it below its
dependencies:

.. doctest::

  >>> from schematics.models import Model
  >>> from schematics.types import StringType, BooleanType
  >>> from schematics.exceptions import ValidationError
  >>>
  >>> class Signup(Model):
  ...     name = StringType()
  ...     call_me = BooleanType(default=False)
  ...     def validate_call_me(self, data, value):
  ...         if data['name'] == u'Brad' and value is True:
  ...             raise ValidationError(u'I don\'t call Brads!')
  ...         return value
  ...
  >>> Signup({'name': u'Brad'}).validate()
  >>> Signup({'name': u'Brad', 'call_me': True}).validate()
  Traceback (most recent call last):
  ...
  ModelValidationError: {'call_me': [u'I don\'t call Brads!']}


Detailed Example
~~~~~~~~~~~~~~~~

What else can Schematics do?

.. testcode:: detailed

  from schematics.models import Model
  from schematics.types import StringType, IntType, BooleanType
  from schematics.types.compound import ListType, ModelType

  class Movie(Model):
      name = StringType(required=True)
      year = IntType(required=True)
      credits = ListType(StringType())

      def __unicode__(self):
          return u"{} ({})".format(self.name, self.year)

  class Actor(Model):
      name = StringType(required=True)
      movies = ListType(ModelType(Movie))
      has_agent = BooleanType(default=True)
      breakout_movie = ModelType(Movie)

Special field types ``ModelType`` and ``ListType`` allow traversal of validation
or serialization of nested fields. With these you can express deep structures.

.. doctest:: detailed

  >>> actor = Actor({
  ...     'name': u'Tom Cruise',
  ...     'movies': [{
  ...         'name': u'Top Gun',
  ...         'year': 1986,
  ...         'credits': ['Tony Scott']
  ...     }]
  ... })
  ...
  >>> actor.name
  u'Tom Cruise'
  >>> actor.movies[0].name
  u'Top Gun'
  >>> actor.movies[0].credits
  [u'Tony Scott']

You can patch the object by assigning attributes to fields with raw data too
(which fails if the field is unable to convert the data cleanly).

.. doctest:: detailed

  >>> actor.movies = [{"name": "Knight and Day", "year": 2010}]
  >>> movie = actor.movies[0]
  >>> movie
  <Movie: Knight and Day (2010)>
  >>> actor.breakout_movie = u"Not a movie!"
  Traceback (most recent call last):
  ...
  ConversionError: [u'Please use a mapping for this field or Movie instance instead of str.']

Notice that ``ModelType`` fields return ``Model`` instances.

You can patch the object by assigning attributes to fields with raw data too
(which  fails if the field doesn’t validate).

It is also possible to define roles that filter which attributes appear in the
serialized output

.. testcode:: detailed

  from schematics.models import Model
  from schematics.types import StringType, IntType, BooleanType
  from schematics.types.compound import ListType, ModelType
  from schematics.serialize import blacklist

  class Movie(Model):
      name = StringType(required=True)
      year = IntType(required=True)
      credits = ListType(StringType())

      class Options:
          roles = {
            "public": blacklist("credits")
          }

These roles behave pretty much as you expect with respect to subclassing and
embedded objects using one of the compound types ``ModelType``, ``ListType``, ``DictType``.
