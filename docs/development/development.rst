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


.. _development_commit_guidelines:

Commit Message Guidelines
=========================

We use a standard format for the commit messages that allows more readable
browsing of the project history, and specially to help in generating the
change log.

Commit Message Format
---------------------

Each commit message consists of a **header**, a **body** and a **footer**.
The header has a special format that includes a **type**, a **scope**
and a **subject**:

::

  <type>(<scope>): <subject>
  <BLANK LINE>
  <body>
  <BLANK LINE>
  <footer>

The **header** is mandatory and the **scope** of the header is optional.

Any line of the commit message cannot be longer 100 characters! This allows
the message to be easier to read on GitHub as well as in various git tools.

The footer should contain a `closing reference <https://help.github.com/articles/closing-issues-via-commit-messages/>`_ to an issue if any.

Allowed **type** values:

- build: Changes that affect the build system or external dependencies
- ci: Changes to CI configuration files and scripts
- docs: Documentation only changes
- feat: A new feature
- fix: A bug fix
- perf: A code change that improves performance
- refactor: A code change that neither fixes a bug nor adds a feature (eg. renaming a variable)
- style: Changes that do not affect the meaning of the code (formatting, missing semi colons, etc)
- test: Adding missing tests or correcting existing tests

Example **scope** values:

The scope should be the name of the module affected.

- types
- models
- serializable
- schema
- transforms
- etc.

Subject
-------

The subject contains a succinct description of the change:

- use the imperative, present tense: "change" not "changed" nor "changes"
- don't capitalize the first letter
- no dot (.) at the end

Body
----

Just as in the subject, use the imperative, present tense: "change" not
"changed" nor "changes". The body should include the motivation for the
change and contrast this with previous behavior.

Footer
------

The footer should contain any information about Breaking Changes and is
also the place to reference GitHub issues that this commit Closes.

Example:
::

  Closes #123, #234, #456

Breaking Changes should start with the word BREAKING CHANGE: with a space
or two newlines. The rest of the commit message is then used for this.

Example:

::

  BREAKING CHANGE: convert and validate functions for Types now need to
    accept an optional context parameter and pass it to any calls to super.

    To migrate the code follow the example below:

    Before:

    def convert(self, value):
        return super().convert(value)

    After:

    def convert(self, value, context=None):
        return super().convert(value, context)

    Refer to the documentation regarding using the context data.


.. _development_tests:

Tests
=====

Using pytest::

  $ py.test

Naming
------

Schematics has the tradition of naming examples after music bands and artists
so you can use your favorite ones when creating examples in the docs and for
test fixtures.

If you are not feeling particularly creative, you can use one of @jmsdnns
selections below:

- Mutoid Man
- Pulled Apart By Horses
- Fiona Apple
- Julia Holter
- Lifetime
- Nujabes
- Radiohead
- Stars Of The Lid


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


.. _release_guide:

Release Guide
=============

To prepare a new release, follow this procedure:

- Update version number in ``schematics/__init__.py``
- Add signed tag with version number in git, ex: ``git tag -s v1.1.3 -m "Release v1.1.3"``
- Create distribution archives ``poetry build``
- Sign the generated archives:

::
  gpg --detach-sign -u GPGKEYID -a dist/schematics-1.1.3-py2.py3-none-any.whl
  gpg --detach-sign -u GPGKEYID -a dist/schematics-1.1.3.tar.gz

- Upload to PyPI ``twine upload dist/schematics-1.1.3*``
