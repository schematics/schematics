.. _types:

=====
Types
=====

Types are the smallest definition of structure in Schematics.  They represent
structure by offering functions to inspect or mutate the data in some way.

According to Schematics, a type is an instance of a way to do three things:

1. Coerce the data type into an appropriate representation in Python
2. Convert the Python representation into other formats suitable for
   serialization
3. Offer a precise method of validating data of many forms

These properties are implemented as ``to_native``, ``to_primitive``, and
``validate``. 


Coercion
========

A simple example is the ``DateTimeType``.

::

  >>> from schematics.types import DateTimeType
  >>> dt_t = DateTimeType()

The ``to_native`` function transforms an ISO8601 formatted date string into a 
Python ``datetime.datetime``.

::

  >>> dt = dt_t.to_native('2013-08-31T02:21:21.486072')
  >>> dt
  datetime.datetime(2013, 8, 31, 2, 21, 21, 486072)


Conversion
==========

The ``to_primitive`` function changes it back to a langauge agnostic form, in
this case an ISO8601 formatted string, just like we used above.

::

  >>> dt_t.to_primitive(dt)
  '2013-08-31T02:21:21.486072'


Validation
==========

Validation can be as simple as successfully calling ``to_native``, but
sometimes more is needed.  
data or behavior during a typical use, like serialization.

Let's look at the ``StringType``.  We'll set a ``max_length`` of 10.

::

  >>> st = StringType(max_length=10)
  >>> st.to_native('this is longer than 10')
  u'this is longer than 10'

It converts to a string just fine.  Now, let's attempt to validate it.

::

  >>> st.validate('this is longer than 10')
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "schematics/types/base.py", line 164, in validate
      raise ValidationError(errors)
  schematics.exceptions.ValidationError: [u'String value is too long.']


More Information
~~~~~~~~~~~~~~~~

To learn more about **Types**, visit the :ref:`Types API <api_doc_types>`