from __future__ import absolute_import

import numpy as np

from ..types.base import BaseType
from ..exceptions import ValidationError, ConversionError


class NumpyType(BaseType):
    """A numpy field type. Accepts list, tuple or numpy.ndarray types.
    Non numpy.ndarray types will be converted to a numpy.ndarray.
    """

    MESSAGES = {
        'convert_type': u"Value is not numpy array compatible",
        'convert_shape': u"Could not convert shape",
        'convert_dtype': u"Could not convert to dtype",
        'not_numpy_array': u"Not a numpy array.",
        'dtype_differs': u"Numpy dtype doesn't match.",
        'shape_differs': u"Array shape doesn't match.",
        'size_differs': u"Array size doesn't match.",
        'ndims_differs': u"Dimensions don't match.",
    }

    def __init__(self, dtype=None, shape=None, size=None, ndim=None, **kwargs):
        super(NumpyType, self).__init__(**kwargs)
        self.dtype = dtype
        self.shape = shape
        self.size = size
        self.ndim = ndim

    def convert(self, value):
        # numpy can store strings in a numpy array
        # but this usually not intended
        # in that case, send in a numpy array that has the string in it
        if isinstance(value, (list, tuple)):
            value = np.array(value, dtype=self.dtype)

        if not isinstance(value, np.ndarray):
            raise ConversionError(self.messages['convert_type'])

        try:
            if self.dtype and value.dtype != self.dtype:
                value.dtype = self.dtype
        except:
            raise ConversionError(self.messages['convert_dtype'])

        try:
            if self.shape and value.shape != self.shape:
                value.shape = self.shape
        except:
            raise ConversionError(self.messages['convert_shape'])

        return value

    def validate(self, value):
        if value is not None:
            if not isinstance(value, np.ndarray):
                raise ValidationError(self.messages['not_numpy_array'])

            if self.dtype and value.dtype != self.dtype:
                raise ValidationError(self.messages['dtype_differs'])

            if self.shape and value.shape != self.shape:
                raise ValidationError(self.messages['shape_differs'])

            if self.size and value.size != self.size:
                raise ValidationError(self.messages['size_differs'])

            if self.ndim and value.ndim != self.ndim:
                raise ValidationError(self.messages['ndims_differs'])

        return True
