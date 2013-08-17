#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

from schematics import __version__


class PyTest(TestCommand):
    """Test command."""
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='schematics',
    license='BSD',
    version=__version__,
    description='Structured Data for Humans',
    author=u'James Dennis, Jökull Sólberg, Jóhann Þorvaldur Bergþórsson',
    author_email='jdennis@gmail.com, jokull@plainvanillagames.com, johann@plainvanillagames.com',
    url='http://github.com/j2labs/schematics',
    packages=['schematics', 'schematics.types'],
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    cmdclass={
        'test': PyTest,
    },
    tests_require=[
        'ordereddict==1.1',
        'pytest==2.3.5',
    ],
)
