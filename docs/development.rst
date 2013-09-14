.. _development:

Developer's Guide
=================

Schematics development is lead by `James Dennis <http://j2labs.io>`_, but this
project is very much a sum of the work done by a community.


.. _development_contributors:

List of Contributors
--------------------

.. code: sh

  $ cd schematics
  $ git shortlog -sn

Schematics has a few design choices that are both explicit and implicit. We
care about these decisions and have probably debated them on the mailing list.
We ask that you honor those and make them known in this document.


.. _development_get_the_code:

Get the code
------------

Please see the :ref:`source-code-checkouts` section of the :doc:`installation`
page for details on how to obtain Fabric's source code.


.. _development_tests:

Tests
-----

Using py.test::

  $ py.test tests/


