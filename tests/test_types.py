# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal
from fractions import Fraction
import random
import sys
import uuid

import pytest

from schematics.datastructures import Context
from schematics.models import Model
from schematics.types import *
from schematics.types.compound import *
from schematics.types.base import get_range_endpoints
from schematics.exceptions import ConversionError, ValidationError, DataError


_uuid = uuid.UUID('3ce85e48-3028-409c-a07c-c8ee3d16d5c4')


def test_type_repr():

    class Bar(Model):
        pass

    class Foo(Model):
        intfield = IntType()
        modelfield = ModelType(Bar)
        listfield = ListType(ListType(StringType))

    assert repr(Foo.intfield) == "<IntType() instance on Foo as 'intfield'>"
    assert repr(Foo.listfield) == "<ListType(ListType) instance on Foo as 'listfield'>"
    assert repr(Foo.listfield.field.field) == "<StringType() instance on Foo>"
    assert repr(Foo.modelfield) == "<ModelType(Bar) instance on Foo as 'modelfield'>"
    assert repr(DateTimeType()) == "<DateTimeType() instance>"


def test_string_choices():
    with pytest.raises(TypeError):
        BaseType(choices='foo')


def test_date():
    today = datetime.date(2013, 3, 1)

    date_type = DateType()
    assert date_type("2013-03-01") == today

    assert date_type.to_primitive(today) == "2013-03-01"

    assert date_type.to_native(today) is today

    with pytest.raises(ConversionError):
        date_type.to_native('foo')


def test_datetime():
    dt = datetime.datetime.now()
    assert DateTimeType()(dt.isoformat()) == dt

    obj = DateTimeType(formats='foo')
    assert obj.formats == ['foo']


def test_datetime_format():
    dt_input = '2013.03.07 15:31'
    dt = datetime.datetime(2013, 3, 7, 15, 31)
    assert DateTimeType(formats=['%Y.%m.%d %H:%M'])(dt_input) == dt


def test_datetime_to_native():
    with pytest.raises(ConversionError):
        DateTimeType().to_native('foo')


def test_datetime_primitive():
    output = '2013.03.07 15:31'
    dt = datetime.datetime(2013, 3, 7, 15, 31)
    dt_type = DateTimeType(serialized_format='%Y.%m.%d %H:%M')
    assert dt_type(dt.isoformat()) == dt
    assert dt_type.to_primitive(dt) == output

    obj = DateTimeType(serialized_format=str)
    assert obj.to_primitive(123) == '123'


def test_datetime_accepts_datetime():
    output = '2013.03.07 15:31'
    dt = datetime.datetime(2013, 3, 7, 15, 31)
    dt_type = DateTimeType(serialized_format='%Y.%m.%d %H:%M')
    assert dt_type(dt) == dt
    assert dt_type.to_primitive(dt) == output


def test_int():
    intfield = IntType()
    i = lambda x: (intfield(x), type(intfield(x)))
    # from int
    assert i(3) == (3, int)
    # from float
    assert i(3.0) == (3, int)
    with pytest.raises(ConversionError):
        i(3.2)
    # from string
    assert i("3") == (3, int)
    with pytest.raises(ConversionError):
        i("3.0")
    with pytest.raises(ConversionError):
        i("a")
    # from decimal
    assert i(Decimal("3")) == (3, int)
    assert i(Decimal("3.0")) == (3, int)
    with pytest.raises(ConversionError):
        i(Decimal("3.2"))
    # from fraction
    assert i(Fraction(30, 10)) == (3, int)
    with pytest.raises(ConversionError):
        i(Fraction(7, 2))
    # from uuid
    with pytest.raises(ConversionError):
        i(_uuid)


def test_int_strict():
    intfield = IntType(strict=True)
    i = lambda x: (intfield(x), type(intfield(x)))
    # from int
    assert i(3) == (3, int)
    # from float
    with pytest.raises(ConversionError):
        i(3.0)
    # from string
    assert i("3") == (3, int)
    with pytest.raises(ConversionError):
        i("3.0")
    # from decimal
    with pytest.raises(ConversionError):
        assert i(Decimal("3")) == (3, int)
    with pytest.raises(ConversionError):
        assert i(Decimal("3.0")) == (3, int)
    # from fraction
    with pytest.raises(ConversionError):
        assert i(Fraction(30, 10)) == (3, int)
    # from uuid
    with pytest.raises(ConversionError):
        i(_uuid)


