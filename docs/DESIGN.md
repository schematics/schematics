# How It Works

DictShield is a metaprogramming system for modeling data.  Metaprogramming lets
DictShield know which fields it should treat as part of your model and which are
not important.

The most obvious part is that any fields used, like StringField or IntField, are
treated as relevant data.  Anything else is not.

This doesn't yet answer the question of how DictShield works.


## Fields

First thing we need is the concept of a `Field`.  A field is a container for 
some value, along with some logic for validating and printing the value.

To create the concept of a `Field` we'll create a class that implements two
descriptors: `__get__` and `__set__`. 

Let's consider a simple field like below.

    class IntField(object):
        def __get__(self, instance, owner):
            print '__get__'
            return self.value

        def __set__(self, instance, value):
            print '__set__'
            self.value = value

This field doesn't do anything special.  It just receives or provides the value
of the field for now, which we attach manually to `self`.

We cannot use the class just yet, though.  Watch what happens when we use it as
an instance.

    >>> f = IntField()
    >>> f = 'word'
    >>> type(f)
    <type 'str'>
    >>> f
    'word'
    >>> 

It simply overwrote the value of f.  But check out what happens when we use it
in a class called `Foo`.

    >>> class Foo(object):
    ...     f = IntField()
    ...     x = 'xxxx'
    ... 
    >>> f = Foo()
    >>> f.f = 'word'
    __set__
    >>> f.f
    __get__
    'word'
    
    
### Type System / Validation

Validation comes in the form of type checks, effectively creating a type system
out of however you think you can exactly describe a particular type. 

For an integer field we could simply try converting the value to an `int`.  If
the conversion succeeds, we know the data in the field is valid.

Here is what our `IntField` looks like with a `validate()` function added.

    class IntField(object):
        def __get__(self, instance, owner):
            print '__get__'
            return self.value

        def __set__(self, instance, value):
            print '__set__'
            self.value = value

        def validate(self):
            """If no exception is thrown when we convert the value to an int
            it is because validation has succeeded.
            """
            try:
                int(self.value)
            except:
                raise Exception()

OK. Let's try using our new `validate` function.

    >>> class Foo(object):
    ...     i = IntField()
    ...     x = 'xxxx'
    ...
    >>> f = Foo()
    >>> f.i = 5
    __set__
    >>> f.i.validate()
    __get__
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    AttributeError: 'int' object has no attribute 'validate'

Hmm...  Looks like we can't call `validate()` on `f.i` because our definition of
`__get__` is getting in the middle and returning 5.  So we then attempt to call 
`validate()` on an int, which fails.

We need a way of getting at the `IntField` class itself without accidentally
triggering a call to `__get__`.  We could try putting the field in a `dict` and
extract the field by it's name from the dict when we need to call `validate()`.

This is what the new definition of `Foo` looks like with `_fields` added.

    class Foo(object):
        i = IntField()
        x = 'xxxx'
        _fields = {'i': i}

It's a little cumbersome to consider creating `_fields` by hand, but we'll
automate that soon enough.  For now, let's check if we can reach `validate()`
correctly.

    >>> f = Foo()
    >>> f.i = 5
    __set__
    >>> f._fields['i'].validate()
    >>>
    
Looks like it worked!  The real test, though, is if we can get validation to
fail.

    >>> f.i = 'not an int'
    >>> f._fields['i'].validate()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 12, in validate
    Exception

Wahoo! We're in business.


## Documents

Up to now we've been using an extremely simple class `Foo` to hold our
`IntField`, but this isn't useful to us yet.  The code for validating a field is
too long: `f._fields['i'].validate()`. 

We'll rename `Foo` into a more useful name: `Document`.

It would be better to make a `Document` level validate function that can loop
through each field and validate them for us.

    class Document(object):
        i = IntField()
        x = 'xxxx'
        _fields = {'i': i}
        
        def validate(self):
            for k,v in self._fields.items():
                v.validate()

Let's see if it works.

    >>> d = Document()
    >>> d.i = 5
    __set__
    >>> d.validate()
    >>> d.i = 'word'
    __set__
    >>> d.validate()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 7, in validate
      File "<stdin>", line 12, in validate
    Exception

Looks good.  But I think it's still awkward to write that `_fields` dictionary
by hand.  It's possible someone might even forget to do.


## Metaclasses

To solve this we can create a Python metaclass.  A metaclass allows us to run
code at the time a class is created.  This is different from when a class is
instantiated because the class is created the moment the python interpreter
reads your class definition.  It is instantiated when you say something like:

    d = Document()

Let's look at a simple example to drive the point home.

    >>> class MetaBar(type):
    ...     def __new__(cls, name, bases, attrs):
    ...         klass = type.__new__(cls, name, bases, attrs)
    ...         print 'Hello from MetaBar
    ...         klass._some_field = 'some field'
    ...         return klass
    ... 
    >>> class Bar(object):
    ...     __metaclass__ = MetaBar
    ...     def __init__(self):
    ...         print 'Hello from __init__'
    ... 
    Hello from MetaBar
    >>>

Look at that! It printed 'Hello from MetaBar' simply because we created a class
that uses `MetaBar` for it's metaclass.  This means we can run code on class
definitions whenever we create them.

What does this let us do?  Well... for starters it let's us dynamically figure
out how to create that `_fields` dictionary we mentioned before.  If someone 
subclasses `Bar`, which uses `MetaBar` as it's metaclass, they automatically
populate `_fields` and our validation technique won't depend on any extra work
from the programmer.

Let's see explore that a little bit.


### Recap

Here is our `IntField` from above, with the print statements removed.

    class IntField(object):
        def __get__(self, instance, owner):
            return self.value
    
        def __set__(self, instance, value):
            self.value = value
    
        def validate(self):
            try:
                int(self.value)
            except:
                raise Exception()
    
And here is our `Foo` class.  Notice we no longer create `_fields` by hand.
Also notice, however, that we make use of `_fields` in `validate()`.

    class Document(object):
        __metaclass__ = MetaDoc
        
        i = IntField()
        x = 'xxxx'
        
        def validate(self):
            for k,v in self._fields.items():
                v.validate()

Now, here is the fun part.  We'll create a `MetaDoc` that loops through each
attribute in `Document` and determines which ones are `IntField` instances.  It
then populates `_fields` with any `IntField` instances it finds.

In it's most stripped down form, that looks like this.

    class MetaDoc(type):
        def __new__(cls, name, bases, attrs):
            klass = type.__new__(cls, name, bases, attrs)
            klass._fields = dict()
            
            for attr_name, attr_value in attrs.items():
                if type(attr_value) is IntField:
                    klass._fields[attr_name] = attr_value
                    
            return klass

Let's see what it does.

    >>> class Document(object):
    ...     __metaclass__ = MetaDoc
    ...     i = IntField()
    ...     x = 'xxxx'
    ...     def validate(self):
    ...         for k,v in self._fields.items():
    ...             v.validate()
    ... 
    >>> 
    >>> d = Document()
    >>> d._fields
    {'i': <__main__.IntField object at 0x102e64d90>}
    
Neat!  So `_fields` populated correctly with our `IntField`. But can we validate
a field?

    >>> d.i = 'not a number'
    >>> d.validate()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "<stdin>", line 7, in validate
      File "<stdin>", line 10, in validate
    Exception
    >>> d.i = 5
    >>> d.validate()
    >>> 
    
Looks good!


## DictShield

This design document aims to teach someone about metaprogramming with Python
because metaprogramming is exactly how DictShield magically knows which fields
you want serialized as part of it's `to_python()` or `to_json()` calls.

Read the source code for more.
