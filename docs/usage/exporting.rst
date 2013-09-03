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

.. code:: python

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
  

Native Types
============

The fields in a model attempt to use the best Python representation of data
whenever possible.  For example, the DateTimeType will use Python's
``datetime.datetime`` module.

You can reduce a model into the native Python types by calling ``to_native``.

  >>> trainspotting = Trainspotting()
  >>> trainspotting.name = u'Trainspotting'
  >>> trainspotting.director = u'Danny Boyle'
  >>> trainspotting.release_date = datetime.datetime(1996, 7, 19, 0, 0)
  >>> trainspotting.personal_thoughts = 'This movie was great!'
  >>> trainspotting.to_native()
  {'name': u'Trainspotting', 'director': u'Danny Boyle', 'release_date': datetime.datetime(1996, 7, 19, 0, 0), 'personal_thoughts': 'This movie was great!'}


Primitive Types
===============

To present data to clients we have the ``Model.to_primitive`` method. Default
behavior is to output the same data you would need to reproduce the model in its
current state.

.. code:: python

  >>> trainspotting.to_primitive()
  {'name': u'Trainspotting', 'director': u'Danny Boyle', 'release_date': '1996-07-19T00:00:00.000000', 'personal_thoughts': 'This movie was great!'}

Great.  We got the primitive data back.  It would be easy to convert to JSON
from here.

  >>> import json
  >>> json.dumps(trainspotting.to_primitive())
  '{"name": "Trainspotting", "director": "Danny Boyle", "release_date": "1996-07-19T00:00:00.000000", "personal_thoughts": "This movie was great!"}'


Compound Types
==============

Let's complicate things and observe what happens with data exporting.  First,
we'll define a collection which will have a list of ``Movie`` instances.

First, let's instantiate another movie.

.. code:: python

  >>> total_recall = Movie()
  >>> total_recall.name = u'Total Recall'
  >>> total_recall.director = u'Paul Verhoeven'
  >>> total_recall.release_date = datetime.datetime(1990, 6, 1, 0, 0)
  >>> total_recall.personal_thoughts = 'Old classic.  Still love it.'

Now, let's define a collection, which has a list of movies in it.

.. code:: python

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
  {'movies': [{'director': u'Danny Boyle', 'personal_thoughts': 'This movie was great!', 'release_date': '1996-07-19T00:00:00.000000', 'name': u'Trainspotting'}, {'director': u'Paul Verhoeven', 'personal_thoughts': 'Old classic.  Still love it.', 'release_date': '1990-06-01T00:00:00.000000', 'name': u'Total Recall'}], 'notes': 'These are some of my favorite movies', 'name': 'My favorites'}
  

Roles
=====

Roles offer a way to specify whether or not a field should be skipped during
export.  There are many reasons this might be desirable, such as access
permissions or to not serialize more data than absolutely necessary.

Imagine we are sending our movie instance to a random person on the Internet.
We probably don't want to share our personal thoughts.

Recall earlier that we added a role called ``public`` and gave it a blacklist
with ``personal_thoughts`` listed.

.. code:: python

  class Movie(Model):
      ...
      class Options:
          roles = {'public': blacklist('personal_thoughts')}

This is what it looks like to use the role, which should simply remove
``personal_thoughts`` from the export.

.. code:: python

  >>> movie.to_primitive(role='public')
  {'name': u'Trainspotting', 'director': u'Danny Boyle', 'release_date': '1996-07-19T00:00:00.000000'}

This works for compound types too, such as the list of movies in our
``Collection`` model above.

.. code:: python

  class Collection(Model):
      ...
      class Options:
          roles = {'public': blacklist('notes')}

We expect the ``personal_thoughts`` field to removed from the movie data and we
also expect the ``notes`` field to be removed from the collection data.

  >>> favorites.to_primitive(role='public')
  {'movies': [{'director': u'Danny Boyle', 'release_date': '1996-07-19T00:00:00.000000', 'name': u'Trainspotting'}, {'director': u'Paul Verhoeven', 'release_date': '1990-06-01T00:00:00.000000', 'name': u'Total Recall'}], 'name': 'My favorites'}

