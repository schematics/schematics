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

Word.


