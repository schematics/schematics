.. _models:

======
Models
======

Schematics models are the next form of structure above types.  They are a
collection types in a class.  When a `Type` is given a name inside a `Model`, it
is called a `field`.


Simple Model
============

Let's say we want to build a social network for weather.  At it's core, we'll
need a way to represent some temperature information and where that temp was
found.

.. code:: python

  import datetime
  from schematics.models import Model
  from schematics.types import StringType, DecimalType, DateTimeType

  class WeatherReport(Model):
      city = StringType()
      temperature = DecimalType()
      taken_at = DateTimeType(default=datetime.datetime.now)

That'll do.  Let's try using it.

.. code:: python

  >>> wr = WeatherReport({'city': 'NYC', 'temperature': 80})
  >>> wr.temperature
  Decimal('80.0')

And remember that ``DateTimeType`` we set a default callable for?

.. code:: python

  >>> wr.taken_at
  datetime.datetime(2013, 8, 21, 13, 6, 38, 11883)


Model Configuration
===================

Models offer a few configuration options.  Options are attached in the form of a
class.

.. code:: python 

  class Whatever(Model):
      ...
      class Options:
          option = value

``namespace`` is a namespace identifier that can be used with persistence
layers.

.. code:: python 

  class Whatever(Model):
      ...
      class Options:
          namespace = "whatever_bucket"

``roles`` is a dictionary that stores whitelists and blacklists.

.. code:: python

  class Whatever(Model):
      ...
      class Options:
          roles = {
              'public': whitelist('some', 'fields'),
              'owner': blacklist('some', 'internal', 'stuff'),
          }

``serialize_when_none`` can be ``True`` or ``False``.  It's behavior is
explained here: :ref:`_exporting_serialize_when_none`.

.. code:: python

  class Whatever(Model):
      ...
      class Options:
          serialize_when_none = False

