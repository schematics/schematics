# -*- coding: utf-8 -*-
import pytest

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

    _natives = natives.copy()
    assert m._data.pop('modelfield')._data == _natives.pop('modelfield')
    assert m._data == _natives


def test_to_dict():

    m = M(input)
    assert m.to_dict() == natives


def test_to_primitive():

    m = M(input)
    assert m.to_primitive() == input


def test_custom_exporter():

    class Foo(object):
        def __init__(self, x, y):
            self.x, self.y = x, y
        def __eq__(self, other):
            return self.x == other.x and self.y == other.y

    class FooType(BaseType):
        def to_native(self, value, context):
            if isinstance(value, Foo):
                return value
            return Foo(value['x'], value['y'])
        def to_primitive(self, value, context):
            return dict(x=value.x, y=value.y)

    class M(Model):
        id = UUIDType()
        dt = UTCDateTimeType()
        foo = FooType()

    m = M({ 'id': '54020382-291e-4192-b370-4850493ac5bc',
            'dt': '2015-11-26T07:00',
            'foo': {'x': 1, 'y': 2} })

    assert m.to_dict() == {
        'id': uuid.UUID('54020382-291e-4192-b370-4850493ac5bc'),
        'dt': datetime.datetime(2015, 11, 26, 7),
        'foo': Foo(1, 2) }

    exporter = ExportConverter(PRIMITIVE, [UTCDateTimeType, UUIDType])

    assert m.export(PRIMITIVE, field_converter=exporter) == {
        'id': uuid.UUID('54020382-291e-4192-b370-4850493ac5bc'),
        'dt': datetime.datetime(2015, 11, 26, 7),
        'foo': {'x': 1, 'y': 2} }


