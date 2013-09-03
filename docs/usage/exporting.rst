=========
Exporting
=========


Native Types
============


Primitive Types
===============

To present data to clients we have the ``Model.to_primitive`` method. Default
behavior is to output the same data you would need to reproduce the model in its
current state.

.. doctest::

  >>> from schematics.models import Model
  >>> from schematics.types import StringType
  >>> from schematics.serialize import whitelist
  >>>
  >>> class Movie(Model):
  ...     name = StringType()
  ...     director = StringType()
  ...     class Options:
  ...         roles = {'public': whitelist('name')}
  ...
  >>> movie = Movie()
  >>> movie.name = u'Trainspotting'
  >>> movie.director = u'Danny Boyle'
  >>> movie.to_primitive()
  {'director': u'Danny Boyle', 'name': u'Trainspotting'}

Great. We got the primitive data back. Date types would have been cast back and
forth etc.


Roles
=====

What if we wanted to expose this to untrusted parties who mustn’t know the
director?

.. doctest::

  >>> movie.to_primitive(role='public')
  {'name': u'Trainspotting'}

A role can be used to filter data during serialization.  Blacklists and whitelists are available

