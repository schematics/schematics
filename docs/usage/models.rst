.. _models:

======
Models
======

Schematics models are the next form of structure above types.  They are a
collection types in a class.  When a `Type` is given a name inside a `Model`, it
is called a `field`.


.. _simple_model:

Simple Model
============

Let's say we want to build a social network for weather.  At it's core, we'll
need a way to represent some temperature information and where that temp was
found.

::

  import datetime
  from schematics.models import Model
  from schematics.types import StringType, DecimalType, DateTimeType

  class WeatherReport(Model):
      city = StringType()
      temperature = DecimalType()
      taken_at = DateTimeType(default=datetime.datetime.now)

That'll do.  Let's try using it.

::

  >>> wr = WeatherReport({'city': 'NYC', 'temperature': 80})
  >>> wr.temperature
  Decimal('80.0')

And remember that ``DateTimeType`` we set a default callable for?

::

  >>> wr.taken_at
  datetime.datetime(2013, 8, 21, 13, 6, 38, 11883)


.. _model_configuration:

Model Configuration
===================

Models offer a few configuration options.  Options are attached in the form of a
class.

:: 

  class Whatever(Model):
      ...
      class Options:
          option = value

``namespace`` is a namespace identifier that can be used with persistence
layers.

:: 

  class Whatever(Model):
      ...
      class Options:
          namespace = "whatever_bucket"

``roles`` is a dictionary that stores whitelists and blacklists.

::

  class Whatever(Model):
      ...
      class Options:
          roles = {
              'public': whitelist('some', 'fields'),
              'owner': blacklist('some', 'internal', 'stuff'),
          }

``serialize_when_none`` can be ``True`` or ``False``.  It's behavior is
explained here: :ref:`exporting_serialize_when_none`.

::

  class Whatever(Model):
      ...
      class Options:
          serialize_when_none = False


More Information
~~~~~~~~~~~~~~~~

To learn more about **Models**, visit the :ref:`Models API <api_doc_models>`
