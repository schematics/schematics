# DictShield

Aside from being a cheeky excuse to make people say things that sound sorta 
dirty, DictShield is a database-agnostic modeling system. It provides a way to
model, validate and reshape data easily. All without requiring any particular
database.

A blog model might look like this:

    from dictshield.document import Document
    from dictshield.fields import StringField

    class BlogPost(Document):
        title = StringField(max_length=40)
        body = StringField(max_length=4096)

DictShield objects serialize to JSON by default. Store them in Memcached,
MongoDB, Riak, whatever you need.

Say we have some data coming in from an iPhone:

    json_data = request.post.get('data')
    data = json.loads(json_data)

Validating the data then looks like this: `Model(**data).validate()`.

Easy.


# The Design 

DictShield aims to provides helpers for a few types of common needs for 
modeling. It has been useful on the server-side so far, but I believe it could
also serve for building an RPC.

1. Creating Flexible Documents

2. Easy To Use With Databases Or Caches

3. A Type System

4. Validation Of Types

5. Input / Output Shaping

DictShield also allows for object hierarchy's to be mapped into 
dictionaries too. This is useful primarily to those who use DictShield 
to instantiate classes representing their data instead of just filtering
dictionaries through the class's static methods.


# Example Uses

There are a few ways to use DictShield.  A simple case is to create a class
structure that has typed fields.  DictShield offers multiple types in
`fields.py`, like an EmailField or DecimalField.


## Creating Flexible Documents

Below is an example of a Media class with a single field, the title.

    from dictshield.document import Document
    from dictshield.fields import StringField

    class Media(Document):
        """Simple document that has one StringField member
        """
        title = StringField(max_length=40)
    
You create the class just like you would any Python class. And we'll see 
how that class is represented as a Python dictionary.

    m = Media()
    m.title = 'Misc Media'
    print 'From Media class as Python structure:\n\n    %s\n' % (m.to_python())

The output from this looks like:

    {
        '_types': ['Media'],
        '_cls': 'Media',
        'title': u'Misc Media'
    }

All the meta information is removed and we have just a barebones representation
of our data. Notice that the class information is still there as `_cls` and 
`_types`.

### More On Object Modeling

We see two keys that come from Media's meta class: `_types` and `_cls`.
`_types` stores the hierachy of Document classes used to create the
document. `_cls` stores the specific class instance. This becomes more
obvious when I subclass Media to create the Movie document below.

    import datetime
    from dictshield.fields import IntField

    class Movie(Media):
        """Subclass of Foo. Adds bar and limits publicly shareable
        fields to only 'bar'.
        """
        _public_fields = ['title','year']
        year = IntField(min_value=1950, 
                        max_value=datetime.datetime.now().year)
        personal_thoughts = StringField(max_length=255)

Here's an instance of the Movie class:

    mv = Movie()
    mv.title = u'Total Recall'
    mv.year = 1990
    mv.personal_thoughts = u'I wish I had three hands...'

This is the raw document as converted to a Python dictionary:

    {
        'personal_thoughts': u'I wish I had three hands...', 
        '_types': ['Media', 'Media.Movie'], 
        'title': u'Total Recall', 
        '_cls': 'Media.Movie',
        'year': 1990
    }

Notice that `_types` has kept track of the relationship between `Movie` and
`Media`.

### Upgrading Documents

Upgrading documents is then easy because you can add optional fields and remove
them. 

As instances are created, two things happen. The fields that don't belong are 
removed as data is sent back and forth between the client and the server. And 
fields that are new are allowed at the data layer, assuming the user experience
layer will be catching up soon. Until then, the field can just be optional.


## Easy To Use With Databases Or Caches

We could pass this directly to Mongo to save it.

    >>> db.test_collection.save(m.to_python())

Or if we were using Riak.

    >>> media = bucket.new('test_key', data=m.to_python())
    >>> media.store()

Or maybe we're storing json in a memcached.

    >>> mc["test_key"] = m.to_json()


