#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup

version = '2.1.1.1'
setup(
    name='schemv',
    license='BSD',
    version=version,
    description='Python Data Structures for Humans',
    author=u'James Dennis, Jökull Sólberg, Jóhann Þorvaldur Bergþórsson, Kalle Tuure, Paul Eipper',
    author_email='jdennis@gmail.com, jokull@plainvanillagames.com, johann@plainvanillagames.com, kalle@goodtimes.fi, paul@nkey.com.br',
    url='https://github.com/schematics/schematics',
    download_url='https://github.com/schematics/schematics/archive/v%s.tar.gz' % version,
    packages=['schemv', 'schemv.types', 'schemv.contrib', 'schemv.extensions'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=[],
    package_data={
        'schemv': ['locale/*/LC_MESSAGES/*.mo']
    },
    include_package_data=True,
    setup_requires=[
        'pytest-runner',
        'mo_installer',
    ],
    tests_require=[
        'pytest',
        'python-dateutil',
        'pymongo',
        'mock',
        'coverage',
    ],
)