def test_float():
    floatfield = FloatType()
    f = lambda x: (floatfield(x), type(floatfield(x)))
    # from int
    assert f(3) == (3.0, float)
    # from float
    assert f(3.2) == (3.2, float)
    # from string
    assert f("3") == (3.0, float)
    assert f("3.2") == (3.2, float)
    assert f("3.210987e6") == (3210987, float)
    with pytest.raises(ConversionError):
        f("a")
    # from decimal
    assert f(Decimal("3")) == (3.0, float)
    assert f(Decimal("3.2")) == (3.2, float)
    # from fraction
    assert f(Fraction(7, 2)) == (3.5, float)
    # from uuid
    with pytest.raises(ConversionError):
        f(_uuid)


def test_int_validation():
    with pytest.raises(ConversionError):
        IntType().validate('foo')
    assert IntType().validate(5001) == 5001


def test_custom_validation_functions():
    class UppercaseType(BaseType):

        def validate_uppercase(self, value, context=None):
            if value.upper() != value:
                raise ValidationError("Value must be uppercase!")

        def validate_without_context(self, value):
            pass

    field = UppercaseType()

    field.validate("UPPERCASE")

    with pytest.raises(ValidationError):
        field.validate("lowercase")


def test_custom_validation_function_and_inheritance():
    class UppercaseType(StringType):

        def validate_uppercase(self, value, context=None):
            if value.upper() != value:
                raise ValidationError("Value must be uppercase!")

    class MUppercaseType(UppercaseType):

        def __init__(self, number_of_m_chars, **kwargs):
            self.number_of_m_chars = number_of_m_chars

            super(MUppercaseType, self).__init__(**kwargs)

        def validate_contains_m_chars(self, value, context=None):
            if value.count("M") != self.number_of_m_chars:
                raise ValidationError(
                    "Value must contain {0} 'm' characters".format(self.number_of_m_chars))

    field = MUppercaseType(number_of_m_chars=3)

    field.validate("MMM")

    with pytest.raises(ValidationError):
        field.validate("mmm")

    with pytest.raises(ValidationError):
        field.validate("MM")


def test_string_type_required():
    class M(Model):
        field = StringType(required=True)
    with pytest.raises(DataError):
        M({'field': None}).validate()


def test_string_type_accepts_none():
    class M(Model):
        field = StringType()
    M({'field': None}).validate()


def test_string_required_accepts_empty_string():
    class M(Model):
        field = StringType()
    M({'field': ''}).validate()


def test_string_min_length_doesnt_accept_empty_string():
    field = StringType(min_length=1)
    with pytest.raises(ValidationError):
        field.validate('')


def test_string_regex():
    StringType(regex='\d+').validate("1")

    with pytest.raises(ValidationError):
        StringType(regex='\d+').validate("a")


def test_string_to_native():

    with pytest.raises(ConversionError):
        StringType().to_native(3.14)
    with pytest.raises(ConversionError):
        StringType().to_native(b'\xE0\xA0') # invalid UTF-8 sequence

    if sys.version_info[0] == 2:
        assert StringType().to_native(u'abc éíçßµ') == u'abc éíçßµ'
        assert StringType().to_native('\xC3\xA4') == u'ä'
    else:
        assert StringType().to_native('abc éíçßµ') == 'abc éíçßµ'
        assert StringType().to_native(b'\xC3\xA4') == 'ä'


def test_string_max_length_is_enforced():
    with pytest.raises(ValidationError):
        StringType(max_length=2).validate_length('foo')


def test_multilingualstring_should_only_take_certain_types():
    mls = MultilingualStringType()

    mls(None)
    mls({})

    with pytest.raises(ConversionError):
        mls(123)

    with pytest.raises(ConversionError):
        mls([])

    with pytest.raises(ConversionError):
        mls('foo')


def test_multilingualstring_should_validate_length():
    MultilingualStringType(min_length=3).validate({'en_US': 'foo'})
    MultilingualStringType(max_length=3).validate({'en_US': 'foo'})

    with pytest.raises(ValidationError):
        MultilingualStringType(min_length=4).validate({'en_US': 'foo'})

    with pytest.raises(ValidationError):
        MultilingualStringType(max_length=2).validate({'en_US': 'foo'})


def test_multilingualstring_should_validate_regex():
    MultilingualStringType(regex='^[a-z]*$').validate({'en_US': 'foo'})

    with pytest.raises(ValidationError):
        MultilingualStringType(regex='^[a-z]*$').validate({'en_US': '123'})

    with pytest.raises(ValidationError):
        MultilingualStringType(locale_regex='^\d*$').validate({'en_US': 'foo'})

    assert MultilingualStringType(locale_regex=None).validate_regex({'en_US': 'foo'}) is None


