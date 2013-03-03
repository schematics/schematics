# Schematics

Schematics is an easy way to model data.  It provides mechanisms for structuring
data, initializing data, serializing data, formatting data and validating data
against type definitions, like an email address.

It is going through substantial changes at the moment.  Please bear with me as
I simplify, extend, and create a new foundation from which to build. 

I have been listening to everyone's suggestions and finally decided the right
way to address them was to build a new core. 

Along the way I have decided to change some things about how validation will
work.  It is going to be broken out into something that is list oriented and
never uses exceptions.  Exceptions are often misused and it is a matter of my
personal taste to avoid them altogether.  Having a system that returns a list
of validation data are easier to work with than systems that throw exceptions.

[The demos](https://github.com/j2labs/schematics/tree/master/demos) are fully
up to date with the current thinking, but it's possible this library will
change, or even has already changed significantly, beyond what people are used
to with DictShield.  I believe that's a great thing.
