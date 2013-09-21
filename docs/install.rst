.. _install:

Install Guide
=============

::

  $ pip install schematics

Python 2.6 and 2.7 are supported. 


.. _install_dependencies:

Dependencies
------------

Schematics has no dependencies.  Regardless, we often use it with `ujson
<https://pypi.python.org/pypi/ujson>`_ or `msgpack
<https://pypi.python.org/pypi/msgpack-python/>`_.


.. _install_from_github:

Installing from Github
----------------------

The canonical repository for Schematics is `on Github
<https://github.com/j2labs/schematics>`_.

::

  $ git clone https://github.com/j2labs/schematics.git

New releases are first released as a branch for feedback and then they are
pushed into master around the same time the update is pushed to `Pypi
<https://pypi.python.org/pypi>`_.  The best reason to install from source is to
help us develop Schematics.  See the :doc:`development`.

One trick the development team likes is to alias ``pythisdir`` to add the
current directory to ``$PYTHONPATH``.

::

  $ alias pythisdir='export PYTHONPATH=$PWD'

Between this and ``virtualenv``, the authors are happy hackers.
