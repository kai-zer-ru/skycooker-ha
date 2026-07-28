# Тесты для модуля entity_base.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.entity_base import SkyCookerEntity


def test_entity_base_initialization():
    """Тест инициализации базового класса сущности."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    assert entity.hass == mock_hass
    assert entity.entry == mock_entry


@pytest.mark.asyncio
async def test_async_added_to_hass():
    """Тест добавления сущности в hass."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    with patch.object(entity, 'update', new_callable=MagicMock) as mock_update:
        with patch('custom_components.skycooker.entity_base.async_dispatcher_connect', new_callable=MagicMock):
            await entity.async_added_to_hass()
    
    mock_update.assert_called_once()


def test_update():
    """Тест обновления сущности."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    with patch.object(entity, 'schedule_update_ha_state', new_callable=MagicMock) as mock_schedule_update_ha_state:
        entity.update()
    
    mock_schedule_update_ha_state.assert_called_once()


def test_skycooker_property():
    """Тест свойства skycooker."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = 'test_entry_id'
    mock_hass.data = {
        'skycooker': {
            'test_entry_id': {
                'connection': MagicMock()
            }
        }
    }
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    assert entity.skycooker == mock_hass.data['skycooker']['test_entry_id']['connection']


def test_device_info_property():
    """Тест свойства device_info."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_hass.data = {
        'skycooker': {
            'device_info': MagicMock()
        }
    }
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    assert entity.device_info == mock_hass.data['skycooker']['device_info']()


def test_should_poll_property():
    """Тест свойства should_poll."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    assert entity.should_poll is False


def test_assumed_state_property():
    """Тест свойства assumed_state."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    assert entity.assumed_state is False


def test_available_property():
    """Тест свойства available."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = 'test_entry_id'
    mock_hass.data = {
        'skycooker': {
            'test_entry_id': {
                'connection': MagicMock()
            }
        }
    }
    mock_hass.data['skycooker']['test_entry_id']['connection'].available = True
    
    entity = SkyCookerEntity(mock_hass, mock_entry)
    
    assert entity.available is True
