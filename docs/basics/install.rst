.. _install:

=============
Install Guide
=============

Tagged releases are available from `PyPI <https://pypi.python.org/pypi>`_::

  $ pip install schematics

The latest development version can be obtained via git::

  $ pip install git+https://github.com/schematics/schematics.git#egg=schematics

Schematics currently supports Python versions 2.6, 2.7, 3.3, and 3.4.


.. _install_dependencies:

Dependencies
============

The only dependency is `six <https://pypi.python.org/pypi/six>`_ for Python 2+3 support.


.. _install_from_github:

Installing from GitHub
======================

The `canonical repository for Schematics <https://github.com/schematics/schematics>`_ is hosted on GitHub.

Getting a local copy is simple::

  $ git clone https://github.com/schematics/schematics.git

If you are planning to contribute, first create your own fork of Schematics on GitHub and clone the fork::

  $ git clone https://github.com/YOUR-USERNAME/schematics.git

Then add the main Schematics repository as another remote called *upstream*::

  $ git remote add upstream https://github.com/schematics/schematics.git

See also :doc:`/development/development`.

