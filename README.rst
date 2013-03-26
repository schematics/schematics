**Python Data Structures for Humans™.**

This is a fork of the `original project <https://github.com/j2labs/schematics>`_
by @j2labs

There are big API changes in this fork. However it **is** documented and tested.
Join #schematics on Freenode if you are interested in this project. This fork is
in the process of being merged into the original.

.. image:: https://secure.travis-ci.org/plain-vanilla-games/schematics.png?branch=master
  :target: https://secure.travis-ci.org/plain-vanilla-games/schematics
  :alt: Build Status

Show me the Code!
~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from schematics.models import Model
  >>> from schematics.types import StringType
  >>> class Person(Model):
  ...     name = StringType(required=True)
  ...
  >>> person = Person({'name': u'Joey Bada$$'})
  >>>

Let’s see some validation

.. code-block:: python

  >>> person = Person(raises=False)
  >>> person.errors
  {'name': [u'This field is required.']}
  >>>

Installation
~~~~~~~~~~~~

This is currently an unstable, unofficial fork of Schematics. To install this
fork::

  $ pip install git+git@github.com:plain-vanilla-games/schematics.git#egg=schematics

Python 2.7 is supported. 2.6 support is close but test suite needs to be
updated.

Documentation
~~~~~~~~~~~~~

`schematics.readthedocs.org <https://schematics.readthedocs.org/en/latest/>`_

Tests
~~~~~

Using py.test::

  $ py.test tests/

Fork Authors
~~~~~~~~~~~~

+ `Jökull Sólberg Auðunsson <https://github.com/jokull>`_
+ `Jóhann Þorvaldur Bergþórsson <https://github.com/johannth>`_

We’re developers at `Plain Vanilla Games <http://plainvanilla.is/>`_.
