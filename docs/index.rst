
Schematics
==========

Schematics is a Python library to validate and serialize data structures. The
internals are a lot like form libraries such as WTForms or Django forms, but
is geared towards richer data structures like JSON.

**Use Cases**

+ Validating untrusted data from clients
+ Use with ``json.dumps`` and ``json.loads``
+ Enforce schemas and validation across internal datastores
+ Document your object schemas in code for schemaless NoSQL

Quickstart
~~~~~~~~~~

Describe data schemas and data geometry with Python classes:

.. testcode:: intro

  from schematics.models import Model
  from schematics.types import StringType, DecimalType

  class WeatherReport(Model):
      city = StringType()
      temperature = DecimalType()

Create a weather report object from primitive data types

.. doctest:: intro

  >>> report = WeatherReport({'city': u'Helsinki', 'temperature': '10.3'})
  >>> report.temperature
  Decimal('10.3')

Serialization and Roles
~~~~~~~~~~~~~~~~~~~~~~~

To present data to clients we have the ``Model.serialize`` method. Default
behavior is to output the same data you would need to reproduce the model in its
current state.

.. doctest::

  >>> from schematics.models import Model
  >>> from schematics.types import StringType
  >>> from schematics.serialize import whitelist
  >>>
  >>> class Movie(Model):
  ...     name = StringType()
  ...     director = StringType()
  ...     class Options:
  ...         roles = {'public': whitelist('name')}
  ...
  >>> movie = Movie({'name': u'Trainspotting', 'director': u'Danny Boyle'})
  >>> movie.serialize()
  {'director': u'Danny Boyle', 'name': u'Trainspotting'}

Great. We got the primitive data back. Date types would have been cast back and
forth etc.

What if we wanted to expose this to untrusted parties who mustn’t know the
director?

.. doctest::

  >>> movie.serialize('public')
  {'name': u'Trainspotting'}
  >>>

The role, if found, is also used to filter data in contained models (more on
nested structures below).

Validation
~~~~~~~~~~

Custom validation per field is achieved callables in ``BaseField.validators``.

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
  >>> me = Person({'name': u'Jökull'}, raises=False)
  >>> me.errors
  {'name': [u'Please speak up!']}
  >>>

If you want explicit exceptions, initialize with ``raises=True`` or call
``validate()`` on the object.

Calling validate accepts data too:

.. doctest::

  >>> from schematics.types import StringType, IntType, BooleanType
  >>> from schematics.models import Model
  >>> class Person(Model):
  ...     name = StringType(required=True)
  ...     age = IntType(required=True)
  ...
  >>> p1 = Person({'name': 'jbone'})
  >>> p1.validate(raises=False)
  False
  >>> p1.validate({'age': 26})
  True
  >>> p1.serialize()
  {'age': 26, 'name': u'jbone'}

The reason ``p1.validate({'age': 26})`` validated above is that ``name`` was
already populated internally. The internal state of the object was updated.
Only valid batches of data are applied to the internal state.

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
  ...             raise ValidationError(u'I’m sorry I never call people who’s name is Brad')
  ...         return value
  ...
  >>> Signup().validate({'name': u'Brad'})
  True
  >>> Signup().validate({'name': u'Brad', 'call_me': True}, raises=False)
  False

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
embedded objects using one of the compound types `ModelType`, `ListType`, `DictType`.

You can patch the object by assigning attributes to fields with raw data too
(which fails if the field doesn’t validate).

.. doctest:: detailed

  >>> actor.movies
  [<Movie: Movie object>]

Notice that ``ModelType`` fields return ``Model`` instances.

You can patch the object by assigning attributes to fields with raw data too
(which  fails if the field doesn’t validate).

API
===

.. Contents:

.. toctree::
   :maxdepth: 2

   api