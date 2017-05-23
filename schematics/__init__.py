# -*- coding: utf-8 -*-
from __future__ import absolute_import

__version__ = '2.0.0'

# TODO: remove deprecated API
from . import deprecated
deprecated.patch_all()

from . import types
from .models import Model, ModelMeta
from . import types

types.compound.Model = Model
types.compound.ModelMeta = ModelMeta

__all__ = ['Model']
