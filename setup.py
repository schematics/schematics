#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

from schematics import __version__


class Tox(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--recreate']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


tests_require = open(
    os.path.join(os.path.dirname(__file__), 'requirements-testing.txt')).read().split() + ['tox']

setup(
    name='schematics',
    license='BSD',
    version=__version__,
    description='Structured Data for Humans',
    author=u'James Dennis, Jökull Sólberg, Jóhann Þorvaldur Bergþórsson',
    author_email='jdennis@gmail.com, jokull@plainvanillagames.com, johann@plainvanillagames.com',
    url='http://github.com/schematics/schematics',
    packages=['schematics', 'schematics.types', 'schematics.contrib'],
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    cmdclass={
        'test': Tox,
    },
    tests_require=tests_require,
)