def test_multilingualstring_should_handle_none():
    mls = MultilingualStringType(default_locale='en_US')

    assert mls.to_primitive(None) is None


def test_multilingualstring_should_handle_castable_values():
    mls = MultilingualStringType(default_locale='en_US')

    assert mls.to_primitive({'en_US': 123}) == u'123'


def test_multilingualstring_should_enforce_noncastable_values():
    mls = MultilingualStringType(default_locale='en_US')

    with pytest.raises(ConversionError):
        mls.to_primitive({'en_US': 123.0}) == u'123'


def test_multilingual_string_should_emit_string_with_default_locale():
    mls = MultilingualStringType(default_locale='en_US')

    assert mls.to_primitive({'en_US': 'snake', 'fr_FR': 'serpent'}) == 'snake'


def test_multilingual_string_should_emit_string_with_explicit_locale():
    mls = MultilingualStringType(default_locale='en_US')

    assert mls.to_primitive(
        {'en_US': 'snake', 'fr_FR': 'serpent'},
        context=Context(app_data={'locale': 'fr_FR'})) == 'serpent'


def test_multilingual_string_should_require_a_locale():
    mls = MultilingualStringType()

    with pytest.raises(ConversionError):
        mls.to_primitive({'foo': 'bar'})


def test_multilingual_string_without_matching_locale_should_explode():
    mls = MultilingualStringType()

    with pytest.raises(ConversionError):
        mls.to_primitive({'fr_FR': 'serpent'})

    with pytest.raises(ConversionError):
        mls.to_primitive({'en_US': 'snake'}, context=Context(app_data={'locale': 'fr_FR'}))


def test_multilingual_string_should_accept_lists_of_locales():
    strings = {
        'en_US': 'snake',
        'fr_FR': 'serpent',
        'es_MX': 'serpiente',
    }

    mls = MultilingualStringType(default_locale=['foo', 'fr_FR', 'es_MX'])

    assert mls.to_primitive(strings) == 'serpent'
    assert mls.to_primitive(strings, context=Context(app_data={'locale': ['es_MX', 'bar']})) == 'serpiente'

    mls = MultilingualStringType()

    assert mls.to_primitive(strings, context=Context(app_data={'locale': ['foo', 'es_MX', 'fr_FR']})) == 'serpiente'


def test_boolean_to_native():
    bool_field = BooleanType()

    for true_value in ['True', '1', 1, True]:
        assert bool_field.to_native(true_value)

    for false_value in ['False', '0', 0, False]:
        assert not bool_field.to_native(false_value)

    for bad_value in ['TrUe', 'foo', 2, None, 1.0]:
        with pytest.raises(ConversionError):
            bool_field.to_native(bad_value)


def test_geopoint_mock():
    geo = GeoPointType(required=True)
    geo_point = geo.mock()
    assert geo_point[0] >= -90
    assert geo_point[0] <= 90
    assert geo_point[1] >= -180
    assert geo_point[1] <= 180


def test_geopoint_to_native():
    geo = GeoPointType(required=True)

    with pytest.raises(ConversionError):
        native = geo.to_native((10,))

    with pytest.raises(ConversionError):
        native = geo.to_native({'1':'-20', '2': '18'})

    with pytest.raises(ConversionError):
        native = geo.to_native(['-20',  '18'])

    with pytest.raises(ConversionError):
        native = geo.to_native('-20, 18')

    class Point(object):

        def __len__(self):
            return 2

    with pytest.raises(ConversionError):
        native = geo.to_native(Point())

    native = geo.to_native([89, -12])
    assert native == [89, -12]

    latitude = random.uniform(-90, 90)
    longitude = random.uniform(-180, 180)
    point = [latitude, longitude]

    native = geo.to_native(point)
    assert native == point


def test_geopoint_range():
    geo = GeoPointType(required=True)

    with pytest.raises(ValidationError) as ve:
        geo.validate((-91, 110))

    with pytest.raises(ValidationError) as ve:
        geo.validate((90.12345, 65))

    with pytest.raises(ValidationError) as ve:
        geo.validate((23, -181))

    with pytest.raises(ValidationError) as ve:
        geo.validate((28.2342323, 181.123141))

def test_metadata():
    metadata = {'description': 'amazing', 'extra': {'abc': 1}}
    assert StringType(metadata=metadata).metadata == metadata
    assert StringType().metadata == {}