## A Type System

DictShield has its own type system - every field within a `Document` is defined with a specific type, for example a string will be defined as `StringField`. This "strong typing" makes serialising/deserialising semi-structured data to and from Python much more robust.

### All Types

A complete list of the types supported by DictShield:

| **TYPE**                | **DESCRIPTION**                                                           |
|------------------------:|:--------------------------------------------------------------------------|
|         **Text fields** |                                                                           |    
|           `StringField` | A unicode string                                                          |    
|              `URLField` | A valid URL                                                               |     
|            `EmailField` | A valid email address                                                     |
|           **ID fields** |                                                                           |    
|             `UUIDField` | A valid UUID value, optionally auto-populates empty values with new UUIDs |    
|         `ObjectIDField` | Wraps a MongoDB "BSON" ObjectId                                           |
|      **Numeric fields** |                                                                           |
|           `NumberField` | Any number (the parent of all the other numeric fields)                   |
|              `IntField` | An integer                                                                |
|             `LongField` | A long                                                                    |
|            `FloatField` | A float                                                                   |
|          `DecimalField` | A fixed-point decimal number                                              |
|      **Hashing fields** |                                                                           |
|              `MD5Field` | An MD5 hash                                                               |
|             `SHA1Field` | An SHA1 hash                                                              |
|      **'Native types'** |                                                                           |
|          `BooleanField` | A boolean                                                                 |
|         `DateTimeField` | A datetime                                                                |
|         `GeoPointField` | A geo-value of the form x, y (latitude, longitude)                        |
|          **Containers** |                                                                           | 
|             `ListField` | Wraps a standard field, so multiple instances of the field can be used    |
|       `SortedListField` | A ListField which sorts the list before saving, so list is always sorted  |
|             `DictField` | Wraps a standard Python dictionary                                        |
| `EmbeddedDocumentField` | Stores a DictShield EmbeddedDocument                                      |

### A Close Look at the MD5Field

This is what the MD5Field looks like. Notice that it's basically just
an implementation of a `validate()` function, which raises a `ShieldException`
exception if validation fails.

    class MD5Field(BaseField):
        """A field that validates input as resembling an MD5 hash.
        """
        hash_length = 32
        def validate(self, value):
            if len(value) != MD5Field.hash_length:
                raise ShieldException('MD5 value is wrong length',
                                      self.field_name, value)
            try:
                x = int(value, 16)
            except:
                raise ShieldException('MD5 value is not hex',
                                      self.field_name, value)

You might notice that the field which failed is also reported. It's available on
the exception as `field_name` and `field_value`.

The exception prints in this pattern `field_name(field_value): reason`.

    ShieldException caught: secret(whatevz):  MD5 value is wrong length

If you think the overhead of validation is unnecessary for some use cases, you 
can skip it by never calling `validate()`. 


## Validation Of Types

As we saw above, we know we can validate `Document` instances by calling
`validate()`. Let's generate a `User` instance with seed data and validate it.

First, here is the User model:

    class User(Document):
        _public_fields = ['name']
        secret = MD5Field()
        name = StringField(required=True, max_length=50)
        bio = StringField(max_length=100)
        url = URLField()

Next, we seed the instance with some data and validate it.
    
    user = User(**{'secret': 'whatevs', 'name': 'test hash'})
    try:
        user.validate()
    except ShieldException, se:
        print 'ShieldException caught: %s' % (se)

This calling `validate()` on a model validates an instance by looping through
it's fields and calling `field.validate()` on each one. 

We can still be leaner. DictShield also allows validating input without 
instantiating any objects.


### Validating User Input

Let's say we get this JSON string from a user.

    {"bio": "Python, Erlang and guitars!", "secret": "e8b5d682452313a6142c10b045a9a135", "name": "J2D2"}

We might write some server code that looks like this:

    json_string = request.get_arg('data')
    user_input = json.loads(json_string)
    user.validate(**user_input)

