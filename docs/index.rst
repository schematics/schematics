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

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Basics

   Overview <self>
   basics/install
   basics/quickstart

.. contents::
   :local:
   :depth: 1


**Please note that the documentation is currently somewhat out of date.**


About
=====

Schematics is a Python library to combine types into structures, validate them,
and transform the shapes of your data based on simple descriptions.

The internals are similar to ORM type systems, but there is no database layer
in Schematics.  Instead, we believe that building a database
layer is made significantly easier when Schematics handles everything but
writing the query.

Further, it can be used for a range of tasks where having a database involved
may not make sense.

Some common use cases:

+ Design and document specific :ref:`data structures <models>`
+ :ref:`Convert structures <exporting_converting_data>` to and from different formats such as JSON or MsgPack
+ :ref:`Validate <validation>` API inputs
+ :ref:`Remove fields based on access rights <exporting>` of some data's recipient
+ Define message formats for communications protocols, like an RPC
+ Custom :ref:`persistence layers <model_configuration>`


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


Installing
==========

Install stable releases of Schematics with pip. ::

  $ pip install schematics

See the :doc:`basics/install` for more detail.


Getting Started
===============

New Schematics users should start with the :doc:`basics/quickstart`.  That is the
fastest way to get a look at what Schematics does.


Documentation
=============

Schematics exists to make a few concepts easy to glue together.  The types
allow us to describe units of data, models let us put them together into
structures with fields.  We can then import data, check if it looks correct,
and easily serialize the results into any format we need.

The User's Guide provides the high-level concepts, but the API documentation and
the code itself provide the most accurate reference.

.. toctree::
   :maxdepth: 2
   :caption: User's Guide

   usage/types
   usage/models
   usage/exporting
   usage/importing
   usage/validation

.. toctree::
   :maxdepth: 1
   :caption: API Reference

   schematics.models <api/models>
   schematics.validation <api/validation>
   schematics.transforms <api/transforms>
   schematics.types <api/types>
   schematics.contrib <api/contrib>


Development
===========

We welcome ideas and code.  We ask that you follow some of our guidelines
though.

See the :doc:`development/development` for more information.

.. toctree::
   :hidden:
   :caption: Development

   development/development
   development/community


Testing & Coverage
==================

Run ``coverage`` and check the missing statements. ::

  $ coverage run --source schematics -m py.test && coverage report

