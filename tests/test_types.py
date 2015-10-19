import datetime
import decimal
import uuid

import pytest

from schematics.types import (
    BaseType, StringType, DateTimeType, DateType, IntType, EmailType, LongType,
    URLType, MultilingualStringType, UUIDType, IPv4Type, MD5Type, BooleanType,
    GeoPointType, FloatType, DecimalType, force_unicode
)
from schematics.types.base import get_range_endpoints
from schematics.exceptions import (
    ValidationError, ConversionError, MockCreationError
)


def test_string_choices():
    with pytest.raises(TypeError):
        BaseType(choices='foo')

def test_int():
    with pytest.raises(ConversionError):
        IntType().validate('foo')

    assert IntType.validate(5001) == None


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
    with pytest.raises(ConversionError):
        IntType()('a')
    assert IntType()(1) == 1


def test_custom_validation_functions():
    class UppercaseType(BaseType):

        def validate_uppercase(self, value):
            if value.upper() != value:
                raise ValidationError("Value must be uppercase!")

    field = UppercaseType()

    with pytest.raises(ValidationError):
        field.validate("lowercase")


def test_custom_validation_function_and_inheritance():
    class UppercaseType(StringType):

        def validate_uppercase(self, value):
            if value.upper() != value:
                raise ValidationError("Value must be uppercase!")

    class MUppercaseType(UppercaseType):

        def __init__(self, number_of_m_chars, **kwargs):
            self.number_of_m_chars = number_of_m_chars

            super(MUppercaseType, self).__init__(**kwargs)

        def validate_contains_m_chars(self, value):
            if value.count("M") != self.number_of_m_chars:
                raise ValidationError(
                    "Value must contain {0} 'm' characters".format(self.number_of_m_chars))

    field = MUppercaseType(number_of_m_chars=3)

    field.validate("MMM")

    with pytest.raises(ValidationError):
        field.validate("mmm")

    with pytest.raises(ValidationError):
        field.validate("MM")


def test_email_type_with_invalid_email():
    with pytest.raises(ValidationError):
        EmailType().validate(u'sdfg\U0001f636\U0001f46e')


def test_url_type_with_invalid_url():
    with pytest.raises(ValidationError):
        URLType().validate(u'http:example.com')


def test_url_type_with_unreachable_url():
    with pytest.raises(ValidationError):
        URLType(verify_exists=True).validate_url('http://127.0.0.1:99999/')


def test_string_type_required():
    field = StringType(required=True)
    with pytest.raises(ValidationError):
        field.validate(None)


def test_string_type_accepts_none():
    field = StringType()
    field.validate(None)


def test_string_required_accepts_empty_string():
    field = StringType(required=True)
    field.validate('')


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


def test_string_max_length_is_enforced():
    with pytest.raises(ValidationError):
        StringType(max_length=2).validate_length('foo')


def test_multilingualstring_should_only_take_certain_types():
    mls = MultilingualStringType()

    mls(None)
    mls({})

    with pytest.raises(ValueError):
        mls(123)

    with pytest.raises(ValueError):
        mls([])

    with pytest.raises(ValueError):
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
        context={'locale': 'fr_FR'}) == 'serpent'


def test_multilingual_string_should_require_a_locale():
    mls = MultilingualStringType()

    with pytest.raises(ConversionError):
        mls.to_primitive({'foo': 'bar'})


def test_multilingual_string_without_matching_locale_should_explode():
    mls = MultilingualStringType()

    with pytest.raises(ConversionError):
        mls.to_primitive({'fr_FR': 'serpent'})

    with pytest.raises(ConversionError):
        mls.to_primitive({'en_US': 'snake'}, context={'locale': 'fr_FR'})


def test_multilingual_string_should_accept_lists_of_locales():
    strings = {
        'en_US': 'snake',
        'fr_FR': 'serpent',
        'es_MX': 'serpiente',
    }

    mls = MultilingualStringType(default_locale=['foo', 'fr_FR', 'es_MX'])

    assert mls.to_primitive(strings) == 'serpent'
    assert mls.to_primitive(strings, context={'locale': ['es_MX', 'bar']}) == 'serpiente'

    mls = MultilingualStringType()

    assert mls.to_primitive(strings, context={'locale': ['foo', 'es_MX', 'fr_FR']}) == 'serpiente'


def test_boolean_to_native():
    bool_field = BooleanType()

    for true_value in ['True', '1', 1, True]:
        assert bool_field.to_native(true_value)

    for false_value in ['False', '0', 0, False]:
        assert not bool_field.to_native(false_value)

    for bad_value in ['TrUe', 'foo', 2, None, 1.0]:
        with pytest.raises(ConversionError):
            bool_field.to_native(bad_value)