This method builds a User instance out of the input, which also throws away 
keys that aren't in the User definition.

We then call `validate()` on that `User` instance to validate each field against
what the dictionary contained. If the data doesn't pass exception, a
`ShieldException` is thrown and we handle the error. 

If validation passed, we're done. We know the data looks good.


## Input / Output shaping

Input is coming from everyone online, so who knows what it's in there. We do,
however, know exactly what fields we want to be there. Same goes for output.

A web system typically has tiers involved with data access, depending on the 
user logged in. My most common need is to differentiate between internal system
data (the raw document), data fields for the owner of the data (internal data
removed) and the data fields that are shareable with the general public.

### Removing Unknown Fields

Unrecognized fields, in user input, are thrown away. This makes handling input
fairly easy because you are generally working with a list of fields, what they
look like and how to turn them into Python or JSON. Not much else.

So here's how you can reduce the user input into just the fields found on a 
`User` document.

Consider the following string:

    {
        "rogue_field": "MWAHAHA", 
        "bio": "Python, Erlang and guitars!", 
        "secret": "e8b5d682452313a6142c10b045a9a135", 
        "name": "J2D2"
    }

Parse it just like before.

    user_doc = User(**total_input).to_python()

The values in total_input are matched against fields found in the DictShield
Document class and everything else is discarded.

`user_doc` now looks like below with `rogue_field` removed.

    {
        '_types': ['User'], 
        'bio': u'Python, Erlang and guitars!, 
        'secret': 'e8b5d682452313a6142c10b045a9a135', 
        'name': u'J2D2', 
        '_cls': 'User'
    }

### JSON for Owner of Document

Here is our `Movie` document safe for transmitting to the owner of the document.
We achieve this by calling `Movie.make_json_ownersafe`. This function is a 
classmethod available on the `Document` class. It knows to remove `_cls` and
`_types` because they are in `Document._internal_fields`. _You can  add any 
fields that should be treated as internal to your system by adding a list named
`_private_fields` to your Document and listing each field.

    {
        "personal_thoughts": "I wish I had three hands...",
        "title": "Total Recall",
        "year": 1990
    }
   
### JSON for Public View of Document

This is  dictionary safe for transmitting to the public, not just the owner.
Get this by calling `make_json_publicsafe`.

    {
        "title": "Total Recall",
        "year": 1990
    }


## Working Without Instances

Consider a user updating some of their settings. Rather than validate the entire
document, you want to check validation for just the field the client is 
updating and tell your database to store just that field.

DictShield offers a few classmethods to facilitate this.

### Class Level Validation

`validate_class_fields` gives us that by checking if some dictionary matches
the pattern it needs, including required fields. Notice, it's also a 
classmethod. No need to instantiate anything.

    user_input = {
        'url': 'http://j2labs.tumblr.com'
    }

    try:
        User.validate_class_fields(user_input)
    except ShieldException, se:
        print('  Validation failure: %s\n' % (dp))

This particular code would throw an exception because the `name` field is 
required, but not present.

`validation_class_partial` lets you validate only the fields present in the
input. This is useful for updating one or two fields in a document at a time, 
like we attempted above.

    ...
        User.validate_class_partial(user_input)
    ...

### Aggregating Errors

`validate_class_fields` also offers more full validation. Pass 
`validate_all=True` to return 0 or more exceptions. 0 exceptions indicates
validation was successful.

    exceptions = User.validate_class_fields(total_input, validate_all=True)


# Installing

DictShield is in [pypi](http://pypi.python.org) so you can use `easy_install` or `pip`.

    pip install dictshield


# Contributors

* [James Dennis](https://github.com/j2labs)
* [Andrew Gwozdziewycz](https://github.com/apgwoz)
* [Dion Paragas](https://github.com/d1on)
* [Tom Waits](https://github.com/tomwaits)
* [Chris McCulloh](https://github.com/st0w)
* [Sean O'Connor](https://github.com/SeanOC)


# License

BSD!

