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


More Information
================

To learn more about **Importing**, visit the :ref:`Transforms API <api_doc_transforms>`
