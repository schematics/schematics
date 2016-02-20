# -*- coding: utf-8 -*-

import pytest

from schematics.exceptions import *


def test_error_from_string():

    e = ConversionError('hello')
    assert e.messages == ['hello']

    e = ValidationError('hello', 'world', '!')
    assert e.messages == ['hello', 'world', '!']
    assert len(e) == 3


def _assert(e):
    assert e.messages == ['hello'] and e.messages[0].info == 99


def test_error_from_args():
    _assert(ValidationError('hello', info=99))


def test_error_from_tuple():
    _assert(ValidationError(('hello', 99)))


def test_error_from_tuple():
    msg = ErrorMessage('hello', info=99)
    _assert(ValidationError(msg))


def test_error_from_error():
    e = ValidationError('hello', info=99)
    _assert(ValidationError(e))


def test_error_from_mixed_args():

    e = ValidationError(
            ('hello', 99),
            'world',
            ErrorMessage('from_msg', info=0),
            ValidationError('from_err', info=1))

    assert e == e.messages == ['hello', 'world', 'from_msg', 'from_err']
    assert [msg.info for msg in e] == [99, None, 0, 1]


def test_error_from_mixed_list():

    e = ConversionError([
            ('hello', 99),
            'world',
            ErrorMessage('from_msg', info=0),
            ConversionError('from_err', info=1)])

    assert e.messages == ['hello', 'world', 'from_msg', 'from_err']
    assert [msg.info for msg in e.messages] == [99, None, 0, 1]


def test_error_repr():

    assert str(ValidationError('foo')) == 'ValidationError("foo")'

    e = ValidationError(
            ('foo', None),
            ('bar', 98),
            ('baz', [1, 2, 3]))

    assert str(e) == 'ValidationError(["foo", ("bar", 98), ("baz", <\'list\' object>)])'

    e = ValidationError(u'é')
    assert str(e) == repr(e)


def test_error_message_object():

    assert ErrorMessage('foo') == 'foo'
    assert ErrorMessage('foo') != 'bar'
    assert ErrorMessage('foo', 1) == ErrorMessage('foo', 1)
    assert ErrorMessage('foo', 1) != ErrorMessage('foo', 2)


def test_error_failures():

    with pytest.raises(NotImplementedError):
        FieldError()

    with pytest.raises(TypeError):
        ValidationError()

    with pytest.raises(TypeError):
        ValidationError('hello', 99)

    with pytest.raises(TypeError):
        ConversionError(ValidationError('hello'))

    with pytest.raises(TypeError):
        CompoundError(['hello'])

