from schematics.models import Model
from schematics.types import StringType, IntType
from schematics.validate import validate


class Foo(Model):
    s = StringType()
    i = IntType()

data = {'s': 'schematics', 'i': 42}


if __name__ == '__main__':
    for i in xrange(10000):
        validate(Foo, data)
    for i in xrange(10000):
        Foo(trusted_data=data, validate=True)

