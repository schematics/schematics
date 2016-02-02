import pytest

from schematics.models import Model
from schematics.types import StringType, IntType
from schematics.validate import validate


class Foo(Model):
    s = StringType()
    i = IntType()

data = {'s': 'schematics', 'i': 42}

@pytest.mark.benchmark(group='validation')
def test_bench_validate_dictionary(benchmark):
    benchmark(validate, Foo, data)

@pytest.mark.benchmark(group='validation')
def test_bench_validate_model(benchmark):
    benchmark(Foo, data, validate=True)

