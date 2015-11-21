import mock

from schematics.models import Model


def test_equality_against_mock_any():

    class TestModel(Model):
        pass

    assert TestModel() == mock.ANY

