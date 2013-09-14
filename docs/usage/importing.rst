=========
Importing
=========

To import data is to convert from an external, possibly non-pythonic,
representation of data into a Schematics representation.

The general mechanism for data import is to call a function on every field in
the data.  This function should coerce the input into the best Pythonic
representation of the data possible.  A date string, for example, would be
converted to a ``datetime.datetime`` instance.


Terminology
===========


Coercing Data
=============


Compound Types
==============


Customizing Input
=================


Context
-------


Partial
-------


Strict
------


Serialized Name
---------------
