.. _exporting:

=========
Exporting
=========

To export data is to go from the Schematics representation of data to some
other form.  It's also possible you want to adjust some things along the way,
such as skipping over some fields or providing empty values for missing fields.

The general mechanism for data export is to call a function on every field in
the model.  The function probably converts the field's value to some other
format, but you can easily modify it.

We'll use the following model for the examples:

::

  from schematics.models import Model
  from schematics.types import StringType, DateTimeType
  from schematics.transforms import blacklist
  
  class Movie(Model):
      name = StringType()
      director = StringType()
      release_date = DateTimeType
      personal_thoughts = StringType()
      class Options:
          roles = {'public': blacklist('personal_thoughts')}


.. _exporting_terminology:

Terminology
===========

To `serialize` data is to convert from the way it's represented in Schematics
to some other form.  That might be a reduction of the ``Model`` into a
``dict``, but it might also be more complicated.

A field can be serialized if it is an instance of ``BaseType`` or if a function
is wrapped with the ``@serializable`` decorator.

A ``Model`` instance may be serialized with a particular `context`. A context
is a ``dict`` passed through the model to each of its fields. A field may use
values from the context to alter how it is serialized.

.. _exporting_converting_data:

Converting Data
===============

To export data is basically to convert from one form to another.  Schematics
can convert data into simple Python types or a language agnostic format.  We
refer to the native serialization as `to_native`, but we refer to the language
agnostic format as `primitive`, since it has removed all dependencies on
Python.


.. _exporting_native_types:

Native Types
------------

The fields in a model attempt to use the best Python representation of data
whenever possible.  For example, the DateTimeType will use Python's
``datetime.datetime`` module.

You can reduce a model into the native Python types by calling ``to_native``.

  >>> trainspotting = Movie()
  >>> trainspotting.name = u'Trainspotting'
  >>> trainspotting.director = u'Danny Boyle'
  >>> trainspotting.release_date = datetime.datetime(1996, 7, 19, 0, 0)
  >>> trainspotting.personal_thoughts = 'This movie was great!'
  >>> trainspotting.to_native()
  {
    'name': u'Trainspotting', 
    'director': u'Danny Boyle', 
    'release_date': datetime.datetime(1996, 7, 19, 0, 0), 
    'personal_thoughts': 'This movie was great!'
  }


.. _exporting_primitive_types:

Primitive Types
---------------

To present data to clients we have the ``Model.to_primitive`` method. Default
behavior is to output the same data you would need to reproduce the model in its
current state.

::

  >>> trainspotting.to_primitive()
  {
    'name': u'Trainspotting',
    'director': u'Danny Boyle', 
    'release_date': '1996-07-19T00:00:00.000000', 
    'personal_thoughts': 'This movie was great!'
  }

Great.  We got the primitive data back.  It would be easy to convert to JSON
from here.

  >>> import json
  >>> json.dumps(trainspotting.to_primitive())
  '{
     "name": "Trainspotting", 
     "director": "Danny Boyle", 
     "release_date": "1996-07-19T00:00:00.000000", 
     "personal_thoughts": "This movie was great!"
   }'

.. _exporting_using_contexts:

Using Contexts
--------------

Sometimes a field needs information about its environment to know how to
serialize itself. For example, the ``MultilingualStringType`` holds several
translations of a phrase:

  >>> class TestModel(Model):
  ...     mls = MultilingualStringType()
  ...
  >>> mls_test = TestModel({'mls': {
  ...     'en_US': 'Hello, world!',
  ...     'fr_FR': 'Bonjour tout le monde!',
  ...     'es_MX': '¡Hola, mundo!',
  ... }})

In this case, serializing without knowing which localized string to use
wouldn't make sense:

  >>> mls_test.to_primitive()
  [...]
  schematics.exceptions.ConversionError: [u'No default or explicit locales were given.']

Neither does choosing the locale ahead of time, because the same
MultilingualStringType field might be serialized several times with different
locales inside the same method.

However, it could use information in a `context` to return a useful
representation:

  >>> mls_test.to_primitive(context={'locale': 'en_US'})
  {'mls': 'Hello, world!'}

This allows us to use the same model instance several times with different
contexts:


  >>> for user, locale in [('Joe', 'en_US'), ('Sue', 'es_MX')]:
  ...     print '%s says %s' % (user, mls_test.to_primitive(context={'locale': locale})['mls'])
  ...
  Joe says Hello, world!
  Sue says ¡Hola, mundo!

.. _exporting_compound_types:

Compound Types
==============

Let's complicate things and observe what happens with data exporting.  First,
we'll define a collection which will have a list of ``Movie`` instances.

First, let's instantiate another movie.

::

  >>> total_recall = Movie()
  >>> total_recall.name = u'Total Recall'
  >>> total_recall.director = u'Paul Verhoeven'
  >>> total_recall.release_date = datetime.datetime(1990, 6, 1, 0, 0)
  >>> total_recall.personal_thoughts = 'Old classic.  Still love it.'

Now, let's define a collection, which has a list of movies in it.

::

  from schematics.types.compound import ListType, ModelType

  class Collection(Model):
      name = StringType()
      movies = ListType(ModelType(Movie))
      notes = StringType()
      class Options:
          roles = {'public': blacklist('notes')}

Let's instantiate a collection.

  >>> favorites = Collection()
  >>> favorites.name = 'My favorites'
  >>> favorites.notes = 'These are some of my favorite movies'
  >>> favorites.movies = [trainspotting, total_recall]

