# Schematics

Schematics is an easy way to model data.  It provides mechanisms for structuring
data, initializing data, serializing data, formatting data and validating data
against type definitions, like an email address.

The library provides data types, in the form of fields. Each field controls the
details of how its data should look in various formats.  It also provides a 
`validate()` function which is responsible for determining if the data looks
correct.

Schematics' main goal is to provide similar functionality to a type system
along with a way to generate the schematics we send to the Internet, or store
in a database, or send to some Java process, or basically any use case with
structured data.

A blog model might look like this:

```python
from schematics.models import Model
from schematics.types import StringType

class BlogPost(Model):
    title = StringType(max_length=40)
    body = StringType(max_length=4096)
```

Schematics objects serialize to JSON by default. Store them in Memcached,
MongoDB, Riak, whatever you need.

```python
>>> from schematics.models import Model
>>> from schematics.types import StringType
>>> class Comment(Model):
...   name = StringType(max_length=10)
...   body = StringType(max_length=4000)
...
>>> data = {'name':'a hacker', 'body':'schematics makes validation easy'}
>>> Comment(**data).validate()
True
```
    
Let's see what happens if we try using invalid data.
    
```python
>>> data['name'] = 'a hacker with a name that is too long'
>>> Comment(**data).validate()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/path/to/site-packages/schematics/models.py", line 280, in validate
    field._validate(value)
  File "/path/to/site-packages/schematics/fields/base.py", line 99, in _validate
    self.validate(value)
  File "/path/to/site-packages/schematics/fields/base.py", line 224, in validate
    self.field_name, value)
schematics.base.TypeException: String value is too long - name:a hacker with a name who is too long
```

Combining schematics with JSON coming from a web request is quite natural as
well. Say we have some data coming in from an iPhone:

```python
json_data = request.post.get('data')
data = json.loads(json_data)
```

Validating the data then looks like this: `Comment(**data).validate()`.

Easy.


# The Design

Schematics aims to provides helpers for a few types of common needs for
modeling. It has been useful on the server-side so far, but I believe it could
also serve for building an RPC.

1. Creating Flexible models

2. Easy To Use With Databases Or Caches

3. A Type System

4. Validation Of Types

5. Input / Output Shaping

Schematics also allows for object hierarchies to be mapped into dictionaries
too. This is useful primarily to those who use schematics to instantiate
classes representing their data instead of just filtering dictionaries through
the class's static methods.


# Example Uses

There are a few ways to use schematics.  A simple case is to create a class
Schematic that has typed fields.  Schematics offers multiple types in
`types.py`, like an EmailType or DecimalType.


## Creating Flexible models

Below is an example of a Media class with a single field, the title.

```python
from schematics.models import Model
from schematics.types import StringType

class Media(Model):
    """Simple model that has one Stringtype member
    """
    title = StringType(max_length=40)
```

You create the class just like you would any Python class. And we'll see how
that class is represented when serialized to a Python dictionary.

```python
m = Media()
m.title = 'Misc Media'
m.to_python()
```

The output from this looks like:

```python
{
    '_types': ['Media'],
    '_cls': 'Media',
    'title': u'Misc Media'
}
```

All the meta information is removed and we have just a barebones representation
of our data. Notice that the class information is still there as `_cls` and
`_types`.


### More On Object Modeling

We see two keys that come from Media's meta class: `_types` and `_cls`.
`_types` stores the hierachy of model classes used to create the
Document. `_cls` stores the specific class instance. This becomes more
obvious when I subclass Media to create the Movie model below.

```python
import datetime
from schematics.types import IntType

class Movie(Media):
    """Subclass of Foo. Adds bar and limits publicly shareable
    fields to only 'bar'.
    """
    year = IntType(min_value=1950,
                   max_value=datetime.datetime.now().year)
    personal_thoughts = StringType(max_length=255)
    class Options:
        public_fields = ['title','year']
```


Here's an instance of the Movie class:

```python
mv = Movie()
mv.title = u'Total Recall'
mv.year = 1990
mv.personal_thoughts = u'I wish I had three hands...'
```

This is the model serialized to a Python dictionary:

```python
{
    'personal_thoughts': u'I wish I had three hands...',
    '_types': ['Media', 'Media.Movie'],
    'title': u'Total Recall',
    '_cls': 'Media.Movie',
    'year': 1990
}
```

Notice that `_types` has kept track of the relationship between `Movie` and
`Media`.


## Easy To Use With Databases Or Caches

We could pass this directly to Mongo to save it.

```python
>>> db.test_collection.save(m.to_python())
```

Or if we were using Riak.

```python
>>> media = bucket.new('test_key', data=m.to_python())
>>> media.store()
```

Or maybe we're storing json in a memcached.

```python
>>> mc["test_key"] = m.to_json()
```


## A Type System

