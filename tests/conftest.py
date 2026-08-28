# Фикстуры для тестов
import os
import sys
from unittest.mock import MagicMock

# Импорт из корня проекта, а не из tests/custom_components
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# HA 2026.6+: импорт bluetooth тянет usb → serialx → aioesphomeapi (конфликт zeroconf с HA).
# Для unit-тестов достаточно заглушки — реальный BLE-стек не используется.
_bluetooth_stub = MagicMock()
_bluetooth_stub.async_ble_device_from_address = MagicMock(return_value=None)
_bluetooth_stub.async_get_scanner = MagicMock(return_value=MagicMock())
sys.modules.setdefault("homeassistant.components.bluetooth", _bluetooth_stub)

import pytest
from custom_components.skycooker.skycooker_connection import SkyCookerConnection
from custom_components.skycooker.skycooker_cooking_controller import SkyCookerCookingController


@pytest.fixture
def mock_hass():
    """Фикстура для mock Home Assistant."""
    return MagicMock()


@pytest.fixture
def mock_connection(mock_hass):
    """Фикстура для создания mock-соединения с Skycooker."""
    return SkyCookerConnection(
        mac="00:00:00:00:00:00",
        key=b"test_key",
        model_name="RMC-M40S",
        hass=mock_hass,
    )


@pytest.fixture
def mock_cooking_controller(mock_connection):
    """Фикстура для создания mock-контроллера приготовления."""
    return SkyCookerCookingController(mock_connection.connection_manager)
