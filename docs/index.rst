
Schematics
==========

Schematics is a Python library to validate and serialize data structures. The
internals are a lot like form libraries such as WTForms or Django forms, but
is geared towards richer data structures like JSON.

**Use Cases**

+ Validating untrusted data from clients
+ Use with ``json.dumps`` and ``json.loads``
+ Enforce object schemas across internal datastores
+ Document your object schemas in code for schemaless NoSQL

Quickstart
~~~~~~~~~~

Describe data schemas and data geometry with Python classes:

.. code-block:: python

  from schematics.models import Model
  from schematics.types import StringType

  class User(Model):
      name = StringType()

Init ``User`` with some data:

.. code-block:: python

  >>> user = User({'name': u'Clint Eastwood'})
  >>> user.name
  u'Clint Eastwood'

Serialization and Roles
~~~~~~~~~~~~~~~~~~~~~~~

To present data to clients we have the ``Model.serialize`` method. Default behavior
is to output the same data you would need to reproduce the model in it’s current
state.

.. code-block:: python

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

.. code-block:: python

  >>> movie.serialize('public')
  {'name': u'Trainspotting'}
  >>>

Validation
~~~~~~~~~~

Custom validation per field is achieved callables in ``BaseField.validators``.

.. code-block:: python

  >>> from schematics.exceptions import ValidationError
  >>> def is_uppercase(value):
  ...     if value.upper() != value:
  ...         raise ValidationError(u'Please speak up!')
  ...     return value
  ...
  >>> class Person(Model):
  ...     name = StringType(validators=[is_uppercase])
  ...
  >>> me = Person({'name': u'Jökull'})  # Returns False
  >>> me.errors
  {'name': [u'Please speak up!']}
  >>>

What about data integrity? Models don’t guarantee data integrity. They can be
instantiated with partial data:

.. code-block:: python

  >>> from schematics.types import StringType, IntType, BooleanType
  >>> from schematics.models import Model
  >>> class Person(Model):
      name = StringType(required=True)
      age = IntType(required=True)
  ...
  >>> p1 = Person({'name': 'jbone'})
  >>> p1.validate(raises=False)
  False
  >>> p1.validate({'age': 26})
  True
  >>> p1.serialize()
  {'age': 26, 'name': u'jbone'}

Notice that the model received part of the data on init without complaints.
``__init__`` and  ``validate`` are much the same, with an important difference: By
default  ``__init__`` accepts partial data and validates the keys supplied,
whereas  ``validate`` sets partial to ``False``. Both can be overriden with the
``partial`` keyword argument. The reason ``p1.validate({'age': 26})`` validated
above, with ``partial = False`` is that ``name`` was already populated internally.

What about validation based on other data? Because the field declaration order
is preserved you can attach model level validation for fields that have access
to other data. The order whith which fields are validated is the same as
field declarations:

.. code-block:: python

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
  >>> Signup().validate({'name': u'Brad', 'call_me': True})
  False

Here ``validate_call_me`` can check the internal data state as it becomes
populated *in the order that fields were defined on the model*.

Detailed Example
~~~~~~~~~~~~~~~~

What else can Schematics do?

.. code-block:: python

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

``ModelType`` and ``ListType`` traverse validation or serialization of a model down
to their subfields. You can express structures as deep as you like.

.. code-block:: python

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

You can patch the object by assigning attributes to fields with raw data too
(which  fails if the field doesn’t validate).

.. code-block:: python

  >>> actor.movies
  [<Movie: Movie object>]

Notice that ``ModelType`` instances return ``Model`` instances.

API
===

.. Contents:

.. toctree::
   :maxdepth: 2

   api