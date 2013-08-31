==========
Schematics
==========

.. rubric:: Python Data Structures for Humans™.

.. image:: https://secure.travis-ci.org/j2labs/schematics.png?branch=master
  :target: https://secure.travis-ci.org/j2labs/schematics
  :alt: Build Status


About
=====

Schematics is a Python library to validate, manipulate, and serialize data
structures. The internals are a lot like form libraries such as WTForms or
Django forms, but Schematics is geared towards richer data structures like
JSON.


Common use cases:

+ Create data structures for very specific types of data.
+ Convert structures to and from different formats, like JSON or a simple dict.
+ Validate API inputs.
+ Serialize data with / without fields, depending on how you're using it.
+ Define message formats for communications protocols, like an RPC.
+ Customer persistence layers.


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
  >>> json.dumps(person.to_native())
  {"name": "Joe Strummer", "url": "http://soundcloud.com/joestrummer"}

This is validation.

.. code:: python

  >>> person = Person()
  >>> try:
  ...     person.validate()
  ... except ValidationError, e:
  ...     print e.messages
  {'name': [u'This field is required.']}
