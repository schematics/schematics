#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

from schematics import __version__

setup(
    name='schematics',
    license='BSD',
    version=__version__,
    description='Structured Data for Humans',
    author=u'James Dennis, Jökull Sólberg, Jóhann Þorvaldur Bergþórsson',
    author_email='jdennis@gmail.com, jokull@plainvanillagames.com, johann@plainvanillagames.com',
    url='http://github.com/j2labs/schematics',
    packages=['schematics', 'schematics.types', 'schematics.contrib'],
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)