Here is what happens when we call ``to_primitive()`` on it.

  >>> favorites.to_primitive()
  {
      'notes': 'These are some of my favorite movies', 
      'name': 'My favorites',
      'movies': [{
          'name': u'Trainspotting',
          'director': u'Danny Boyle', 
          'personal_thoughts': 'This movie was great!', 
          'release_date': '1996-07-19T00:00:00.000000'
      }, {
          'name': u'Total Recall',
          'director': u'Paul Verhoeven', 
          'personal_thoughts': 'Old classic.  Still love it.', 
          'release_date': '1990-06-01T00:00:00.000000'
      }]
  }
  

.. _exporting_customizing_output:

Customizing Output
==================

Schematics offers many ways to customize the behavior of serialization:


.. _exporting_roles:

Roles
-----

Roles offer a way to specify whether or not a field should be skipped during
export.  There are many reasons this might be desirable, such as access
permissions or to not serialize more data than absolutely necessary.

Roles are implemented as either white lists or black lists where the members of
the list are field names.

::

  >>> r = blacklist('private_field', 'another_private_field')

Imagine we are sending our movie instance to a random person on the Internet.
We probably don't want to share our personal thoughts.  Recall earlier that we
added a role called ``public`` and gave it a blacklist with
``personal_thoughts`` listed.

::

  class Movie(Model):
      personal_thoughts = StringType()
      ...
      class Options:
          roles = {'public': blacklist('personal_thoughts')}

This is what it looks like to use the role, which should simply remove
``personal_thoughts`` from the export.

::

  >>> movie.to_primitive(role='public')
  {
      'name': u'Trainspotting', 
      'director': u'Danny Boyle', 
      'release_date': '1996-07-19T00:00:00.000000'
  }

This works for compound types too, such as the list of movies in our
``Collection`` model above.

::

  class Collection(Model):
      notes = StringType()
      ...
      class Options:
          roles = {'public': blacklist('notes')}

We expect the ``personal_thoughts`` field to removed from the movie data and we
also expect the ``notes`` field to be removed from the collection data.

  >>> favorites.to_primitive(role='public')
  {
      'name': 'My favorites',
      'movies': [{
          'name': u'Trainspotting',
          'director': u'Danny Boyle', 
          'release_date': '1996-07-19T00:00:00.000000'
      }, {
          'name': u'Total Recall',
          'director': u'Paul Verhoeven', 
          'release_date': '1990-06-01T00:00:00.000000'
      }]
  }

If no role is specified, the default behavior is to export all fields.  This
behavior can be overridden by specifying a ``default`` role.  Renaming
the ``public`` role to ``default`` in the example above yields equivalent
results without having to specify ``role`` in the export function.

  >>> favorites.to_primitive()
  {
      'name': 'My favorites',
      'movies': [{
          'name': u'Trainspotting',
          'director': u'Danny Boyle',
          'release_date': '1996-07-19T00:00:00.000000'
      }, {
          'name': u'Total Recall',
          'director': u'Paul Verhoeven',
          'release_date': '1990-06-01T00:00:00.000000'
      }]
  }



.. _exporting_serializable:

Serializable
------------

Earlier we mentioned a ``@serializable`` decorator.  You can write a function
that will produce a value used during serialization with a field name matching
the function name.

That looks like this:

::

  ...
  from schematics.types.serializable import serializable
  
  class Song(Model):
      name = StringType()
      artist = StringType()
      url = URLType()

      @serializable
      def id(self):
          return u'%s/%s' % (self.artist, self.name)

This is what it looks like to use it.  

::

  >>> song = Song()
  >>> song.artist = 'Fiona Apple'
  >>> song.name = 'Werewolf'
  >>> song.url = 'http://www.youtube.com/watch?v=67KGSJVkix0'
  >>> song.id
  'Fiona Apple/Werewolf'

Or here:

::

  >>> song.to_native()
  {
      'id': u'Fiona Apple/Werewolf', 
      'artist': u'Fiona Apple'
      'name': u'Werewolf',
      'url': u'http://www.youtube.com/watch?v=67KGSJVkix0', 
  }


.. _exporting_serialized_name:

Serialized Name
---------------

There are times when you have one name for a field in one place and another
name for it somewhere else.  Schematics tries to help you by letting you
customize the field names used during serialization.

That looks like this:

::

  class Person(Model):
      name = StringType(serialized_name='person_name')

Notice the effect it has on serialization.

::

  >>> p = Person()
  >>> p.name = 'Ben Weinman'
  >>> p.to_native()
  {'person_name': u'Ben Weinman'}


.. _exporting_serialize_when_none:

Serialize When None
-------------------

If a value is not required and doesn't have a value, it will serialize with a
None value by default.  This can be disabled.

::

  >>> song = Song()
  >>> song.to_native()
  {'url': None, 'name': None, 'artist': None}

You can disable at the field level like this:

::

  class Song(Model):
      name = StringType(serialize_when_none=False)
      artist = StringType()

And this produces the following:

::

  >>> s = Song()
  >>> s.to_native()
  {'artist': None}

Or you can disable it at the class level:

::

  class Song(Model):
      name = StringType()
      artist = StringType()
      class Options:
          serialize_when_none=False
  
Using it:

::

  >>> s = Song()
  >>> s.to_native()
  >>> 



More Information
================

To learn more about **Exporting**, visit the :ref:`Transforms API <api_doc_transforms>`
