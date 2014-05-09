from schematics.exceptions import BaseError, ValidationError


def test_clean_messages():
    err = BaseError(None)

    assert err.clean_messages({'foo': 'bar'}) == {'foo': 'bar'}
    assert err.clean_messages({'foo': ValidationError('bar')}) == {'foo': ['bar']}
    assert err.clean_messages(['foo']) == ['foo']
    assert err.clean_messages([ValidationError('bar')]) == [['bar']]
