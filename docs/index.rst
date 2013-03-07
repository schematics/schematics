.. Schematics documentation master file, created by
   sphinx-quickstart on Thu Mar  7 13:45:09 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Schematics
==========

Schematics is a Python library to validate and serialize data structures. The
internals are a lot like form libraries such as WTForms or Django forms, but
is geared towards richer data structures like JSON.

Great for:

+ Validating untrusted data from clients
+ Use with `json.dumps` and `json.loads`
+ Enforce object schemas across internal datastores
+ Document your object schemas in code for schemaless NoSQL

.. Contents:

.. toctree::
   :maxdepth: 2

   api

Quickstart
~~~~~~~~~~

Describe data schemas and data geometry with Python classes:

.. code-block:: python

  from schematics.models import Model
  from schematics.types import StringType

  class User(Model):
      name = StringType()

Init `User` with untrusted data to trigger validation:

.. code-block:: python

  >>> user = User({'name': u'Clint Eastwood'})
  >>> user.name
  u'Clint Eastwood'
  >>>

A more detailed example:

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

`ModelType` and `ListType` traverse validation or serialization of a model down
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

Notice that `ModelType` instances return `Model` instances.

Serialization
~~~~~~~~~~~~~



Validation
~~~~~~~~~~

Custom validation per field is achieved with a list of callables. By default only


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

