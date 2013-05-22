Schematics
==========

**Python Data Structures for Humans™.**

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
  >>> person.name
  u'Joey Bada$$'

Let’s see some validation

.. code-block:: python

  >>> person = Person()
  >>> try:
  ...     person.validate()
  ... except ValidationError, e:
  ...     print e.messages
  {'name': [u'This field is required.']}

Installation
~~~~~~~~~~~~

  $ pip install schematics

Python 2.7 is supported. 2.6 support is close but test suite needs to be
updated.

Documentation
~~~~~~~~~~~~~

`schematics.readthedocs.org <https://schematics.readthedocs.org/en/latest/>`_

Tests
~~~~~

Using py.test::

  $ py.test tests/

Authors
~~~~~~~~~~~~

+ `James Dennis <https://github.com/j2labs>`_
+ `Jökull Sólberg Auðunsson <https://github.com/jokull>`_
+ `Jóhann Þorvaldur Bergþórsson <https://github.com/johannth>`_
+ `James Dennis <https://github.com/j2labs>`_
+ `Andrew Gwozdziewycz <https://github.com/apgwoz>`_
+ `Dion Paragas <https://github.com/d1on>`_
+ `Tom Waits <https://github.com/tomwaits>`_
+ `Chris McCulloh <https://github.com/st0w>`_
+ `Sean O'Connor <https://github.com/SeanOC>`_
+ `Alexander Dean <https://github.com/alexanderdean>`_
+ `Rob Spychala <https://github.com/robspychala>`_
+ `Ben Beecher <https://github.com/gone>`_
+ `John Krauss <https://github.com/talos>`_
+ `Titusz <https://github.com/titusz>`_
+ `Nicola Iarocci <https://github.com/nicolaiarocci>`_
+ `Justin Lilly <http://github.com/justinlilly>`_
+ `Jonathan Halcrow <https://github.com/jhalcrow>`_

