# DictShield

Aside from being a cheeky excuse to make people say things that sound 
sorta dirty, DictShield is a fast way to validate and trim the values
in a dictionary. This is most useful to people building server-side
API's that can't necessarily trust their inputs.

It is designed with MongoDB in mind but could be easily adapted to work
with other storage systems.

# The Design 

DictShield specifically aims to provides helpers for a few types of 
common needs for server-side API designers.

1. Transform some string of input into a Python dictionary.

2. Validate keys as being certain types

3. Remove keys we're not interested in.

4. Provide helpers to remove keys in Mongo's representation before
   the data is sent to a user. 

5. Provide helpers for reshaping dictionaries depending on the intended
   consumer (eg. owner or random person).

DictShield also allows for object hierarchy's to mapped into 
dictionaries too. This is useful primarily to those who use DictShield 
to instantiate classes representing their data instead of just filtering
dictionaries through the class's static methods.

# Examples

There are a few ways to use DictShield. To introduce the concept, I'll
show how Document classes can be instantiated and then converted to

1. An object fit for mongo to store
2. A dictionary safe for transmitting to the owner of the document
3. A dictionary safe for transmitting to anyone on the site

## Object Creation

This code is taken from dictshield/examples/creating_objects.py

Below is an example of a Media class holding one member.

    from dictshield.document import Document
    from dictshield.fields import StringField
    class Media(Document):
        """Simple document that has one StringField member
        """
        title = StringField(max_length=40)
    
You create the class just like you would any Python class. And we'll see 
how that class is represented in Mongo.

    m = Media()
    m.title = 'Misc Media'
    print 'From Media class to mongo structure:\n\n    %s\n' % (m.to_mongo())

The output from this looks like:

    {
        '_types': ['Media'],
        '_cls': 'Media',
        'title': u'Misc Media'
    }

We see two keys that come from Media's meta class: \_types and \_cls.
\_types stores the hierachy of Document classes used to create the
document. \_cls stores the specific class instance. This becomes more
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

If you feel these fields are too much overhead, you can turn them
off by adding a dictionary called `meta` to the Movie class with
the key `allow_inheritance` set to False.
    
Noticed we've added a `_public_fields` member to our document. This list 
is used to store which fields are safe for transmitting to someone who 
doesn't own this particular document. You'll notice `personal_thoughts` 
is not in that list.

Here's an instance of the Movie class:

    mv = Movie()
    mv.title = u'Total Recall'
    mv.year = 1990
    mv.personal_thoughts = u'I wish I had three hands...'

Next, we'll see what happens when we print this document in different forms.
Perhaps you're wondering what I mean?

A web system typically has tiers involved with data access, depending on 
the user logged in. My most common need is to differentiate between internal 
system data (the raw document), data fields for the owner of the data 
(internal data removed) and the data fields that are shareable with the 
general public.

This is the raw document as stored in Mongo:

    {
        'personal_thoughts': u'I wish I had three hands...', 
        '_types': ['Media', 'Media.Movie'], 
        'title': u'Total Recall', 
        '_cls': 'Media.Movie',
        'year': 1990
    }

Here is a document safe for transmitting to the owner of the document. We
achieve this by calling `Movie.make_json_ownersafe`. This function is a 
classmethod available on the `Document` class. It knows to remove \_cls
and \_types because they are in `Document._internal_fields`. _You can 
add any fields that should be treated as internal to your system by 
adding a list named `_private_fields` to your Document and listing each
field_.
   
    {
        'personal_thoughts': u'I wish I had three hands...',
        'title': u'Total Recall',
        'year': 1990
    }
   
A dictionary safe for transmitting to the public, not just the owner. 
We achieve this by calling `make_json_publicsafe`.

    {
        'title': u'Total Recall',
        'year': 1990
    }

## Validation

This code is taken from dictshield/examples/validation.py

For the first example, we'll instantiate a User instance and then fill
in some fields to focus simply on validation.

Here is an example of a User document.

    from dictshield.document import Document
    from dictshield.fields import MD5Field
    from dictshield.fields import StringField
    class User(Document):
        _public_fields = ['name']
        secret = MD5Field()
        name = StringField(required=True, max_length=50)
        bio = StringField(max_length=100)
    
We'll populate a User instance with a bogus looking secret.

    u = User()
    u.secret = 'whatevz'
    u.name = 'test hash'
    
Now, we'll validate this. Failed validation throws `DictPunch` 
exceptions, so we'll protect against that in our code.

    print 'Attempting first validation...'
    try:
        u.validate()
    except DictPunch, dp:
        print 'DictPunch caught: %s' % (dp))

You might notice that the field which failed is also (new) reported. 
It's available on the exception as `field_name` and `field_value`. The
reason is stored as `reason`.

The exception prints in this pattern: field_name(field_value): reason

    DictPunch caught: secret(whatevz):  MD5 value is wrong length

Anyway, in this particular case an MD5 was expected, but we had the
string 'whatevz', which is not an MD5. 

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
    
Back to validation...

It's possible we don't want to instantiate a bunch of objects just to
validate some fields, so let's see what it looks like to use a more
typical process: go from python dictionary into a validated mongo bson
structure via a DictShield Document definition.

Remember the `User` class we defined earlier?

    class User(Document):
        _public_fields = ['name']
        secret = MD5Field()
        name = StringField(required=True, max_length=50)
        bio = StringField(max_length=100)

Here is a dictionary we'll use to seed the document. Notice the key 
names are the same as the field named in the document.

    total_input = {
        'secret': 'e8b5d682452313a6142c10b045a9a135',
        'name': 'J2D2',
        'bio': 'J2D2 loves music',
        'rogue_field': 'MWAHAHA',
    }

Let's validate the dictionary. This only checks if the fields in the 
`User` class have valid entries in the dictionary. This also makes
sure that any required fields are present and validated.
    
    try:
        User.validate_class_fields(total_input)
    except DictPunch, dp:
        print('  DictPunch caught: %s\n' % (dp))

This is the first time we've seen `validate_class_fields(...)`. This
is a classmethod which throws a DictPunch when validation on any field
fails. 

The keyword `validate_all` is available if you'd prefer to
check every field and get a list of DictPunch's, if found, as 
a return value.

    exceptions = User.validate_class_fields(total_input, validate_all=True)

Once validation has passed, we can pass the dictionary into our User class,
to map dictionary keys to field names, and call `to_mongo()` to get a mongo
safe dictionary mapped to the design of the User class.

    user_doc = User(**total_input).to_mongo()

The values in total_input are matched against fields found in the
DictShield Document class and anything else is discarded.

`user_doc` now looks like below with `rogue_field` removed.

    {
        '_types': ['User'], 
        'bio': u'J2D2 loves music', 
        'secret': 'e8b5d682452313a6142c10b045a9a135', 
        'name': u'J2D2', 
        '_cls': 'User'
    }
