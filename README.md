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

    class Media(Document):
        """Simple document that has one StringField member
        """
        title = StringField(max_length=40)
    
You create the class just like you would any Python class

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

    class Movie(Media):
        """Subclass of Foo. Adds bar and limits publicly shareable
        fields to only 'bar'.
        """
        _public_fields = ['title','year']
        year = IntField(min_value=1950, 
                        max_value=datetime.datetime.now().year)
        personal_thoughts = StringField(max_length=255)
    
We've added a `_public_fields` member to our document. This list is used
to store which fields are safe for transmitting to someone who doesn't
own this particular document. You'll notice `personal_thoughts` is not
in that list.

Let's see what happens when we print this document as:

1. An object fit for mongo to store

    {
        'personal_thoughts': u'I wish I had three hands...', 
        '_types': ['Media', 'Media.Movie'], 
        'title': u'Total Recall', 
        '_cls': 'Media.Movie',
        'year': 1990
    }

2. A dictionary safe for transmitting to the owner of the document. We
   achieve this by calling `make_json_safe`. This function is a 
   classmethod available on the `Document` class. This function knows to
   remove \_cls and \_types because they are in 
   `Document._internal_fields`. _You can add any fields that should be
   treated as internal to your system by adding a list named 
   `_private_fields` to your Document and listing each field_.
   
    {
        'personal_thoughts': u'I wish I had three hands...',
        'title': u'Total Recall',
        'year': 1990
    }
   
3. A dictionary safe for transmitting to anyone on the site. We achieve
   this by calling `make_json_publicsafe`.

    {
        'title': u'Total Recall',
        'year': 1990
    }

## Validation

This code is taken from dictshield/examples/validation.py

For the first example, we'll instantiate a User instance and then fill
in some fields to focus simply on validation.

Here is an example of a User document.

    class User(Document):
        _private_fields = ['secret']
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
        print('  DictPunch caught: %s\n' % (dp))

You might notice that the field which failed is not reported well yet.
That's on the way, but not here yet.

Anyway, in this particular case an MD5 was expected. This is what the 
MD5Field looks like. Notice that it's basically just an implementation
of a `validate()` function.

    class MD5Field(BaseField):
        """A field that validates input as resembling an MD5 hash.
        """
        hash_length = 32
    
        def validate(self, value):
            if len(value) != MD5Field.hash_length:
                raise DictPunch('MD5 value is wrong length')
            try:
                x = int(value, 16)
            except:
                raise DictPunch('MD5 value is not hex')
    
Back to validation...

It's possible we don't want to instantiate a bunch of objects just to
validate some fields, so let's see what it looks like to use a more
typical process: go from python dictionary into a mongo-friendly
DictShield document.

    total_input = {
        'secret': 'e8b5d682452313a6142c10b045a9a135',
        'name': 'J2D2',
        'bio': 'J2D2 loves music',
        'rogue_field': 'MWAHAHA',
    }
    
    valid_fields = User.check_class_fields(total_input)

This is the first time we've seen `check_class_fields()`. This is a 
classmethod which returns true or false, depending whether or not
validation is successful. Once we know validation has passed, we can
pass the dictionary into our User document and call `to_mongo()` to
get a mongo safe dictionary immediately.

    user_doc = User(**total_input).to_mongo()

The values in total_input are matched against fields found in the
DictShield Document class and anything else is discarded.

user_doc now looks like below with `rogue_field` is removed.

    {
        '_types': ['User'], 
        'bio': u'J2D2 loves music', 
        'secret': 'e8b5d682452313a6142c10b045a9a135', 
        'name': u'J2D2', 
        '_cls': 'User'
    }

