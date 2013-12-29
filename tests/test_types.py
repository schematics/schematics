import contextlib
import datetime
import decimal

import pytest

from schematics.types import (
    BaseType, StringType, DateTimeType, DateType, IntType, EmailType, LongType,
    URLType, PrimitiveType, SimplePrimitiveType
)
from schematics.exceptions import ValidationError, ConversionError


@contextlib.contextmanager
def does_not_raise(ExceptionClass):
    try:
        yield
    except ExceptionClass:
        assert False, u'{0} was raised'.format(ExceptionClass.__name__)


def test_primitive_to_primitive():
    field = PrimitiveType()
    data = {'attr': [1.0, 'a', False, None]}
    primitive = field.to_primitive(data)
    assert data == primitive


def test_primitive_tuple_to_primitive():
    field = PrimitiveType()
    primitive = field.to_primitive((1, 2))
    assert [1, 2] == primitive


def test_primitive_list_to_primitive():
    field = PrimitiveType()
    primitive = field.to_primitive([decimal.Decimal('3.14')])
    assert [u'3.14'] == primitive


def test_primitive_dict_to_primitive():
    field = PrimitiveType()
    primitive = field.to_primitive({'a': decimal.Decimal('3.14')})
    assert {'a': u'3.14'} == primitive


def test_primitive_custom_to_primitive():
    class PrimitiveWithDateType(PrimitiveType):
        def date_to_primitive(self, value):
            return value.isoformat()

    d = datetime.date.today()
    primitive = PrimitiveWithDateType().to_primitive(d)
    assert d.isoformat() == primitive


def test_primitive_default_to_primitive():
    field = PrimitiveType()
    primitive = field.to_primitive(decimal.Decimal('3.14'))
    assert u'3.14' == primitive


def test_primitive_validate_list_elements():
    field = PrimitiveType()
    with pytest.raises(ValidationError):
        field.validate([datetime.date.today()])


def test_primitive_validate_dict_values():
    field = PrimitiveType()
    with pytest.raises(ValidationError):
        field.validate({'a': datetime.date.today()})


def test_primitive_validate_type():
    field = PrimitiveType()
    with pytest.raises(ValidationError):
        field.validate(object())
    with pytest.raises(ValidationError):
        field.validate(())

    with does_not_raise(ValidationError):
        field.validate([])
    with does_not_raise(ValidationError):
        field.validate({})
    with does_not_raise(ValidationError):
        field.validate(None)
    with does_not_raise(ValidationError):
        field.validate(1)
    with does_not_raise(ValidationError):
        field.validate(3.14159)
    with does_not_raise(ValidationError):
        field.validate(True)
    with does_not_raise(ValidationError):
        field.validate("aString")
    


def test_simple_primitive_validate_type():
    field = SimplePrimitiveType()
    with pytest.raises(ValidationError):
        field.validate([])
    with pytest.raises(ValidationError):
        field.validate({})
    with pytest.raises(ValidationError):
        field.validate(())

    with does_not_raise(ValidationError):
        field.validate(None)
    with does_not_raise(ValidationError):
        field.validate(1)
    with does_not_raise(ValidationError):
        field.validate(3.14159)
    with does_not_raise(ValidationError):
        field.validate(True)
    with does_not_raise(ValidationError):
        field.validate("aString")


def test_date():
    today = datetime.date(2013, 3, 1)

    date_type = DateType()
    assert date_type("2013-03-01") == today

    assert date_type.to_primitive(today) == "2013-03-01"


def test_datetime():
    dt = datetime.datetime.now()
    assert DateTimeType()(dt.isoformat()) == dt


def test_datetime_format():
    dt_input = '2013.03.07 15:31'
    dt = datetime.datetime(2013, 3, 7, 15, 31)
    assert DateTimeType(formats=['%Y.%m.%d %H:%M'])(dt_input) == dt


def test_datetime_primitive():
    output = '2013.03.07 15:31'
    dt = datetime.datetime(2013, 3, 7, 15, 31)
    dt_type = DateTimeType(serialized_format='%Y.%m.%d %H:%M')
    assert dt_type(dt.isoformat()) == dt
    assert dt_type.to_primitive(dt) == output


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
                raise ValidationError("Value must contain {0} 'm' characters".format(self.number_of_m_chars))

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