schematics has its own type system - every field within a `Model` is defined with a specific type,
for example a string will be defined as `StringType`. This "strong typing" makes serialising/deserialising
semi-structured data to and from Python much more robust.

### All Types

A complete list of the types supported by schematics:

| **TYPE**               | **DESCRIPTION**                                                            |
|-----------------------:|:---------------------------------------------------------------------------|
|         **Text types** |                                                                            |
|           `StringType` | A unicode string                                                           |
|              `URLType` | A valid URL                                                                |
|            `EmailType` | A valid email address                                                      |
|           **ID types** |                                                                            |
|             `UUIDType` | A valid UUID value, optionally auto-populates empty values with new UUIDs  |
|         `ObjectIDType` | Wraps a MongoDB "BSON" ObjectId                                            |
|      **Numeric types** |                                                                            |
|           `NumberType` | Any number (the parent of all the other numeric types)                     |
|              `IntType` | An integer                                                                 |
|             `LongType` | A long                                                                     |
|            `FloatType` | A float                                                                    |
|          `DecimalType` | A fixed-point decimal number                                               |
|      **Hashing types** |                                                                            |
|              `MD5Type` | An MD5 hash                                                                |
|             `SHA1Type` | An SHA1 hash                                                               |
|**'Native type' types** |                                                                            |
|          `BooleanType` | A boolean                                                                  |
|         `DateTimeType` | A datetime                                                                 |
|         `GeoPointType` | A geo-value of the form x, y (latitude, longitude)                         |
|         **Containers** |                                                                            |
|             `ListType` | Wraps a standard type, so multiple instances of the field can be used      |
|       `SortedListType` | A `Listtype` which sorts the list before saving, so list is always sorted  |
|             `DictType` | Wraps a standard Python dictionary                                         |
|   `MultiValueDictType` | Django's implementation of a MultiValueDict.                               |
| `ModelType`            | Stores a schematics `Model` inside another model as a field.               |

Types can also receive some arguments for customizing their behavior. The
currently accepted arguments are:

| **ARGUMENT**                | **DESCRIPTION**                                                           |
|----------------------------:|:--------------------------------------------------------------------------|
|           *field_name=None* | The name of the field in serialized form.                                 |
|            *required=False* | This field must have a value or validation and serialization will fail.   |
|              *default=None* | Either a default value or callable that produces a default.               |
|            *id_field=False* | Set to `True` if this field should be used as the id field.               |
|           *validation=None* | Supply an alternate function for validation for this field.               |
|              *choices=None* | Limit the possible values for this field by passing a list.               |
|          *description=None* | Set an alternate field description for serialization to jsonschema.       |
| *minimized_field_name=None* | Name of the field to use when serializing the model with short names.     |
|           *uniq_field=None* | Legacy arg. Will be removed soon.                                         |


### A Close Look at the MD5Type

This is what the MD5Type looks like. Notice that it's basically just
an implementation of a `validate()` function, which raises a `TypeException`
exception if validation fails.

```python
class MD5Type(BaseType):
    """A type that validates input as resembling an MD5 hash.
    """
    hash_length = 32
    def validate(self, value):
        if len(value) != MD5Type.hash_length:
            raise TypeException('MD5 value is wrong length',
                                self.field_name, value)
        try:
            x = int(value, 16)
        except:
            raise TypeException('MD5 value is not hex',
                                self.field_name, value)
```

You might notice that the field which failed is also reported. It's available on
the exception as `field_name` and `field_value`.

The exception prints in this pattern `field_name(field_value): reason`.

    TypeException caught: secret(whatevz):  MD5 value is wrong length

If you think the overhead of validation is unnecessary for some use cases, you
can skip it by never calling `validate()`.


## Validation Of Types

As we saw above, we know we can validate `Model` instances by calling
`Validate()`. Let's generate a `User` instance with seed data and validate it.

First, here is the User model:

```python
class User(Model):
    secret = MD5Type()
    name = StringType(required=True, max_length=50)
    bio = StringType(max_length=100)
    url = URLType()
    class Options:
        public_fields = ['name']
```

Next, we seed the instance with some data and validate it.

```python
user = User(**{'secret': 'whatevs', 'name': 'test hash'})
try:
    user.validate()
except TypeException, se:
    print 'TypeException caught: %s' % (se)
```

This calling `validate()` on a model validates an instance by looping through
its fields and calling `field.validate()` on each one.

We can still be leaner. Schematics also allows validating input without
instantiating any objects.


### Validating User Input

Let's say we get this JSON string from a user.

```python
{"bio": "Python, Erlang and guitars!", "secret": "e8b5d682452313a6142c10b045a9a135", "name": "J2D2"}
```

We might write some server code that looks like this:

```python
json_string = request.get_arg('data')
user_input = json.loads(json_string)
User(**user_input).validate()
```

This method builds a User instance out of the input, which also throws away
keys that aren't in the User definition.

