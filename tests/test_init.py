# Тесты для модуля __init__.py
import pytest
from datetime import timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
    device_info,
    entry_update_listener,
    load_translations,
    _create_poll_scheduler,
    _ensure_services_registered,
)
from custom_components.skycooker.const import DOMAIN, DATA_CONNECTION


class MockServices:
    """Простая реализация регистратора сервисов для тестов."""

    def __init__(self):
        self.handlers = {}

    def async_register(self, domain, service, handler):
        self.handlers[(domain, service)] = handler

    async def async_call(self, domain, service, data=None):
        handler = self.handlers[(domain, service)]
        call = MagicMock()
        call.data = data or {}
        await handler(call)


@pytest.mark.asyncio
async def test_async_setup_success():
    """Тест успешной настройки компонента."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_config = {}
    
    with patch('custom_components.skycooker.HA_VERSION', '2025.12.6'):
        result = await async_setup(mock_hass, mock_config)
    
    assert result is True
    assert 'skycooker' in mock_hass.data


@pytest.mark.asyncio
async def test_async_setup_failure():
    """Тест неудачной настройки компонента."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_config = {}
    
    with patch('custom_components.skycooker.HA_VERSION', '2024.1.1'):
        result = await async_setup(mock_hass, mock_config)
    
    assert result is False


@pytest.mark.asyncio
async def test_async_setup_entry_success():
    """Тест успешной настройки конфигурационного входа."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'RMC-M40S',
        'mac': '00:11:22:33:44:55',
        'password': list(bytes.fromhex('0000000000000000')),
        'persistent_connection': False,
        'scan_interval': 30
    }
    mock_entry.entry_id = 'test_entry_id'
    mock_entry.add_update_listener = MagicMock(return_value=MagicMock())

    with patch('custom_components.skycooker.SkyCookerConnection', new_callable=MagicMock) as mock_connection:
        mock_skycooker = MagicMock()
        mock_skycooker.sw_version = '1.0.0'
        mock_skycooker.update = AsyncMock()
        mock_connection.return_value = mock_skycooker
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()
        
        result = await async_setup_entry(mock_hass, mock_entry)
    
    assert result is True
    assert 'skycooker' in mock_hass.data


@pytest.mark.asyncio
async def test_async_setup_entry_failure():
    """Тест неудачной настройки конфигурационного входа."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'MC-100',
        'mac': '00:11:22:33:44:55',
        'password': 'password',
        'persistent_connection': False,
        'scan_interval': 30
    }
    mock_entry.entry_id = 'test_entry_id'
    
    with patch('custom_components.skycooker.SkyCookerConnection', new_callable=MagicMock) as mock_connection:
        mock_connection.side_effect = Exception('Device not found')
        
        result = await async_setup_entry(mock_hass, mock_entry)
    
    assert result is False


@pytest.mark.asyncio
async def test_async_unload_entry():
    """Тест выгрузки конфигурационного входа."""
    mock_hass = MagicMock()
    mock_hass.data = {
        'skycooker': {
            'test_entry_id': {
                'connection': MagicMock()
            },
            'cancel': MagicMock()
        }
    }
    mock_entry = MagicMock()
    mock_entry.entry_id = 'test_entry_id'
    mock_hass.async_add_executor_job = AsyncMock()
    mock_hass.data['skycooker']['test_entry_id']['connection'].stop = MagicMock()
    mock_hass.config_entries.async_forward_entry_unload = AsyncMock(return_value=None)

    result = await async_unload_entry(mock_hass, mock_entry)

    assert result is True


def test_device_info():
    """Тест получения информации об устройстве."""
    mock_hass = MagicMock()
    mock_hass.data = {
        'skycooker': {
            'test_entry_id': {
                'connection': MagicMock()
            }
        }
    }
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'MC-100',
        'mac': '00:11:22:33:44:55'
    }
    mock_entry.entry_id = 'test_entry_id'
    
    device_info_result = device_info(mock_entry, mock_hass)
    
    assert device_info_result is not None


@pytest.mark.asyncio
async def test_entry_update_listener():
    """Тест обработки обновления опций."""
    mock_connection = MagicMock()
    mock_hass = MagicMock()
    mock_hass.data = {
        'skycooker': {
            'test_entry_id': {
                'connection': mock_connection
            }
        }
    }
    mock_entry = MagicMock()
    mock_entry.data = {
        'persistent_connection': True
    }
    mock_entry.entry_id = 'test_entry_id'
    mock_hass.config_entries.async_reload = AsyncMock()

    await entry_update_listener(mock_hass, mock_entry)

    assert mock_connection.persistent is True
    mock_hass.config_entries.async_reload.assert_called_once_with('test_entry_id')


