# Тесты для модуля config_flow.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.config_flow import SkyCookerConfigFlow
from custom_components.skycooker.const import DOMAIN, CONF_MODEL, CONF_PERSISTENT_CONNECTION, CONF_FAVORITE_PROGRAMS
from homeassistant.const import CONF_MAC, CONF_PASSWORD, CONF_FRIENDLY_NAME, CONF_SCAN_INTERVAL


def test_config_flow_initialization():
    """Тест инициализации потока конфигурации."""
    mock_entry = MagicMock()
    mock_entry.data = {"test": "data"}
    
    # Тест инициализации с существующим входом
    config_flow = SkyCookerConfigFlow(entry=mock_entry)
    assert config_flow is not None
    assert config_flow.entry == mock_entry
    assert config_flow.config == {"test": "data"}
    
    # Тест инициализации без входа
    config_flow_no_entry = SkyCookerConfigFlow(entry=None)
    assert config_flow_no_entry is not None
    assert config_flow_no_entry.entry is None
    assert config_flow_no_entry.config == {}


@pytest.mark.asyncio
async def test_init_mac():
    """Тест инициализации MAC-адреса."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    
    # Мокаем методы
    config_flow._async_current_ids = MagicMock(return_value=[])
    config_flow.async_set_unique_id = AsyncMock()
    
    # Тест успешной инициализации MAC
    result = await config_flow.init_mac("AA:BB:CC:DD:EE:FF")
    assert result is True
    assert config_flow.config[CONF_MAC] == "AA:BB:CC:DD:EE:FF"
    assert config_flow.config[CONF_PASSWORD] == list(bytes.fromhex("0000000000000000"))
    
    # Тест с уже существующим MAC
    config_flow._async_current_ids = MagicMock(return_value=[f"{DOMAIN}-AA:BB:CC:DD:EE:FF"])
    result = await config_flow.init_mac("AA:BB:CC:DD:EE:FF")
    assert result is False


@pytest.mark.asyncio
async def test_async_step_user():
    """Тест шага пользователя."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    
    # Мокаем метод async_step_scan
    config_flow.async_step_scan = AsyncMock(return_value={"result": "scan"})
    
    # Тест вызова async_step_scan
    result = await config_flow.async_step_user()
    assert result == {"result": "scan"}
    config_flow.async_step_scan.assert_called_once()


@pytest.mark.asyncio
async def test_async_step_scan_no_devices():
    """Тест шага сканирования без устройств."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    
    # Мокаем сканер Bluetooth
    mock_scanner = MagicMock()
    mock_scanner.discovered_devices = []
    
    with patch('custom_components.skycooker.config_flow.bluetooth.async_get_scanner', return_value=mock_scanner):
        result = await config_flow.async_step_scan()
        
        # Проверяем, что возвращается abort с правильной причиной
        assert result["type"] == "abort"
        assert result["reason"] == "device_not_found"


@pytest.mark.asyncio
async def test_async_step_scan_with_devices():
    """Тест шага сканирования с устройствами."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    
    # Мокаем устройства
    mock_device1 = MagicMock()
    mock_device1.name = "RMC-M40S"
    mock_device1.address = "AA:BB:CC:DD:EE:FF"
    
    mock_device2 = MagicMock()
    mock_device2.name = "RFS-KMC001"
    mock_device2.address = "11:22:33:44:55:66"
    
    mock_scanner = MagicMock()
    mock_scanner.discovered_devices = [mock_device1, mock_device2]
    
    with patch('custom_components.skycooker.config_flow.bluetooth.async_get_scanner', return_value=mock_scanner):
        result = await config_flow.async_step_scan()
        
        # Проверяем, что возвращается форма с правильной схемой
        assert result["type"] == "form"
        assert result["step_id"] == "scan"
        assert CONF_MAC in result["data_schema"].schema


@pytest.mark.asyncio
async def test_async_step_scan_user_input():
    """Тест шага сканирования с вводом пользователя."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    
    # Мокаем методы
    config_flow.init_mac = AsyncMock(return_value=True)
    config_flow.async_step_connect = AsyncMock(return_value={"result": "connect"})
    
    # Тест с корректным вводом пользователя
    user_input = {CONF_MAC: "AA:BB:CC:DD:EE:FF (RMC-M40S)"}
    
    with patch('custom_components.skycooker.config_flow.SkyCooker.get_model_id', return_value=3):
        result = await config_flow.async_step_scan(user_input=user_input)
        
        # Проверяем, что возвращается результат шага connect
        assert result == {"result": "connect"}
        config_flow.init_mac.assert_called_once_with("AA:BB:CC:DD:EE:FF")


@pytest.mark.asyncio
async def test_async_step_connect_success():
    """Тест успешного шага подключения."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000"))
    }
    
    # Мокаем SkyCookerConnection
    mock_connection = AsyncMock()
    mock_connection.last_connect_ok = True
    mock_connection.last_auth_ok = True
    mock_connection.update = AsyncMock()
    mock_connection.stop = AsyncMock()
    
    config_flow.async_step_init = AsyncMock(return_value={"result": "init"})
    
    with patch('custom_components.skycooker.config_flow.SkyCookerConnection', return_value=mock_connection):
        result = await config_flow.async_step_connect(user_input={})
        
        # Проверяем, что возвращается результат шага init
        assert result == {"result": "init"}