We then call `validate()` on that `User` instance to validate each field against
what the dictionary contained. If the data doesn't pass exception, a
`TypeException` is thrown and we handle the error.

If validation passed, we're done. We know the data looks good.


## Input / Output shaping

Input is coming from everyone online, so who knows what it's in there. We do,
however, know exactly what fields we want to be there. Same goes for output.

A web system typically has tiers involved with data access, depending on the
user logged in. My most common need is to differentiate between internal system
data (the raw model), data fields for the owner of the data (internal data
removed) and the data fields that are shareable with the general public.

### Removing Unknown Fields

Unrecognized fields, in user input, are thrown away. This makes handling input
fairly easy because you are generally working with a list of fields, what they
look like and how to turn them into Python or JSON. Not much else.

So here's how you can reduce the user input into just the fields found on a
`User` model.

Consider the following string:

```python
{
    "rogue_field": "MWAHAHA",
    "bio": "Python, Erlang and guitars!",
    "secret": "e8b5d682452313a6142c10b045a9a135",
    "name": "J2D2"
}
```

Parse it just like before.

```python
user_doc = User(**total_input).to_python()
```

The values in total_input are matched against fields found in the schematics
model class and everything else is discarded.

`User_doc` now looks like below with `rogue_field` removed.

```python
{
    '_types': ['User'],
    'bio': u'Python, Erlang and guitars!,
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    'name': u'J2D2',
    '_cls': 'User'
}
```


### JSON for Owner of model

Here is our `Movie` model safe for transmitting to the owner of the document.
We achieve this by calling `Movie.make_json_ownersafe`. This function is a
classmethod available on the `Model` class. It knows to remove `_cls` and
`_Types` because they are in `Model._internal_fields`. You can add any
fields that should be treated as internal to your system by adding a list named
`private_fields` to your model options and listing each field.

```json
{
    "personal_thoughts": "I wish I had three hands...",
    "title": "Total Recall",
    "year": 1990
}
```


### JSON for Public View of model

This dictionary is safe for transmitting to the public, not just the owner.
Get this by calling `make_json_publicsafe`.

```json
{
    "title": "Total Recall",
    "year": 1990
}
```


### JSON Schema

The schematic of models can also be serialized into JSON Schema. Again, with our `Movie` document.

```python
>>> Movie.to_jsonschema()
'{
    "title": "Movie"
    "type": "object",
    "properties": {
        "year": {
            "minimum": 1950,
            "type": "number",
            "maximum": 2012,
            "title": "year"
        }, 
        "title": {
            "title": "title",
            "type": "string", 
            "maxLength": 40
        }
    }, 
}'
```


## Working Without Instances

Consider a user updating some of their settings. Rather than validate the entire
model, you want to check validation for just the field the client is
updating and tell your database to store just that field.

schematics offers a few classmethods to facilitate this.


### Class Level Validation

`validate_class_fields` gives us that by checking if some dictionary matches
the pattern it needs, including required fields. Notice, it's also a
classmethod. No need to instantiate anything.

```python
user_input = {
    'url': 'http://j2labs.tumblr.com'
}

try:
    User.validate_class_fields(user_input)
except TypeException, se:
    print('  Validation failure: %s\n' % (dp))
```

This particular code would throw an exception because the `name` field is
required, but not present.

`validation_class_partial` lets you validate only the fields present in the
input. This is useful for updating one or two fields in a model at a time,
like we attempted above.

```python
...
    User.validate_class_partial(user_input)
...
```


### Aggregating Errors

schematics' validation methods can also give you a list of which individual fields
failed validation.  Calling a model's `validate()` method with `validate_all=True`
will raise a `ModelException` whose `errors_list` attriute is a list of 0 or more
exceptions, and calling `validate_class_fields` with `validate_all=True` will return the
same list.

```python
exceptions = User.validate_class_fields(total_input, validate_all=True)
if exceptions:
    # Validation was not successful
```

# Installing

schematics is in [pypi](http://pypi.python.org) so you can use `easy_install` or `pip`.

    pip install schematics


# Contributors

* [James Dennis](https://github.com/j2labs)
* [Andrew Gwozdziewycz](https://github.com/apgwoz)
* [Dion Paragas](https://github.com/d1on)
* [Tom Waits](https://github.com/tomwaits)
* [Chris McCulloh](https://github.com/st0w)
* [Sean O'Connor](https://github.com/SeanOC)
* [Alexander Dean](https://github.com/alexanderdean)
* [Rob Spychala](https://github.com/robspychala)
* [Ben Beecher](https://github.com/gone)
* [John Krauss](https://github.com/talos)
* [Titusz](https://github.com/titusz)
* [Nicola Iarocci](https://github.com/nicolaiarocci)
* [Justin Lilly](http://github.com/justinlilly)
* [Jonathan Halcrow](https://github.com/jhalcrow)


# License

BSD!

