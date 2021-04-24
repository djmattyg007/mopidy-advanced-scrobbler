from unittest import mock

import pytest

from mopidy_advanced_scrobbler import frontend as frontend_lib
from mopidy_advanced_scrobbler._service import Service

from ._utils import path_to_data_dir


@pytest.fixture
def db_mock():
    with mock.patch("mopidy_advanced_scrobbler.frontend.db_service", spec=Service) as m:
        yield m


@pytest.fixture
def network_mock():
    with mock.patch("mopidy_advanced_scrobbler.frontend.network_service", spec=Service) as m:
        yield m


@pytest.fixture
def frontend():
    core_config = {"data_dir": path_to_data_dir("")}
    ext_config = {
        "api_key": "api_key",
        "api_secret": "api_secret",
        "username": "djmattyg007",
        "password": "secret_password",
    }

    config = {"core": core_config, "advanced_scrobbler": ext_config}
    core = mock.sentinel.core
    return frontend_lib.AdvancedScrobblerFrontend(config, core)


def test_on_start_starts_services(frontend, db_mock, network_mock):
    frontend.on_start()

    db_mock.start_service.assert_called_once()
    network_mock.start_service.assert_called_once()