@pytest.mark.asyncio
async def test_async_step_connect_failure():
    """Тест неудачного шага подключения."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000"))
    }
    
    # Мокаем SkyCookerConnection с ошибкой подключения
    mock_connection = AsyncMock()
    mock_connection.last_connect_ok = False
    mock_connection.update = AsyncMock()
    mock_connection.stop = AsyncMock()
    
    with patch('custom_components.skycooker.config_flow.SkyCookerConnection', return_value=mock_connection):
        result = await config_flow.async_step_connect(user_input={})
        
        # Проверяем, что возвращается форма с ошибкой
        assert result["type"] == "form"
        assert result["step_id"] == "connect"
        assert "errors" in result
        assert "base" in result["errors"]


@pytest.mark.asyncio
async def test_async_step_init_success():
    """Тест успешного шага инициализации."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
        CONF_FRIENDLY_NAME: "Test Device",
        CONF_MODEL: 3
    }
    
    # Мокаем методы
    mock_create_entry = MagicMock()
    mock_create_entry.return_value = {"result": "create"}
    config_flow.async_create_entry = mock_create_entry
    
    user_input = {
        CONF_SCAN_INTERVAL: 30,
        CONF_PERSISTENT_CONNECTION: True,
        CONF_FAVORITE_PROGRAMS: ["program1", "program2"]
    }
    
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["program1", "program2", "program3"]):
        result = await config_flow.async_step_init(user_input=user_input)
        
        # Проверяем, что возвращается результат создания входа
        assert result == {"result": "create"}
        assert config_flow.config[CONF_SCAN_INTERVAL] == 30
        assert config_flow.config[CONF_PERSISTENT_CONNECTION] is True
        assert config_flow.config[CONF_FAVORITE_PROGRAMS] == ["program1", "program2"]


