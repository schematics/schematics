import pytest

from schematics.types.compound import MultiType


def test_base_does_not_implement_export_loop():
    with pytest.raises(NotImplementedError):
        MultiType().export_loop(None, None)
