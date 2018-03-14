
.. _extending:


=======
Extending
=======

For most non trivial cases, the base types may not be enough. Schematics is designed to be flexible to allow for extending data types in order to accomodate custom logic.

Simple Example
=============

A simple example is allowing for value transformations. 

Say that there is a model that requires email validation. Since emails are case insenstive, it might be helpful to convert the input email to lower case before continuing to validate. 

This can be achieved by Extending the Email class 

::

        >>> from schematics.types import EmailType
        >>> class LowerCaseEmailType(EmailType):
        ...
        ...     # override convert method
        ...     def convert(self, value, context=None):
        ...        value = super().convert(value, context)
        ...        return value.lower() # value will be converted to lowercase

Our ``LowerCaseEmailType`` can now be used as an ordinary field.

::

        >>> from schematics.models import Model
        >>> from schematics.types import StringType
        >>> class Person(Model):
        ...     name = StringType()
        ...     bio = StringType(required=True)
        ...     email = LowerCaseEmailType(required=True)
        ...
        >>> p = Person()
        >>> p.name = 'Mutoid Man'
        >>> p.email = 'MutoidMan@Example.com' # technically correct email,but should be 'cleaned'
        >>> p.validate() 
        >>> p.to_native() 
        >>> {'bio': 'Mutoid Man',
        >>> 'email': 'mutoidman@example.com', # the email was converted to lowercase
        >>> 'name': 'Mutoid Man'} 




Taking it a step further
=============

It is also possible that you may have several different kinds of cleaning required.
In such cases, it may not be ideal to subclass a type every time (like the previous example).

We can use the same logic from above and define a ``Type`` that can apply a set of arbitrary
functions.

::

        >>> class CleanedStringType(StringType):
        ...     converters = []
        ... 
        ...     def __init__(self, **kwargs):
        ...         """
        ...         This takes in all the inputs as String Type, but takes in an extra
        ...         input called converters.
        ... 
        ...         Converters must be a list of functions, and each of those functions
        ...         must take in exactly 1 value , and return the transformed input
        ...         """
        ...         if 'converters' in kwargs:
        ...             self.converters = kwargs['converters']
        ...         del kwargs['converters']
        ...         super().__init__(**kwargs)
        ... 
        ...     def convert(self, value, context=None):
        ...         value = super().convert(value, context)
        ...         for func in self.converters:
        ...             value = func(value)
        ...         return value # will have a value after going through all the conversions in order

Now that we have defined our new Type, we can use it. 

::

        >>> from schematics.models import Model
        >>> from schematics.types import StringType
        >>> class Person(Model):
        ...     name = StringType()
        ...     bio = CleanedStringType(required=True,
        ...                             converters = [lambda x: x.upper(),
        ...                             lambda x: x.split(" ")[0]]) # convert to uppercase, then split on " " and just take the first of the split
        ...     email = CleanedStringType(required=True, converts = [lambda x:x.lower()]) # same functionality as LowerCaseEmailType
        ...
        >>> p = Person()
        >>> p.name = 'Mutoid Man'
        >>> p.bio = 'good man'
        >>> p.email = 'MutoidMan@Example.com' # technically correct email,but should be 'cleaned'
        >>> p.validate() 
        >>> p.to_native() 
        >>> {'bio': 'GOOD', # was converted as we specified
        >>> 'email': 'mutoidman@example.com', # was converted to lowercase
        >>> 'name': 'Mutoid Man'} 
