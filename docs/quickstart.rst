.. _quickstart:

================
Quickstart Guide
================

Working with Schematics begins with modeling the data, so this tutorial will
start there.

After that we will take a quick look at serialization, validation, and what it
means to save this data to a database.


Simple Model
============

Let's say we want to build a structure for storing weather data.  At it's core,
we'll need a way to represent some temperature information and where that temp
was found.

::

  import datetime
  from schematics.models import Model
  from schematics.types import StringType, DecimalType, DateTimeType

  class WeatherReport(Model):
      city = StringType()
      temperature = DecimalType()
      taken_at = DateTimeType(default=datetime.datetime.now)

That'll do.

Here's what it looks like use it.

::

  >>> t1 = WeatherReport({'city': 'NYC', 'temperature': 80})
  >>> t2 = WeatherReport({'city': 'NYC', 'temperature': 81})
  >>> t3 = WeatherReport({'city': 'NYC', 'temperature': 90})
  >>> (t1.temperature + t2.temperature + t3.temperature) / 3
  Decimal('83.66666666666666666666666667')

And remember that ``DateTimeType`` we set a default callable for?

::

  >>> t1.taken_at
  datetime.datetime(2013, 8, 21, 13, 6, 38, 11883)


Validation
==========

Validating data is fundamentally important for many systems.

This is what it looks like when validation succeeds.

::

  >>> t1.validate()
  >>>

And this is what it looks like when validation fails.

::

  >>> t1.taken_at = 'whatever'
  >>> t1.validate()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "schematics/models.py", line 229, in validate
      raise ModelValidationError(e.messages)
  schematics.exceptions.ModelValidationError: {'taken_at': [u'Could not parse whatever. Should be ISO8601.']}


Serialization
=============

Serialization comes in two primary forms.  In both cases the data is produced
as a dictionary.

The ``to_primitive()`` function will reduce the native Python types into string
safe formats.  For example, the ``DateTimeType`` from above is stored as a 
Python ``datetime``, but it will serialize to an ISO8601 format string.

::

  >>> t1.to_primitive()
  {'city': u'NYC', 'taken_at': '2013-08-21T13:04:19.074808', 'temperature': u'80'}

Converting to JSON is then a simple task.

::

  >>> json_str = json.dumps(t1.to_primitive())
  >>> json_str
  '{"city": "NYC", "taken_at": "2013-08-21T13:04:19.074808", "temperature": "80"}'

Instantiating an instance from JSON is not too different.

::

  >>> t1_prime = WeatherReport(json.loads(json_str))
  >>> t1_prime.taken_at
  datetime.datetime(2013, 8, 21, 13, 4, 19, 074808)


Persistence
===========

In many cases, persistence can be as easy as converting the model to a
dictionary and passing that into a query.

First, to get at the values we'd pass into a SQL database, we might call
``to_native()``.

Let's get a fresh ``WeatherReport`` instance.

::

  >>> wr = WeatherReport({'city': 'NYC', 'temperature': 80})
  >>> wr.to_native()
  {'city': u'NYC', 'taken_at': datetime.datetime(2013, 8, 27, 0, 25, 53, 185279), 'temperature': Decimal('80')}


With PostgreSQL
---------------

You'll want to create a table with this query:

.. code:: sql

  CREATE TABLE weatherreports(
      city varchar,
      taken_at timestamp,
      temperature decimal
  );


Inserting
~~~~~~~~~

Then, from Python, an insert statement could look like this:

::

  >>> q = "INSERT INTO weatherreports (city, taken_at, temperature) VALUES ('%s', '%s', '%s');"
  >>> query = q % (wr.city, wr.taken_at, wr.temperature)
  >>> query
  u"INSERT INTO temps (city, taken_at, temperature) VALUES ('NYC', '2013-08-29 17:49:41.284189', '80');"

Let's insert that into PostgreSQL using the ``psycopg2`` driver.

::

  >>> import psycopg2
  >>> db_conn = psycopg2.connect("host='localhost' dbname='mydb'")
  >>> cursor = db_conn.cursor()
  >>> cursor.execute(query)
  >>> db_conn.commit()


Reading
~~~~~~~

Reading isn't much different.

::

  >>> query = "SELECT city,taken_at,temperature FROM weatherreports;"
  >>> cursor = db_conn.cursor()
  >>> cursor.execute(query)
  >>> rows = dbc.fetchall()

Now to translate that data into instances

::

  >>> instances = list()
  >>> for row in rows:
  ...     (city, taken_at, temperature) = row
  ...     instance = WeatherReport()
  ...     instance.city = city
  ...     instance.taken_at = taken_at
  ...     instance.temperature = temperature
  ...     instances.append(instance)
  ...
  >>> instances
  [<WeatherReport: WeatherReport object>]