@pytest.mark.asyncio
async def test_load_translations_ru():
    """Тест загрузки переводов для русского языка."""
    mock_hass = MagicMock()
    mock_hass.config.language = 'ru'
    mock_hass.data = {}

    await load_translations(mock_hass)

    assert 'skycooker_translations' in mock_hass.data
    assert isinstance(mock_hass.data['skycooker_translations'], dict)


@pytest.mark.asyncio
async def test_load_translations_en():
    """Тест загрузки переводов для английского языка."""
    mock_hass = MagicMock()
    mock_hass.config.language = 'en'
    mock_hass.data = {}

    await load_translations(mock_hass)

    assert 'skycooker_translations' in mock_hass.data
    assert isinstance(mock_hass.data['skycooker_translations'], dict)


@pytest.mark.asyncio
async def test_load_translations_unsupported_language():
    """Тест загрузки переводов для неподдерживаемого языка."""
    mock_hass = MagicMock()
    mock_hass.config.language = 'de'
    mock_hass.data = {}

    await load_translations(mock_hass)

    assert 'skycooker_translations' in mock_hass.data


@pytest.mark.asyncio
async def test_load_translations_file_not_found_fallback_success():
    """Тест загрузки переводов: FileNotFoundError для ru, fallback на en.json успешен."""
    mock_hass = MagicMock()
    mock_hass.config.language = 'ru'
    mock_hass.data = {}

    call_count = [0]

    class AsyncContextManager:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def read(self):
            return b'{"program_names": {"standby": "Standby"}}'

    def mock_open_side_effect(filepath, *args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise FileNotFoundError("No such file")
        return AsyncContextManager()

    with patch('custom_components.skycooker.aiofiles.open', side_effect=mock_open_side_effect):
        await load_translations(mock_hass)

    assert 'skycooker_translations' in mock_hass.data
    assert mock_hass.data['skycooker_translations'] == {"program_names": {"standby": "Standby"}}


@pytest.mark.asyncio
async def test_load_translations_file_not_found_fallback_fails():
    """Тест загрузки переводов: FileNotFoundError и ошибка fallback на en.json."""
    mock_hass = MagicMock()
    mock_hass.config.language = 'ru'
    mock_hass.data = {}

    call_count = [0]

    def mock_open_raises(filepath, *args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise FileNotFoundError("No such file")
        raise OSError("Read error")

    with patch('custom_components.skycooker.aiofiles.open', side_effect=mock_open_raises):
        await load_translations(mock_hass)

    assert 'skycooker_translations' in mock_hass.data
    assert mock_hass.data['skycooker_translations'] == {}


@pytest.mark.asyncio
async def test_load_translations_general_exception():
    """Тест загрузки переводов при общей ошибке."""
    mock_hass = MagicMock()
    mock_hass.config.language = 'ru'
    mock_hass.data = {}

    with patch('custom_components.skycooker.aiofiles.open', side_effect=Exception("IO Error")):
        await load_translations(mock_hass)

    assert 'skycooker_translations' in mock_hass.data
    assert mock_hass.data['skycooker_translations'] == {}


@pytest.mark.asyncio
async def test_run_recipe_service_starts_program():
    """Сервис run_recipe настраивает параметры и запускает программу."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.services = MockServices()

    # Регистрируем сервисы
    _ensure_services_registered(mock_hass)

    entry_id = "test_entry_id"
    conn = MagicMock()
    conn.set_target_program = AsyncMock()
    conn.set_temperature = AsyncMock()
    conn.set_boil_time = AsyncMock()
    conn.set_delayed_start = AsyncMock()
    conn.enable_auto_warm = AsyncMock()
    conn.disable_auto_warm = AsyncMock()
    conn.start = AsyncMock()
    conn.start_delayed = AsyncMock()

    mock_hass.data[DOMAIN] = {
        entry_id: {DATA_CONNECTION: conn},
        "services_registered": True,
    }

    await mock_hass.services.async_call(
        DOMAIN,
        "run_recipe",
        {
            "entry_id": entry_id,
            "program_name": "Плов",
            "temperature": 120,
            "main_hours": 1,
            "main_minutes": 20,
            "auto_warm": True,
        },
    )

    conn.set_target_program.assert_awaited_once_with("Плов")
    conn.set_temperature.assert_awaited_once_with(120)
    conn.set_boil_time.assert_awaited_once_with(1, 20)
    conn.enable_auto_warm.assert_awaited_once()
    conn.start.assert_awaited_once()
    conn.start_delayed.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_recipe_service_uses_delayed_start():
    """Сервис run_recipe запускает отложенный старт при указанных delayed_start_*."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.services = MockServices()

    _ensure_services_registered(mock_hass)

    entry_id = "test_entry_id"
    conn = MagicMock()
    conn.set_target_program = AsyncMock()
    conn.set_temperature = AsyncMock()
    conn.set_boil_time = AsyncMock()
    conn.set_delayed_start = AsyncMock()
    conn.enable_auto_warm = AsyncMock()
    conn.disable_auto_warm = AsyncMock()
    conn.start = AsyncMock()
    conn.start_delayed = AsyncMock()

    mock_hass.data[DOMAIN] = {
        entry_id: {DATA_CONNECTION: conn},
        "services_registered": True,
    }

    await mock_hass.services.async_call(
        DOMAIN,
        "run_recipe",
        {
            "entry_id": entry_id,
            "program_name": "Крупы",
            "main_hours": 0,
            "main_minutes": 40,
            "delayed_start_hours": 2,
            "delayed_start_minutes": 0,
        },
    )

    conn.set_target_program.assert_awaited_once_with("Крупы")
    conn.set_boil_time.assert_awaited_once_with(0, 40)
    conn.set_delayed_start.assert_awaited_once_with(2, 0)
    conn.start_delayed.assert_awaited_once()
    conn.start.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_program_service_does_not_start():
    """Сервис set_program не запускает программу, только настраивает цели."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.services = MockServices()

    _ensure_services_registered(mock_hass)

    entry_id = "test_entry_id"
    conn = MagicMock()
    conn.set_target_program = AsyncMock()
    conn.set_temperature = AsyncMock()
    conn.set_boil_time = AsyncMock()
    conn.set_delayed_start = AsyncMock()
    conn.enable_auto_warm = AsyncMock()
    conn.disable_auto_warm = AsyncMock()
    conn.start = AsyncMock()
    conn.start_delayed = AsyncMock()

    mock_hass.data[DOMAIN] = {
        entry_id: {DATA_CONNECTION: conn},
        "services_registered": True,
    }

    await mock_hass.services.async_call(
        DOMAIN,
        "set_program",
        {
            "entry_id": entry_id,
            "program_name": "Мультиповар",
            "temperature": 95,
            "main_hours": 5,
            "main_minutes": 0,
            "additional_hours": 1,
            "additional_minutes": 30,
            "auto_warm": False,
        },
    )

    conn.set_target_program.assert_awaited_once_with("Мультиповар")
    conn.set_temperature.assert_awaited_once_with(95)
    conn.set_boil_time.assert_awaited_once_with(5, 0)
    conn.set_delayed_start.assert_awaited_once_with(1, 30)
    conn.disable_auto_warm.assert_awaited_once()
    conn.start.assert_not_awaited()
    conn.start_delayed.assert_not_awaited()


@pytest.mark.asyncio
async def test_enable_disable_auto_warm_services():
    """Сервисы enable/disable_auto_warm вызывают соответствующие методы соединения."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.services = MockServices()

    _ensure_services_registered(mock_hass)

    entry_id = "test_entry_id"
    conn = MagicMock()
    conn.enable_auto_warm = AsyncMock()
    conn.disable_auto_warm = AsyncMock()

    mock_hass.data[DOMAIN] = {
        entry_id: {DATA_CONNECTION: conn},
        "services_registered": True,
    }

    await mock_hass.services.async_call(
        DOMAIN, "enable_auto_warm", {"entry_id": entry_id}
    )
    await mock_hass.services.async_call(
        DOMAIN, "disable_auto_warm", {"entry_id": entry_id}
    )

    conn.enable_auto_warm.assert_awaited_once()
    conn.disable_auto_warm.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_time_service():
    """Сервис sync_time вызывает sync_time у connection_manager."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.services = MockServices()

    _ensure_services_registered(mock_hass)

    entry_id = "test_entry_id"
    conn = MagicMock()
    conn.connection_manager = MagicMock()
    conn.connection_manager.sync_time = AsyncMock()

    mock_hass.data[DOMAIN] = {
        entry_id: {DATA_CONNECTION: conn},
        "services_registered": True,
    }

    await mock_hass.services.async_call(
        DOMAIN, "sync_time", {"entry_id": entry_id}
    )

    conn.connection_manager.sync_time.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_setup_entry_unsupported_model():
    """Тест настройки с неподдерживаемой моделью."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'UNKNOWN-MODEL',
        'mac': '00:11:22:33:44:55',
        'password': 'password',
        'persistent_connection': False,
        'scan_interval': 30,
    }
    mock_entry.entry_id = 'test_entry_id'
    mock_entry.add_update_listener = MagicMock(return_value=MagicMock())

    result = await async_setup_entry(mock_hass, mock_entry)

    assert result is False


@pytest.mark.asyncio
async def test_async_setup_entry_known_but_unsupported_model():
    """Тест настройки с известной, но ещё не поддерживаемой моделью."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'RMC-M222S',
        'mac': '00:11:22:33:44:55',
        'password': 'password',
        'persistent_connection': False,
        'scan_interval': 30,
    }
    mock_entry.entry_id = 'test_entry_id'
    mock_entry.add_update_listener = MagicMock(return_value=MagicMock())

    result = await async_setup_entry(mock_hass, mock_entry)

    assert result is False


@pytest.mark.asyncio
async def test_async_setup_entry_device_not_found():
    """Тест настройки при ошибке 'устройство не найдено'."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'RMC-M40S',
        'mac': '00:11:22:33:44:55',
        'password': 'password',
        'persistent_connection': False,
        'scan_interval': 30,
    }
    mock_entry.entry_id = 'test_entry_id'
    mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
    mock_entry.async_on_unload = MagicMock(return_value=None)

    with patch('custom_components.skycooker.SkyCookerConnection') as mock_conn:
        mock_instance = MagicMock()
        mock_instance.update = AsyncMock(side_effect=Exception('устройство не найдено'))
        mock_conn.return_value = mock_instance

        result = await async_setup_entry(mock_hass, mock_entry)

    assert result is False


