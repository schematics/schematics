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

Maybe we need to load some data from a database and send it to a user quickly.
That code might look like this:

    data = database.load_data()
    scrubbed = Model.make_json_publicsafe(data)
    send_to_user(scrubbed)

Easy.


# The Design 

DictShield aims to provides helpers for a few types of common needs for 
modeling. It has been useful on the server-side so far, but I believe it could
also serve for building an RPC.

1. Transform some string of input into a Python dictionary.

2. Validate keys as being certain types

3. Remove keys we're not interested in.

4. Provide helpers to remove keys in the Python representation before
   the data is sent to a user. 

5. Provide helpers for reshaping dictionaries depending on the intended
   consumer (eg. owner or random person).

DictShield also allows for object hierarchy's to mapped into 
dictionaries too. This is useful primarily to those who use DictShield 
to instantiate classes representing their data instead of just filtering
dictionaries through the class's static methods.


# Example Uses

There are a few ways to use DictShield. A simple case is to create a class
structure that has typed fields. DictShield offers multiple types in
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


## Saving To A Database

We could pass this directly to Mongo to save it.

    >>> db.test_collection.save(m.to_python())

Or if we were using Riak.

    >>> media = bucket.new('test_key', data=m.to_python())
    >>> media.store()


## More Object Modeling

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

Noticed we've added a `_public_fields` member to our document. This list 
is used to store which fields are safe for transmitting to someone who 
doesn't own this particular document. `personal_thoughts`  is not in that list,
for example.

Here's an instance of the Movie class:

    mv = Movie()
    mv.title = u'Total Recall'
    mv.year = 1990
    mv.personal_thoughts = u'I wish I had three hands...'

Next, we'll see what happens when we print this document in different forms.
Perhaps you're wondering what I mean?

A web system typically has tiers involved with data access, depending on the 
user logged in. My most common need is to differentiate between internal system
data (the raw document), data fields for the owner of the data (internal data
removed) and the data fields that are shareable with the general public.

This is the raw document as converted to a Python dictionary:

    {
        'personal_thoughts': u'I wish I had three hands...', 
        '_types': ['Media', 'Media.Movie'], 
        'title': u'Total Recall', 
        '_cls': 'Media.Movie',
        'year': 1990
    }


## JSON for Owner of Document

Here is a document safe for transmitting to the owner of the document. We
achieve this by calling `Movie.make_json_ownersafe`. This function is a 
classmethod available on the `Document` class. It knows to remove `_cls`
and `_types` because they are in `Document._internal_fields`. _You can 
add any fields that should be treated as internal to your system by 
adding a list named `_private_fields` to your Document and listing each
field.
   
    {
        'personal_thoughts': u'I wish I had three hands...',
        'title': u'Total Recall',
        'year': 1990
    }
   
## JSON for Public View of Document

This is  dictionary safe for transmitting to the public, not just the owner.
Get this by calling `make_json_publicsafe`.

    {
        'title': u'Total Recall',
        'year': 1990
    }


## Validation

As we saw above, we know we can validate `Document` instances by calling
`validate()`. Let's generate a `User` instance with seed data and validate it.

First, here is the User model:

    class User(Document):
        _public_fields = ['name']
        secret = MD5Field()
        name = StringField(required=True, max_length=50)
        bio = StringField(max_length=100)
        url = URLField()

Next, we seed the instance with data validate it.
    
    user = User(**{'secret': 'whatevs', 'name': 'test hash'})
    try:
        user.validate()
    except DictPunch, dp:
        print 'DictPunch caught: %s' % (dp))

This model validates an instance by looping through it's fields and calling
`field.validate()` on each one. 

We can still be leaner. DictShield also allows validating input without 
instantiating any objects.


## Validating Document instances

Remember the `User` class we defined earlier?

    class User(Document):
        _public_fields = ['name']
        secret = MD5Field()
        name = StringField(required=True, max_length=50)
        bio = StringField(max_length=100)
        url = URLField()

Let's say we get this dictionary from a user

    user_input = {
        'secret': 'e8b5d682452313a6142c10b045a9a135',
        'name': 'J2D2',
        'bio': 'J2D2 loves music',
        'rogue_field': 'MWAHAHA',
    }

Let's validate the dictionary. 

    u = User(**user_input)
    try:
        u.validate()
    except DictPunch, dp:
        print 'DictPunch caught: %s' % (dp))

This method required a User instance.


### Validating a Subset

Consider a user updating some of their settings. Rather than validate the entire
document, you want to check validation for just the field the client is 
updating.

`validate_class_fields` gives us that by checking if some dictionary matches
the pattern it needs, including required fields. Notice, it's also a 
classmethod. No need to instantiate anything.

    user_input = {
        'url': 'http://j2labs.tumblr.com'
    }

    try:
        User.validate_class_fields(user_input)
    except DictPunch, dp:
        print('  Validation failure: %s\n' % (dp))

This particular code would throw an exception because the `name` field is 
required, but not present.

`validation_class_partial` lets you validate only the fields present in the
input. This is useful for updating one or two fields in a document at a time, 
like we attempted above.

    ...
        User.validate_class_partial(user_input)
    ...


### Aggregating errors

`validate_class_fields` also offers more full validation. Pass 
`validate_all=True` to return 0 or more exceptions. 0 exceptions indicates
validation was successful.

    exceptions = User.validate_class_fields(total_input, validate_all=True)


### Types Through Validation

This is what the MD5Field looks like. Notice that it's basically just
an implementation of a `validate()` function, which raises a `DictPunch`
exception if validation fails.

    class MD5Field(BaseField):
        """A field that validates input as resembling an MD5 hash.
        """
        hash_length = 32
        def validate(self, value):
            if len(value) != MD5Field.hash_length:
                raise DictPunch('MD5 value is wrong length',
                                self.field_name, value)
            try:
                x = int(value, 16)
            except:
                raise DictPunch('MD5 value is not hex',
                                self.field_name, value)

You might notice that the field which failed is also reported. It's available on
the exception as `field_name` and `field_value`. The reason is simply `reason`.

The exception prints in this pattern: `field_name(field_value): reason`

    DictPunch caught: secret(whatevz):  MD5 value is wrong length


### Removing Unknown Fields

Once validation has passed, we can pass the dictionary into our User class,
to map dictionary keys to field names, and call `to_python()` to get a Python
dictionary mapped to the design of the User class.

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


# Installing

DictShield is in [pypi](http://pypi.python.org) so you can use `easy_install` or `pip`.

    pip install dictshield


# License

BSD!

