from unittest import mock

from mopidy_advanced_scrobbler import Extension


def test_setup():
    ext = Extension()
    registry = mock.Mock()

    ext.setup(registry)

    assert registry.add.call_count == 2

    mock_calls = registry.add.mock_calls
    assert len(mock_calls) == 2

    call1 = mock_calls[0]
    assert call1.args[0] == "frontend"

    call2 = mock_calls[1]
    assert call2.args[0] == "http:app"