@pytest.mark.asyncio
async def test_async_setup_entry_connection_error():
    """Тест настройки при общей ошибке соединения."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'RMC-M40S',
        'mac': '00:11:22:33:44:55',
        'password': 'password',
        'persistent_connection': False,
        'scan_interval': 30,
    }
    mock_entry.entry_id = 'test_entry_id'
    mock_entry.add_update_listener = MagicMock(return_value=MagicMock())

    mock_entry.async_on_unload = MagicMock(return_value=None)
    with patch('custom_components.skycooker.SkyCookerConnection') as mock_conn:
        mock_instance = MagicMock()
        mock_instance.update = AsyncMock(side_effect=Exception('Connection failed'))
        mock_conn.return_value = mock_instance
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        result = await async_setup_entry(mock_hass, mock_entry)

    assert result is False


def test_device_info_with_sw_version():
    """Тест получения информации об устройстве с версией ПО."""
    mock_hass = MagicMock()
    mock_connection = MagicMock()
    mock_connection.sw_version = '2.5.0'
    mock_hass.data = {
        'skycooker': {
            'test_entry_id': {
                'connection': mock_connection,
            }
        }
    }
    mock_entry = MagicMock()
    mock_entry.data = {
        'friendly_name': 'RMC-M40S',
        'mac': '00:11:22:33:44:55',
    }
    mock_entry.entry_id = 'test_entry_id'

    result = device_info(mock_entry, mock_hass)

    assert result is not None
    assert result.get('sw_version') == '2.5.0'
    assert result.get('manufacturer') == 'Redmond'


@pytest.mark.asyncio
async def test_create_poll_scheduler_poll_schedules_when_working():
    """Тест _create_poll_scheduler: poll вызывает schedule_poll при DATA_WORKING=True."""
    from custom_components.skycooker.const import DOMAIN, DATA_WORKING, DATA_CANCEL
    from homeassistant.const import CONF_SCAN_INTERVAL

    mock_hass = MagicMock()
    mock_hass.data = {DOMAIN: {DATA_WORKING: True, DATA_CANCEL: MagicMock()}}
    mock_entry = MagicMock()
    mock_entry.data = {CONF_SCAN_INTERVAL: 30}
    mock_skycooker = MagicMock()
    mock_skycooker.update = AsyncMock()
    mock_hass.async_add_executor_job = AsyncMock()

    poll, schedule_poll = _create_poll_scheduler(mock_hass, mock_entry, mock_skycooker)

    with patch('custom_components.skycooker.ev.async_call_later') as mock_call_later:
        await poll(None)
        mock_call_later.assert_called_once()
        mock_skycooker.update.assert_called_once()
