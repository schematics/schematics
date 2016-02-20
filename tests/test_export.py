# -*- coding: utf-8 -*-
import datetime
import pytest
import uuid

from schematics.common import *
from schematics.models import Model
from schematics.transforms import ExportConverter
from schematics.types import *
from schematics.types.compound import *
from schematics.types.serializable import serializable


class BaseModel(Model):
    pass

class N(BaseModel):
    floatfield = FloatType()
    uuidfield = UUIDType()

class M(BaseModel):
    intfield = IntType()
    stringfield = StringType()
    dtfield = DateTimeType()
    utcfield = UTCDateTimeType()
    modelfield = ModelType(N)

field = ListType(ModelType(M)) # standalone field

input = { 'intfield': 3,
          'stringfield': 'foobar',
          'dtfield': '2015-11-26T09:00:00.000000',
          'utcfield': '2015-11-26T07:00:00.000000Z',
          'modelfield': {
              'floatfield': 1.0,
              'uuidfield': '54020382-291e-4192-b370-4850493ac5bc' }}

natives = { 'intfield': 3,
            'stringfield': 'foobar',
            'dtfield': datetime.datetime(2015, 11, 26, 9),
            'utcfield': datetime.datetime(2015, 11, 26, 7),
            'modelfield': { 
                'floatfield': 1.0,
                'uuidfield': uuid.UUID('54020382-291e-4192-b370-4850493ac5bc') }}


def test_to_native():

    m = M(input)
    assert m.to_native() == m

    m = M({'modelfield': {}})
    result = m.to_native()
    assert result.intfield is None
    assert result.modelfield.floatfield is None

    m = M({'modelfield': {}})
    del m.intfield
    del m.modelfield.floatfield
    result = m.to_native()
    assert 'intfield' not in result
    assert 'floatfield' not in result.modelfield
    result = m.to_native(export_level=ALL)
    assert result.intfield is None
    assert result.modelfield.floatfield is None

    result = field.convert([input])
    assert field.to_native(result) == result


def test_to_dict():

    m = M(input)
    assert m.to_dict() == natives

    result = field.convert([input])
    assert field.to_dict(result) == [natives]


def test_to_primitive():

    m = M(input)
    assert m.to_primitive() == input

    result = field.convert([input])
    assert field.to_primitive(result) == [input]


class Foo(object):
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __eq__(self, other):
        return type(self) == type(other) \
                 and self.x == other.x and self.y == other.y

class FooType(BaseType):
    def to_native(self, value, context):
        if isinstance(value, Foo):
            return value
        return Foo(value['x'], value['y'])
    def to_primitive(self, value, context):
        return dict(x=value.x, y=value.y)


def test_custom_exporter():

    class X(Model):
        id = UUIDType()
        dt = UTCDateTimeType()
        foo = FooType()

    x = X({ 'id': '54020382-291e-4192-b370-4850493ac5bc',
            'dt': '2015-11-26T07:00',
            'foo': {'x': 1, 'y': 2} })

    assert x.to_dict() == {
        'id': uuid.UUID('54020382-291e-4192-b370-4850493ac5bc'),
        'dt': datetime.datetime(2015, 11, 26, 7),
        'foo': Foo(1, 2) }

    exporter = ExportConverter(PRIMITIVE, [UTCDateTimeType, UUIDType])

    assert x.export(field_converter=exporter) == {
        'id': uuid.UUID('54020382-291e-4192-b370-4850493ac5bc'),
        'dt': datetime.datetime(2015, 11, 26, 7),
        'foo': {'x': 1, 'y': 2} }


def test_converter_function():

    class X(Model):
        id = UUIDType()
        dt = UTCDateTimeType()
        foo = FooType()

    x = X({ 'id': '54020382-291e-4192-b370-4850493ac5bc',
            'dt': '2015-11-26T07:00',
            'foo': {'x': 1, 'y': 2} })

    exporter = lambda field, value, context: field.export(value, PRIMITIVE, context)

    assert x.export(field_converter=exporter) == x.to_primitive()

