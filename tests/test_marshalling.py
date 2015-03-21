# -*- coding: utf-8 -*-
import pytest

from schematics.exceptions import ModelConversionError
from schematics.models import Model
from schematics.types import StringType, LongType, IntType, MD5Type
from schematics.types.compound import ModelType, DictType, ListType
from schematics.types.serializable import serializable
from schematics.transforms import blacklist, whitelist, wholelist, export_loop

import six
from six import iteritems
try:
    unicode #PY2
except:
    import codecs
    unicode = str #PY3


def test_marshaller():

    class Person(Model):

        first_name = StringType()
        last_name = StringType()
        testfield = StringType(default='aaa')

        def marshal(cls, data):
            del data['testfield']

        def marshal_full_name(cls, data):
            new_data = {
                'full_name': '%s %s' % (data['first_name'], data['last_name'])
            }
            return (new_data, ('first_name', 'last_name'))

        def unmarshal_full_name(cls, data):
            if 'full_name' not in data:
                raise ModelConversionError("Field 'full_name' missing") 
            first_name, last_name = data['full_name'].split()
            new_data = {
                'first_name': first_name, 
                'last_name': last_name
            }
            return (new_data, ('full_name',))

    with pytest.raises(ModelConversionError):
        person = Person()

    person = Person({'full_name': 'First Last'})
    assert person._data == dict(first_name='First', last_name='Last', testfield='aaa')

    person.validate()

    assert person.to_primitive() == dict(full_name='First Last')

