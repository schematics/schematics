.. _types:

=====
Types
=====

Types are the smallest definition of structure in Schematics.  They represent
structure by offering functions to inspect or mutate the data in some way.

The three most interesting functions for types are ``to_native``,
``to_primitive``, and ``validate``.  There are also ways to extend the rules of
validation to customize precision.


Coercion and Conversion
=======================

A simple example is the ``DateTimeType``.

  >>> from schematics.types import DateTimeType
  >>> dt_t = DateTimeType()

The ``to_native`` function transforms an ISO8601 formatted date string into a 
Python ``datetime.datetime``.

  >>> dt = dt_t.to_native('2013-08-31T02:21:21.486072')
  >>> dt
  datetime.datetime(2013, 8, 31, 2, 21, 21, 486072)

The ``to_primitive`` function changes it back to a langauge agnostic form, in
this case an ISO8601 formatted string, just like we used above.

  >>> dt_t.to_primitive(dt)
  '2013-08-31T02:21:21.486072'


Validation
==========

Validation can be as simple as successfully calling ``to_native``, but
sometimes more is needed.

