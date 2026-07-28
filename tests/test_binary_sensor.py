import pytest
from unittest.mock import MagicMock

from custom_components.skycooker.binary_sensor import (
    SkyCookerBinarySensor,
    async_setup_entry,
)
from custom_components.skycooker.const import (
    DOMAIN,
    DATA_CONNECTION,
    BINARY_SENSOR_TYPE_COOKING,
    BINARY_SENSOR_TYPE_AUTO_WARM_ACTIVE,
    BINARY_SENSOR_TYPE_DELAYED_START_ACTIVE,
)


@pytest.mark.asyncio
async def test_binary_sensor_async_setup_entry():
    """Тест настройки бинарных сенсоров."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_hass.data = {
        DOMAIN: {
            mock_entry.entry_id: {
                DATA_CONNECTION: mock_skycooker,
            }
        }
    }

    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    # 3 бинарных сенсора
    assert len(entities) == 3
    types = {e.sensor_type for e in entities}
    assert types == {
        BINARY_SENSOR_TYPE_COOKING,
        BINARY_SENSOR_TYPE_AUTO_WARM_ACTIVE,
        BINARY_SENSOR_TYPE_DELAYED_START_ACTIVE,
    }


def test_binary_sensor_states():
    """Тест состояний бинарных сенсоров."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"

    mock_skycooker = MagicMock()
    mock_skycooker.is_cooking = True
    mock_skycooker.is_auto_warm_active = False
    mock_skycooker.is_delayed_start_active = True

    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker,
            }
        }
    }

    cooking = SkyCookerBinarySensor(mock_hass, mock_entry, BINARY_SENSOR_TYPE_COOKING)
    auto_warm = SkyCookerBinarySensor(
        mock_hass, mock_entry, BINARY_SENSOR_TYPE_AUTO_WARM_ACTIVE
    )
    delayed = SkyCookerBinarySensor(
        mock_hass, mock_entry, BINARY_SENSOR_TYPE_DELAYED_START_ACTIVE
    )

    assert cooking.is_on is True
    assert auto_warm.is_on is False
    assert delayed.is_on is True

