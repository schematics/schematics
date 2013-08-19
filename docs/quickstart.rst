Quickstart
~~~~~~~~~~

Describe data schemas and data geometry with Python classes without a lot
of boilerplate, i.e. instead of defining your models in the basic pythonic way

you can define you objects as a subclass of ``Model``:

.. testcode:: intro

  from schematics.models import Model
  from schematics.types import StringType, DecimalType

  class WeatherReport(Model):
      city = StringType()
      temperature = DecimalType()

Create a weather report object from primitive data types

.. doctest:: intro

  >>> report = WeatherReport({'city': 'Helsinki', 
  ...                         'temperature': '10.3'})
  >>> report.temperature
  Decimal('10.3')

Converting to other formats, like JSON, is easy.

.. doctest::

  >>> import json
  >>> report.serialize()
  {'city': u'Helsinki', 'temperature': u'10.3'}
  >>> json.dumps(report.serialize())
  '{"city": "Helsinki", "temperature": "10.3"}'

And you can validate the data is indeed the type you specified.

.. doctest::

    >>> wr.validate()
    >>> wr.temperature = 'foo'
    >>> wr.validate()
    Traceback (most recent call last):
    ...
    schematics.exceptions.ModelValidationError: {'temperature': ['Number failed to convert to a decimal']}
    >>>
