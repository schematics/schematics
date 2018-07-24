#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), 'schematics/__init__.py')) as f:
    version = re.search("^__version__ = '(\d\.\d+\.\d+(\.?(dev|a|b|rc)\d?)?)'$",
                  f.read(), re.M).group(1)

setup(
    name='schematics',
    license='BSD',
    version=version,
    description='Python Data Structures for Humans',
    author=u'James Dennis, Jökull Sólberg, Jóhann Þorvaldur Bergþórsson, Kalle Tuure, Paul Eipper',
    author_email='jdennis@gmail.com, jokull@plainvanillagames.com, johann@plainvanillagames.com, kalle@goodtimes.fi, paul@nkey.com.br',
    url='https://github.com/schematics/schematics',
    download_url='https://github.com/schematics/schematics/archive/v%s.tar.gz' % version,
    packages=['schematics', 'schematics.types', 'schematics.contrib'],
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
    ],
    install_requires=['typing'],
)
