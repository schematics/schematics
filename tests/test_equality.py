import mock

from schematics.models import Model


class TestModel(Model):
    pass


def test_equality_against_mock_any():
    assert TestModel() == mock.ANY