@pytest.mark.asyncio
async def test_async_step_init_failure():
    """Тест неудачного шага инициализации."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000"))
    }
    
    # Тест с некорректным вводом пользователя
    user_input = {
        CONF_SCAN_INTERVAL: "invalid",  # Некорректное значение
        CONF_PERSISTENT_CONNECTION: True
    }
    
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["program1", "program2"]):
        result = await config_flow.async_step_init(user_input=user_input)
        
        # Проверяем, что возвращается abort с правильной причиной
        assert result["type"] == "abort"
        assert result["reason"] == "invalid_input"


@pytest.mark.asyncio
async def test_async_get_options_flow():
    """Тест получения потока опций."""
    mock_entry = MagicMock()
    mock_entry.data = {"test": "data"}

    # Тест получения потока опций
    options_flow = SkyCookerConfigFlow.async_get_options_flow(mock_entry)

    assert options_flow is not None
    assert options_flow.entry == mock_entry
    assert options_flow.config == {"test": "data"}


@pytest.mark.asyncio
async def test_async_step_scan_unknown_model():
    """Тест шага сканирования с неизвестной моделью."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass

    user_input = {CONF_MAC: "AA:BB:CC:DD:EE:FF (UNKNOWN-MODEL)"}
    with patch('custom_components.skycooker.config_flow.SkyCooker.get_model_id', return_value=None):
        result = await config_flow.async_step_scan(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "unknown_model"


@pytest.mark.asyncio
async def test_async_step_scan_already_configured():
    """Тест шага сканирования с уже настроенным устройством."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow._async_current_ids = MagicMock(return_value=[f"{DOMAIN}-AA:BB:CC:DD:EE:FF"])
    config_flow.async_set_unique_id = AsyncMock()
    config_flow.init_mac = AsyncMock(return_value=False)

    user_input = {CONF_MAC: "AA:BB:CC:DD:EE:FF (RMC-M40S)"}
    with patch('custom_components.skycooker.config_flow.SkyCooker.get_model_id', return_value=3):
        result = await config_flow.async_step_scan(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_async_step_scan_with_name():
    """Тест шага сканирования с именем устройства (len(spl) >= 2)."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.init_mac = AsyncMock(return_value=True)
    config_flow.async_step_connect = AsyncMock(return_value={"result": "connect"})

    user_input = {CONF_MAC: "AA:BB:CC:DD:EE:FF (RMC-M40S)"}
    with patch('custom_components.skycooker.config_flow.SkyCooker.get_model_id', return_value=3):
        result = await config_flow.async_step_scan(user_input=user_input)

    assert result == {"result": "connect"}
    assert config_flow.config.get(CONF_FRIENDLY_NAME) == "RMC-M40S"
    assert config_flow.config.get(CONF_MODEL) == 3


@pytest.mark.asyncio
async def test_async_step_scan_user_input_exception():
    """Тест шага сканирования с исключением при обработке ввода."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass

    user_input = {CONF_MAC: "invalid_format_causing_exception"}
    with patch('custom_components.skycooker.config_flow.SkyCooker.get_model_id', side_effect=ValueError("bad")):
        result = await config_flow.async_step_scan(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_input"


@pytest.mark.asyncio
async def test_async_step_scan_no_scanner():
    """Тест шага сканирования без сканера Bluetooth."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass

    with patch('custom_components.skycooker.config_flow.bluetooth.async_get_scanner', return_value=None):
        result = await config_flow.async_step_scan()

    assert result["type"] == "abort"
    assert result["reason"] == "no_bluetooth"


@pytest.mark.asyncio
async def test_async_step_scan_exception():
    """Тест шага сканирования с исключением при сканировании."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass

    with patch('custom_components.skycooker.config_flow.bluetooth.async_get_scanner', side_effect=RuntimeError("scan failed")):
        result = await config_flow.async_step_scan()

    assert result["type"] == "abort"
    assert result["reason"] == "scan_failed"


@pytest.mark.asyncio
async def test_async_step_connect_no_mac():
    """Тест шага подключения без MAC-адреса."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {CONF_PASSWORD: list(bytes.fromhex("0000000000000000"))}

    result = await config_flow.async_step_connect(user_input={})

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_config"


@pytest.mark.asyncio
async def test_async_step_connect_no_password():
    """Тест шага подключения без пароля."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {CONF_MAC: "AA:BB:CC:DD:EE:FF"}

    result = await config_flow.async_step_connect(user_input={})

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_config"


@pytest.mark.asyncio
async def test_async_step_connect_cant_auth():
    """Тест шага подключения с ошибкой аутентификации."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }

    mock_connection = MagicMock()
    mock_connection.last_connect_ok = True
    mock_connection.last_auth_ok = False
    mock_connection.update = AsyncMock()
    mock_connection.stop = AsyncMock()

    with patch('custom_components.skycooker.config_flow.SkyCookerConnection', return_value=mock_connection):
        result = await config_flow.async_step_connect(user_input={})

    assert result["type"] == "form"
    assert result["step_id"] == "connect"
    assert result["errors"]["base"] == "cant_auth"


@pytest.mark.asyncio
async def test_async_step_connect_exception():
    """Тест шага подключения с исключением."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }

    with patch('custom_components.skycooker.config_flow.SkyCookerConnection', side_effect=RuntimeError("connection error")):
        result = await config_flow.async_step_connect(user_input={})

    assert result["type"] == "abort"
    assert result["reason"] == "connection_failed"


@pytest.mark.asyncio
async def test_async_step_connect_show_form():
    """Тест отображения формы шага подключения (без user_input)."""
    mock_hass = MagicMock()
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }

    result = await config_flow.async_step_connect(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "connect"


@pytest.mark.asyncio
async def test_async_step_init_no_mac():
    """Тест шага инициализации без MAC в конфиге."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {CONF_PASSWORD: list(bytes.fromhex("0000000000000000"))}

    user_input = {CONF_SCAN_INTERVAL: 30, CONF_PERSISTENT_CONNECTION: True}
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=[]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_config"


@pytest.mark.asyncio
async def test_async_step_init_no_password():
    """Тест шага инициализации без пароля в конфиге."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {CONF_MAC: "AA:BB:CC:DD:EE:FF"}

    user_input = {CONF_SCAN_INTERVAL: 30, CONF_PERSISTENT_CONNECTION: True}
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=[]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_config"


@pytest.mark.asyncio
async def test_async_step_init_persistent_connection_string_false():
    """Тест: persistent_connection="false" (строка) преобразуется в False."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
        CONF_FRIENDLY_NAME: "Test",
    }
    config_flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

    user_input = {
        CONF_SCAN_INTERVAL: 30,
        CONF_PERSISTENT_CONNECTION: "false",
    }
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["p1"]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert config_flow.config[CONF_PERSISTENT_CONNECTION] is False
    assert result.get("type") == "create_entry" or "result" in result


