.. _development:

Development
===========

Schematics development is lead by `James Dennis <http://j2labs.io>`_, but this
project is very much the sum of the work from many people.

.. code: sh

  $ cd schematics
  $ git shortlog -sn

Schematics has a few design choices that are both explicit and implicit. We
care about these decisions and have probably debated them on the mailing list.
We ask that you honor those and make them known in this document.


Get the code
------------

Please see the :ref:`source-code-checkouts` section of the :doc:`installation`
page for details on how to obtain Fabric's source code.


Tests
-----

Using py.test::

  $ py.test tests/


