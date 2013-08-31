.. _models:

======
Models
======

Schematics models


Simple Model
============

Let's say we want to build a social network for weather.  At it's core, we'll
need a way to represent some temperature information and where that temp was
found.

.. testcode:: intro

  import datetime
  from schematics.models import Model
  from schematics.types import StringType, DecimalType, DateTimeType

  class WeatherReport(Model):
      city = StringType()
      temperature = DecimalType()
      when = DateTimeType(default=datetime.datetime.now)

That'll do.

Here's what it looks like use it.

.. doctest:: intro

  >>> t1 = WeatherReport({'city': 'NYC', 'temperature': 80})
  >>> t2 = WeatherReport({'city': 'NYC', 'temperature': 81})
  >>> t3 = WeatherReport({'city': 'NYC', 'temperature': 90})
  >>> (t1.temperature + t2.temperature + t3.temperature) / 3
  Decimal('83.66666666666666666666666667')

And remember that ``DateTimeType`` we set a default callable for?

  >>> t1.when
  datetime.datetime(2013, 8, 21, 13, 6, 38, 11883)


Serialization
=============

The ``serialize()`` function will reduce the native Python types into string
safe formats.  For example, the ``DateTimeType`` from above is stored as a 
Python ``datetime``, but it will serialize to an ISO8601 format string.

  >>> t1.serialize()
  {'city': u'NYC', 'when': '2013-08-21T13:04:19.074808', 'temperature': u'80'}

Converting to JSON is then a simple task.

  >>> json.dumps(t1.serialize())
  '{"city": "NYC", "when": "2013-08-21T13:04:19.074808", "temperature": "80"}'

Instantiating an instance from JSON is not too different.

  >>> json_str = json.dumps(t1.serialize())
  >>> json_str
  '{"city": "NYC", "when": "2013-08-21T13:06:38.011883", "temperature": "80"}'

  >>> t1_prime = WeatherReport(json.loads(json_str))
  >>> t1_prime.when
  datetime.datetime(2013, 8, 21, 13, 6, 38, 11883)


Validation
==========

Validating data is fundamentally important for many systems.

This is what it looks like when validation succeeds.

  >>> t1.validate()
  >>>

And this is what it looks like when validation fails.

.. doctest::

  >>> t1.when = 'whatever'
  >>> t1.validate()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "schematics/models.py", line 229, in validate
      raise ModelValidationError(e.messages)
  schematics.exceptions.ModelValidationError: {'when': [u'Could not parse whatever. Should be ISO8601.']}

