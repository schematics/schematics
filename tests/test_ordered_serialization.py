# -*- coding: utf-8 -*-
from schematics.datastructures import OrderedDict
from schematics.models import Model
from schematics.types import StringType, IntType


def test_serialize_field_orders_one_two_three():
    class Example(Model):
        one = StringType()
        two = IntType()
        three = StringType()

        class Options:
            fields_order = ['one', 'two', 'three']

    p1 = Example({'one': 'a', 'two': 2, 'three': '3'})
    order = [('one', 'a'), ('two', 2), ('three', '3')]
    serialized = p1.to_native()
    assert serialized.items() == order


def test_serialize_field_orders_three_two_one():
    class Example(Model):
        one = StringType()
        two = IntType()
        three = StringType()

        class Options:
            fields_order = ['three', 'two', 'one']

    p1 = Example({'one': 'a', 'two': 2, 'three': '3'})
    serialized = p1.to_native()
    order = [('three', '3'), ('two', 2), ('one', 'a')]
    assert serialized.items() == order


def test_serialize_field_orders_one_three_two():
    class Example(Model):
        one = StringType()
        two = IntType()
        three = StringType()

        class Options:
            fields_order = ['one', 'three', 'two']

    p1 = Example({'one': 'a', 'two': 2, 'three': '3'})
    serialized = p1.to_native()
    order = [('one', 'a'), ('three', '3'), ('two', 2)]
    assert serialized.items() == order
