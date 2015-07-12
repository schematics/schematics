=========
Importing
=========

The general mechanism for data import is to call a function on every field in
the data and coerce it into the most appropriate representation in Python. A
date string, for example, would be converted to a ``datetime.datetime``.

Perhaps we're writing a web API that receives song data.  Let's model the song.

::

  class Song(Model):
      name = StringType()
      artist = StringType()
      url = URLType()

This is what successful validation of the data looks like.

::

  >>> song_json = '{"url": "http://www.youtube.com/watch?v=67KGSJVkix0", "name": "Werewolf", "artist": "Fiona Apple"}'
  >>> fiona_song = Song(json.loads(song_json))
  >>> fiona_song.url
  u'http://www.youtube.com/watch?v=67KGSJVkix0'


Compound Types
==============

We could define a simple collection of songs like this:

::

  class Collection(Model):
      songs = ListType(ModelType(Song))

Some JSON data for this type of a model might look like this:

::

  >>> songs_json = '{"songs": [{"url": "https://www.youtube.com/watch?v=UeBFEanVsp4", "name": "When I Lost My Bet", "artist": "Dillinger Escape Plan"}, {"url": "http://www.youtube.com/watch?v=67KGSJVkix0", "name": "Werewolf", "artist": "Fiona Apple"}]}'

The collection has a list of models for songs, so when we import that list, that
data should be converted to model instances.

::

  >>> song_collection = Collection(json.loads(songs_json))
  >>> song_collection.songs[0]
  <Song: Song object>
  >>> song_collection.songs[0].artist
  u'Dillinger Escape Plan'


On strictness
=============

When we're creating model instances from external data, we usually
want to ensure that there are no extra, unexpected fields. Schematics
calls these "rogue fields". By default, models raise a
``ModelConversionError`` whenever rogue fields are present:

::

  class Inner(Model):
      expected_key = StringType()

  class Outer(Model):
      inner = ModelType(Outer)

  doc = {
      'inner': {
          'expected_key': 'expected value',
          'rogue_key': 'unexpected value',
      },
  }

  >>> Inner(doc['inner'])
  [...]
  schematics.exceptions.ModelConversionError: {'rogue_key': 'Rogue field'}

We can modify that behavior by passing in a ``strict`` keyword argument:

::

  >>> Inner(doc['inner'], strict=False)
  <Inner: Inner object>

This also applies to models that contain other models:

::

  >>> Outer(doc)
  [...]
  schematics.exceptions.ModelConversionError: {'inner': {'rogue_key': 'Rogue field'}}

  >>> Outer(doc, strict=False)
  <Outer: Outer object>

This is useful in lots of scenarios:

- We've created a new API version that accepts new fields, but want to
  maintain forward compatibility on the old API.
- We have one customer who just can't make their enterprise document
  system quit embedding extra metadata fields.
- We want to use existing models pluck a few fields out of a large
  document, but don't want to rewrite those tested, working models to
  handle our one-time project.

The default value for ``strict`` is ``None``, which means "don't
override the model's own configuration".

More Information
~~~~~~~~~~~~~~~~

To learn more about **Importing**, visit the :ref:`Transforms API <api_doc_transforms>`
