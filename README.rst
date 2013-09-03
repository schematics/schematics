==========
Schematics
==========

.. rubric:: Python Data Structures for Humans™.

.. image:: https://secure.travis-ci.org/j2labs/schematics.png?branch=master
  :target: https://secure.travis-ci.org/j2labs/schematics
  :alt: Build Status


About
=====

Schematics is a Python library to combine types into structures, validate them,
and transform the shapes of your data based on simple descriptions.

The internals are similar to ORM type systems, but there is no database layer
in Schematics.  Instead, Schematics believes the task of building a database
layer is made significantly easier when Schematics handles everything but
writing the query.

Further, it can be used for a range of tasks where having a database involved
may not make sense.

Some common use cases:

+ Design and document specific data structures for code
+ Convert structures to and from different formats, like JSON or MsgPack
+ Validate API inputs
+ Remove fields based on access rights of some data's recipient
+ Define message formats for communications protocols, like an RPC
+ Custom persistence layers.


Examples
--------

This is a simple Model.

.. code:: python

  >>> from schematics.models import Model
  >>> from schematics.types import StringType, URLType
  >>> class Person(Model):
  ...     name = StringType(required=True)
  ...     website = URLType()
  ...
  >>> person = Person({'name': u'Joe Strummer', 
  ...                  'url': 'http://soundcloud.com/joestrummer'})
  >>> person.name
  u'Joe Strummer'

Serializing the data to JSON.

.. code:: python

  >>> import json
  >>> json.dumps(person.to_primitive())
  {"name": "Joe Strummer", "url": "http://soundcloud.com/joestrummer"}

Let's try validating without a name value, since it's required.

.. code:: python

  >>> person = Person()
  >>> person.url = 'http://www.amontobin.com/'
  >>> person.validate()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "schematics/models.py", line 231, in validate
      raise ModelValidationError(e.messages)
  schematics.exceptions.ModelValidationError: {'name': [u'This field is required.']}

Add the field and validation passes

.. code:: python

  >>> person = Person()
  >>> person.name = 'Amon Tobin'
  >>> person.url = 'http://www.amontobin.com/'
  >>> person.validate()
  >>> 
