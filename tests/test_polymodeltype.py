import pytest

from schematics.models import Model
from schematics.types import StringType
from schematics.types.compound import PolyModelType


class A(Model): # fallback model (doesn't define a claim method)
    stringA = StringType()

class Aaa(A):
    pass

class B(A):
    stringB = StringType()
    @classmethod
    def _claim_polymorphic(cls, data):
        return data.get('stringB') == 'bbb'

class C(B):
    stringC = StringType()
    @classmethod
    def _claim_polymorphic(cls, data):
        return data.get('stringC') == 'ccc'

class X(Model):
    pass

def claim_func(field, data):
    if 'stringB' in data and field.name == 'cfn':
        return B
    if 'stringC' in data and field.name == 'cfn':
        return C
    else:
        return None


class Foo(Model):
    base   = PolyModelType(A)       # accepts any subclass for import and export
    strict = PolyModelType([A, B])  # accepts [A, B] for import and export
    nfb    = PolyModelType([B, C])  # no fallback since A not present
    cfn    = PolyModelType([B, C], claim_function=claim_func, strict=False)


def test_subclass_registry():

    assert A._subclasses == [Aaa, B, C]
    assert B._subclasses == [C]
    assert C._subclasses == []

def test_inheritance_based_polymorphic(): # base

    foo = Foo({'base': {'stringB': 'bbb'}})
    assert type(foo.base) is B

    foo = Foo({'base': {'stringC': 'ccc'}})
    assert type(foo.base) is C

    foo = Foo({'base': {}}) # unrecognizable input => fall back to A
    assert type(foo.base) is A

    foo = Foo({'base': Aaa()})
    assert type(foo.base) is Aaa
    foo.validate()
    foo.to_primitive()

def test_enumerated_polymorphic(): # strict

    foo = Foo({'strict': {'stringB': 'bbb'}})
    assert type(foo.strict) is B

    foo = Foo({'strict': {}}) # unrecognizable input => fall back to A
    assert type(foo.strict) is A

    foo = Foo({'strict': B()})
    assert type(foo.strict) is B
    foo.validate()
    foo.to_primitive()

    Foo.strict.allow_subclasses = True
    foo = Foo({'strict': Aaa()})
    Foo.strict.allow_subclasses = False

def test_external_claim_function(): # cfn

    foo = Foo({'cfn': {'stringB': 'bbb', 'stringC': 'ccc'}})
    assert type(foo.cfn) is B

def test_multiple_matches():

    with pytest.raises(Exception):
        foo = Foo({'base': {'stringB': 'bbb', 'stringC': 'ccc'}})

def test_no_fallback(): # nfb

    with pytest.raises(Exception):
        foo = Foo({'nfb': {}})

def test_refuse_unrelated_import():

    with pytest.raises(Exception):
        foo = Foo({'base': D()})

    with pytest.raises(Exception):
        foo = Foo({'strict': Aaa()})

def test_refuse_unrelated_export():

    with pytest.raises(Exception):
        foo = Foo()
        foo.base = X()
        foo.to_primitive()

    with pytest.raises(Exception):
        foo = Foo()
        foo.strict = Aaa()
        foo.to_primitive()

