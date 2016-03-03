==========
Schematics
==========

.. rubric:: Python Data Structures for Humans™.

.. image:: https://travis-ci.org/schematics/schematics.svg?branch=development
   :target: https://travis-ci.org/schematics/schematics
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/schematics/schematics/badge.svg?branch=development
   :target: https://coveralls.io/github/schematics/schematics?branch=development 
   :alt: Coverage


News
====

After a period of sparse activity, Schematics has again been under heavy development as of late.

It is recommended that new users get started with the latest development release instead
of the stable release. To do this, add the ``--pre`` option when installing via ``pip``::

    pip install --pre schematics


About
=====

**Project documentation:** http://schematics.readthedocs.org/en/latest/

Schematics is a Python library to combine types into structures, validate them,
and transform the shapes of your data based on simple descriptions.

The internals are similar to ORM type systems, but there is no database layer
in Schematics.  Instead, we believe that building a database
layer is made significantly easier when Schematics handles everything but
writing the query.

Further, it can be used for a range of tasks where having a database involved
may not make sense.

Some common use cases:

+ Design and document specific `data structures <https://schematics.readthedocs.org/en/latest/usage/models.html>`_
+ `Convert structures <https://schematics.readthedocs.org/en/latest/usage/exporting.html#converting-data>`_ to and from different formats such as JSON or MsgPack
+ `Validate <https://schematics.readthedocs.org/en/latest/usage/validation.html>`_ API inputs
+ `Remove fields based on access rights <https://schematics.readthedocs.org/en/latest/usage/exporting.html>`_ of some data's recipient
+ Define message formats for communications protocols, like an RPC
+ Custom `persistence layers <https://schematics.readthedocs.org/en/latest/usage/models.html#model-configuration>`_


Example
=======

This is a simple Model. ::

  >>> from schematics.models import Model
  >>> from schematics.types import StringType, URLType
  >>> class Person(Model):
  ...     name = StringType(required=True)
  ...     website = URLType()
  ...
  >>> person = Person({'name': u'Joe Strummer',
  ...                  'website': 'http://soundcloud.com/joestrummer'})
  >>> person.name
  u'Joe Strummer'

Serializing the data to JSON. ::

  >>> import json
  >>> json.dumps(person.to_primitive())
  {"name": "Joe Strummer", "website": "http://soundcloud.com/joestrummer"}

Let's try validating without a name value, since it's required. ::

  >>> person = Person()
  >>> person.website = 'http://www.amontobin.com/'
  >>> person.validate()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "schematics/models.py", line 231, in validate
      raise DataError(e.messages)
  schematics.exceptions.DataError: {'name': ['This field is required.']}

Add the field and validation passes::

  >>> person = Person()
  >>> person.name = 'Amon Tobin'
  >>> person.website = 'http://www.amontobin.com/'
  >>> person.validate()
  >>>


.. _coverage:

Testing & Coverage support
==========================

Run coverage and check the missing statements. ::

  $ coverage run --source schematics -m py.test && coverage report

