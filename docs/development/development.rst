.. _development:

=================
Developer's Guide
=================

Schematics development is currently led by `Kalle Tuure <kalle@goodtimes.fi>`_,
but this project is very much a sum of the work done by a community.


.. _development_contributors:

List of Contributors
====================

::

  $ cd schematics
  $ git shortlog -sne

Schematics has a few design choices that are both explicit and implicit. We
care about these decisions and have probably debated them on the mailing list.
We ask that you honor those and make them known in this document.


.. _development_get_the_code:

Get the code
============

Please see the :ref:`install_from_github` section of the :doc:`/basics/install`
page for details on how to obtain the Schematics source code.


.. _development_tests:

Tests
=====

Using pytest::

  $ py.test


.. _writing_documentation:

Writing Documentation
=====================

:doc:`Documentation </index>` is essential to helping other people understand,
learn, and use Schematics. We would appreciate any help you can offer in
contributing documentation to our project.

Schematics uses the .rst (reStructuredText) format for all of our
documentation. You can read more about .rst on the `reStructuredText Primer <http://sphinx-doc.org/rest.html>`_
page.


.. _installing_documentation:

Installing Documentation
========================

Just as you verify your code changes in your local environment before
committing, you should also verify that your documentation builds and displays
properly on your local environment.

First, install `Sphinx <http://sphinx-doc.org/latest/install.html>`_:

::

  $ pip install sphinx

Next, run the Docs builder:

::

  $ cd docs
  $ make html

The docs will be placed in the ``./_build`` folder and you can view them from
any standard web browser. (Note: the ``./_build`` folder is included in the
``.gitignore`` file to prevent the compiled docs from being included with your
commits).

Each time you make changes and want to see them, re-run the Docs builder and
refresh the page.

Once the documentation is up to your standards, go ahead and commit it. As with
code changes, please be descriptive in your documentation commit messages as it
will help others understand the purpose of your adjustment.