@pytest.mark.asyncio
async def test_async_step_init_persistent_connection_string_true():
    """Тест: persistent_connection="true" (строка) преобразуется в True."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
        CONF_FRIENDLY_NAME: "Test",
    }
    config_flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

    user_input = {
        CONF_SCAN_INTERVAL: 30,
        CONF_PERSISTENT_CONNECTION: "true",
    }
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["p1"]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert config_flow.config[CONF_PERSISTENT_CONNECTION] is True


@pytest.mark.asyncio
async def test_async_step_init_invalid_persistent():
    """Тест шага инициализации с отсутствующим persistent_connection (KeyError)."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }

    # Отсутствует CONF_PERSISTENT_CONNECTION — вызывает KeyError
    user_input = {CONF_SCAN_INTERVAL: 30}
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["p1", "p2"]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_input"


@pytest.mark.asyncio
async def test_async_step_init_favorite_programs_max():
    """Тест шага инициализации с избранными программами > MAX."""
    from custom_components.skycooker.const import MAX_FAVORITE_PROGRAMS

    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
        CONF_FRIENDLY_NAME: "Test",
    }
    config_flow.async_create_entry = MagicMock(return_value={"result": "created"})

    programs = [f"p{i}" for i in range(10)]
    user_input = {
        CONF_SCAN_INTERVAL: 30,
        CONF_PERSISTENT_CONNECTION: True,
        CONF_FAVORITE_PROGRAMS: programs,
    }
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=programs):
        result = await config_flow.async_step_init(user_input=user_input)

    assert config_flow.config[CONF_FAVORITE_PROGRAMS] == programs[:MAX_FAVORITE_PROGRAMS]


@pytest.mark.asyncio
async def test_async_step_init_with_entry_update():
    """Тест шага инициализации с обновлением существующей записи."""
    mock_entry = MagicMock()
    mock_entry.data = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
        CONF_FRIENDLY_NAME: "Test",
    }
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.config_entries = MagicMock()
    mock_hass.config_entries.async_update_entry = AsyncMock()

    config_flow = SkyCookerConfigFlow(entry=mock_entry)
    config_flow.hass = mock_hass
    config_flow.config = dict(mock_entry.data)
    config_flow.async_create_entry = MagicMock(return_value={"result": "created"})

    user_input = {
        CONF_SCAN_INTERVAL: 30,
        CONF_PERSISTENT_CONNECTION: True,
    }
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["p1"]):
        result = await config_flow.async_step_init(user_input=user_input)

    mock_hass.config_entries.async_update_entry.assert_called_once_with(mock_entry, data=config_flow.config)


@pytest.mark.asyncio
async def test_async_step_init_update_failed():
    """Тест шага инициализации с ошибкой обновления записи."""
    mock_entry = MagicMock()
    mock_entry.data = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
        CONF_FRIENDLY_NAME: "Test",
    }
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.config_entries = MagicMock()
    # sync raise — config_flow вызывает async_update_entry без await
    mock_hass.config_entries.async_update_entry = MagicMock(side_effect=Exception("update error"))

    config_flow = SkyCookerConfigFlow(entry=mock_entry)
    config_flow.hass = mock_hass
    config_flow.config = dict(mock_entry.data)

    user_input = {
        CONF_SCAN_INTERVAL: 30,
        CONF_PERSISTENT_CONNECTION: True,
    }
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["p1"]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "update_failed"


@pytest.mark.asyncio
async def test_async_step_init_show_form():
    """Тест отображения формы шага инициализации (без user_input)."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }

    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["Yogurt", "Rice"]):
        result = await config_flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert "data_schema" in result


@pytest.mark.asyncio
async def test_async_step_init_invalid_scan_interval():
    """Тест шага инициализации с некорректным scan_interval (KeyError)."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }

    user_input = {CONF_PERSISTENT_CONNECTION: True}
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["p1"]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_input"


@pytest.mark.asyncio
async def test_async_step_init_config_save_failed():
    """Тест шага инициализации с исключением при сохранении."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }
    config_flow.async_create_entry = MagicMock(side_effect=RuntimeError("create failed"))

    user_input = {
        CONF_SCAN_INTERVAL: 30,
        CONF_PERSISTENT_CONNECTION: True,
    }
    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=["p1"]):
        result = await config_flow.async_step_init(user_input=user_input)

    assert result["type"] == "abort"
    assert result["reason"] == "config_save_failed"


@pytest.mark.asyncio
async def test_async_step_init_form_exception():
    """Тест шага инициализации с исключением при создании формы."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    config_flow = SkyCookerConfigFlow(entry=None)
    config_flow.hass = mock_hass
    config_flow.config = {
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_PASSWORD: list(bytes.fromhex("0000000000000000")),
    }

    with patch('custom_components.skycooker.config_flow.get_program_options', return_value=None):
        result = await config_flow.async_step_init(user_input=None)

    assert result["type"] == "abort"
    assert result["reason"] == "init_failed"