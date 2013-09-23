==========
Schematics
==========

.. rubric:: Python Data Structures for Humans™.

.. image:: https://secure.travis-ci.org/j2labs/schematics.png?branch=master
  :target: https://secure.travis-ci.org/j2labs/schematics
  :alt: Build Status

**For more information, please see our documentation:** http://schematics.readthedocs.org/en/latest/


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

+ Design and document specific `data structures <https://schematics.readthedocs.org/en/latest/usage/models.html>`_
+ `Convert structures <https://schematics.readthedocs.org/en/latest/usage/exporting.html#converting-data>`_ to and from different formats such as JSON or MsgPack
+ `Validate <https://schematics.readthedocs.org/en/latest/usage/validation.html>`_ API inputs
+ `Remove fields based on access rights <https://schematics.readthedocs.org/en/latest/usage/exporting.html>`_ of some data's recipient
+ Define message formats for communications protocols, like an RPC
+ Custom `persistence layers <https://schematics.readthedocs.org/en/latest/usage/models.html#model-configuration>`_


Examples
--------

This is a simple Model.

::

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

Serializing the data to JSON.

::

  >>> import json
  >>> json.dumps(person.to_primitive())
  {"name": "Joe Strummer", "website": "http://soundcloud.com/joestrummer"}

Let's try validating without a name value, since it's required.

::

  >>> person = Person()
  >>> person.website = 'http://www.amontobin.com/'
  >>> person.validate()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "schematics/models.py", line 231, in validate
      raise ModelValidationError(e.messages)
  schematics.exceptions.ModelValidationError: {'name': [u'This field is required.']}

Add the field and validation passes

::

  >>> person = Person()
  >>> person.name = 'Amon Tobin'
  >>> person.website = 'http://www.amontobin.com/'
  >>> person.validate()
  >>> 

What's with the fork?
=====================

At the top of this projects Github page is says "forked from
exfm/dictshield".  James (@j2labs) started dictshield while working
for exfm.  It was open sourced, so he forked it and continued work on
it.

Alas, the name, which was originally a 3am decision to make me James
laugh turned into something that was awkward and a little crude, so it
was renamed Schematics.

DictShield still exists, but consider anything with that label to be
a ghost from this project's early years.
