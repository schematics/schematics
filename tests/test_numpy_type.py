#!/usr/bin/env python

import unittest

from schematics.models import Model
from schematics.types.numpy import NumpyType
from schematics.types.compound import ModelType, ListType
from schematics.serialize import wholelist
from schematics.exceptions import ValidationError, ConversionError

try:
    import numpy as np

    class TestNumpyType(unittest.TestCase):
        def test_numpy_type_with_model_with_numpy_array(self):
            class TestModel(Model):
                data = NumpyType()

            m = TestModel()
            m.data = np.array([1,2,3,4])
            m.validate()

            self.assertTrue(isinstance(m.data, np.ndarray))
            self.assertTrue(np.array_equal(m.data, [1,2,3,4]))

        def test_numpy_type_with_model_with_list(self):
            class TestModel(Model):
                data = NumpyType()

            m = TestModel()
            m.data = [1,2,3,4]
            m.validate()

            self.assertTrue(isinstance(m.data, np.ndarray))
            self.assertTrue(np.array_equal(m.data, [1,2,3,4]))

        def test_numpy_type_with_model_with_tuple(self):
            class TestModel(Model):
                data = NumpyType()

            m = TestModel()
            m.data = (1,2,3,4)
            m.validate()

            self.assertTrue(isinstance(m.data, np.ndarray))
            self.assertTrue(np.array_equal(m.data, [1,2,3,4]))

        def test_numpy_conversion_with_string(self):
            with self.assertRaises(ConversionError):
                NumpyType()('abc')

        def test_numpy_conversion_with_list(self):
            NumpyType()([1,2,3])

        def test_numpy_conversion_with_tuple(self):
            NumpyType()(((1,2,3,),(4,5,6,)))

        def test_numpy_conversion_with_list_of_tuples(self):
            NumpyType()([(1,2,3,),(4,5,6,)])

        def test_numpy_type_with_numpy_array(self):
            NumpyType().validate(np.array([1,2,3,4,5]))

        def test_numpy_type_with_dtype(self):
            with self.assertRaises(ValidationError):
                NumpyType(dtype='float32').validate(np.array([1,2,3,4,5]))

        def test_numpy_type_with_different_dtype(self):
            with self.assertRaises(ValidationError):
                NumpyType(dtype='int64').validate(np.array([1,2,3,4,5], dtype='float32'))

        def test_numpy_type_with_shape(self):
            NumpyType(shape=(5,)).validate(np.array([1,2,3,4,5]))

        def test_numpy_type_with_invalid_shape(self):
            with self.assertRaises(ValidationError):
                NumpyType(shape=(2,2,)).validate(np.array([1,2,3,4,5]))

        def test_numpy_type_with_size(self):
            NumpyType(size=5).validate(np.array([1,2,3,4,5]))

        def test_numpy_type_with_invalid_size(self):
            with self.assertRaises(ValidationError):
                NumpyType(size=6).validate(np.array([1,2,3,4,5]))

        def test_numpy_type_with_ndim(self):
            NumpyType(ndim=2).validate(np.array([[1,2],[3,4],[5,6]]))

        def test_numpy_type_with_invalid_ndim(self):
            with self.assertRaises(ValidationError):
                NumpyType(ndim=2).validate(np.array([1,2,3,4,5]))

        def test_numpy_type_with_string(self):
            with self.assertRaises(ValidationError):
                NumpyType(ndim=2).validate('abc')
except:
    print('Numpy not installed. Numpy tests not run')
