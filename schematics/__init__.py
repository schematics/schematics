__version__ = "3.0.0"

from . import types
from .models import Model, ModelMeta

types.compound.Model = Model
types.compound.ModelMeta = ModelMeta

__all__ = ["Model"]
