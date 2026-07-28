# Тесты для модуля skycooker_connection_manager.py
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.skycooker_connection_manager import SkyCookerConnectionManager, AuthError, DisposedError
from custom_components.skycooker.const import MODEL_3


def test_connection_manager_initialization():
    """Тест инициализации менеджера соединений."""
    mock_hass = MagicMock()
    
    # Тест успешной инициализации
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    assert connection_manager is not None
    assert connection_manager._mac_address == "AA:BB:CC:DD:EE:FF"
    assert connection_manager._key == b"test_key"
    assert connection_manager._persistent is True
    assert connection_manager._hass == mock_hass
    assert connection_manager.model_name == "RMC-M40S"
    assert connection_manager.model_id == MODEL_3


def test_connection_manager_properties():
    """Тест свойств менеджера соединений."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Тест свойств
    assert connection_manager.mac_address == "AA:BB:CC:DD:EE:FF"
    assert connection_manager.successes == []
    assert connection_manager.disposed is False
    assert connection_manager.available is False
    assert connection_manager.connected is False
    assert connection_manager.auth_ok is False
    assert connection_manager.sw_version == "0.0"


@pytest.mark.asyncio
async def test_command_success():
    """Тест успешной отправки команды."""
    # Этот тест требует сложной эмуляции асинхронного поведения
    # и будет реализован позже
    pass


@pytest.mark.asyncio
async def test_command_disposed():
    """Тест отправки команды при disposed состоянии."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Устанавливаем disposed
    connection_manager._disposed = True
    
    with pytest.raises(DisposedError):
        await connection_manager.command(0x01)


@pytest.mark.asyncio
async def test_command_not_connected():
    """Тест отправки команды при отсутствии соединения."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем клиент без соединения
    mock_client = AsyncMock()
    mock_client.is_connected = False
    connection_manager._client = mock_client
    
    with pytest.raises(IOError):
        await connection_manager.command(0x01)


@pytest.mark.asyncio
async def test_rx_callback():
    """Тест обработки входящих данных."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Тест обработки данных
    connection_manager._rx_callback(None, bytes([0x55, 0x01, 0x01, 0x01, 0xAA]))
    
    assert connection_manager._last_data == bytes([0x55, 0x01, 0x01, 0x01, 0xAA])


@pytest.mark.asyncio
async def test_connect_success():
    """Тест успешного подключения."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем устройство и клиент
    mock_device = MagicMock()
    mock_device.name = "RMC-M40S"
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.start_notify = AsyncMock()
    
    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=mock_device):
        with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', return_value=mock_client):
            await connection_manager._connect()
            
            assert connection_manager._device == mock_device
            assert connection_manager._client == mock_client
            mock_client.start_notify.assert_called_once()


@pytest.mark.asyncio
async def test_connect_device_not_found():
    """Тест подключения при отсутствии устройства."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=None):
        with pytest.raises(IOError):
            await connection_manager._connect()


@pytest.mark.asyncio
async def test_disconnect():
    """Тест отключения."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем клиент
    mock_client = AsyncMock()
    mock_client.is_connected = True
    connection_manager._client = mock_client
    
    await connection_manager._disconnect()
    
    mock_client.disconnect.assert_called_once()
    assert connection_manager._auth_ok is False
    assert connection_manager._device is None
    assert connection_manager._client is None


@pytest.mark.asyncio
async def test_connect_if_need_success():
    """Тест подключения при необходимости."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем устройство и клиент
    mock_device = MagicMock()
    mock_device.name = "RMC-M40S"
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.start_notify = AsyncMock()
    
    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=mock_device):
        with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', return_value=mock_client):
            with patch.object(connection_manager, 'auth', new_callable=AsyncMock, return_value=True):
                with patch.object(connection_manager, 'get_version', new_callable=AsyncMock, return_value="1.0"):
                    await connection_manager._connect_if_need()
                    
                    assert connection_manager._last_connect_ok is True
                    assert connection_manager._last_auth_ok is True
                    assert connection_manager._auth_ok is True


@pytest.mark.asyncio
async def test_connect_if_need_auth_failure():
    """Тест подключения при необходимости с ошибкой аутентификации."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем устройство и клиент
    mock_device = MagicMock()
    mock_device.name = "RMC-M40S"
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.start_notify = AsyncMock()
    
    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=mock_device):
        with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', return_value=mock_client):
            with patch.object(connection_manager, 'auth', new_callable=AsyncMock, return_value=False):
                with pytest.raises(AuthError):
                    await connection_manager._connect_if_need()


@pytest.mark.asyncio
async def test_add_stat():
    """Тест добавления статистики."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Тест добавления статистики
    connection_manager.add_stat(True)
    connection_manager.add_stat(False)
    connection_manager.add_stat(True)
    
    assert connection_manager.successes == [True, False, True]
    assert connection_manager.success_rate == 66


@pytest.mark.asyncio
async def test_stop():
    """Тест остановки менеджера соединений."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем клиент
    mock_client = AsyncMock()
    mock_client.is_connected = True
    connection_manager._client = mock_client
    
    await connection_manager.stop()
    
    mock_client.disconnect.assert_called_once()
    assert connection_manager._disposed is True


@pytest.mark.asyncio
async def test_disconnect_if_need():
    """Тест отключения при необходимости."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=False,  # Не постоянное соединение
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем клиент
    mock_client = AsyncMock()
    mock_client.is_connected = True
    connection_manager._client = mock_client
    
    await connection_manager._disconnect_if_need()
    
    mock_client.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_if_need_persistent():
    """Тест отключения при необходимости с постоянным соединением."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,  # Постоянное соединение
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    
    # Мокаем клиент
    mock_client = AsyncMock()
    mock_client.is_connected = True
    connection_manager._client = mock_client
    
    await connection_manager._disconnect_if_need()
    
    # При постоянном соединении отключение не должно происходить
    mock_client.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_connect_if_need_already_connected():
    """Тест подключения при необходимости, если уже подключено."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )

    # Мокаем клиент
    mock_client = AsyncMock()
    mock_client.is_connected = True
    connection_manager._client = mock_client
    connection_manager._auth_ok = True
    connection_manager._last_connect_ok = True
    connection_manager._last_auth_ok = True

    await connection_manager._connect_if_need()

    # Если уже подключено и аутентифицировано, то ничего не должно происходить
    assert connection_manager._last_connect_ok is True
    assert connection_manager._last_auth_ok is True


@pytest.mark.asyncio
async def test_command_success():
    """Тест успешной отправки команды."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    async def mock_sleep(delay):
        # Устанавливаем ответ: 0x55, iter, command, data..., 0xAA
        connection_manager._last_data = bytes([0x55, 0x01, 0x01, 0x01, 0xAA])

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=mock_sleep):
        result = await connection_manager.command(0x01, [1, 2, 3])

    assert result == bytes([0x01])


@pytest.mark.asyncio
async def test_cleanup_previous_connections_with_client():
    """Тест очистки при наличии клиента."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    connection_manager._client = mock_client

    await connection_manager._cleanup_previous_connections()

    mock_client.disconnect.assert_called_once()
    assert connection_manager._client is None
    assert connection_manager._device is None


@pytest.mark.asyncio
async def test_cleanup_previous_connections_exception():
    """Тест очистки при исключении — исключение перехватывается."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.disconnect = AsyncMock(side_effect=RuntimeError("disconnect failed"))
    connection_manager._client = mock_client

    await connection_manager._cleanup_previous_connections()

    # Исключение перехватывается, метод завершается без выброса


@pytest.mark.asyncio
async def test_disconnect_was_not_connected():
    """Тест _disconnect когда клиент не был подключен."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = False
    connection_manager._client = mock_client

    await connection_manager._disconnect()

    mock_client.disconnect.assert_called_once()
    assert connection_manager._auth_ok is False


def test_add_stat_overflow():
    """Тест add_stat с переполнением (>100 записей)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )

    for i in range(150):
        connection_manager.add_stat(True)

    assert len(connection_manager._successes) == 100


def test_success_rate_empty():
    """Тест success_rate при пустом списке."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )

    assert connection_manager.success_rate == 0


@pytest.mark.asyncio
async def test_connect_if_need_connection_lost():
    """Тест _connect_if_need при потере соединения."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = False
    connection_manager._client = mock_client

    mock_device = MagicMock()
    mock_device.name = "RMC-M40S"
    new_client = AsyncMock()
    new_client.is_connected = True
    new_client.start_notify = AsyncMock()

    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=mock_device):
        with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', return_value=new_client):
            with patch.object(connection_manager, 'auth', new_callable=AsyncMock, return_value=True):
                with patch.object(connection_manager, 'get_version', new_callable=AsyncMock, return_value="1.0"):
                    await connection_manager._connect_if_need()

    assert connection_manager._last_connect_ok is True


def test_hass_property():
    """Тест свойства hass."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )

    assert connection_manager.hass == mock_hass
    connection_manager.hass = MagicMock()
    assert connection_manager._hass is not None


def test_update_lock_property():
    """Тест свойства update_lock."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )

    assert connection_manager.update_lock is not None


@pytest.mark.asyncio
async def test_stop_already_disposed():
    """Тест stop когда уже disposed."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager._disposed = True
    connection_manager._client = AsyncMock()

    await connection_manager.stop()

    connection_manager._client.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_disconnect_exception_swallowed():
    """Тест disconnect глотает исключения."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager._client = AsyncMock()
    connection_manager._client.disconnect = AsyncMock(side_effect=RuntimeError("disconnect error"))

    await connection_manager.disconnect()


@pytest.mark.asyncio
async def test_command_write_exception():
    """Тест command при исключении write_gatt_char."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock(side_effect=OSError("write failed"))
    connection_manager._client = mock_client

    with pytest.raises(IOError, match="Ошибка отправки команды"):
        await connection_manager.command(0x01, [])


@pytest.mark.asyncio
async def test_command_invalid_response_format():
    """Тест command при некорректном формате ответа (строки 88-89)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    async def set_bad_response(delay):
        connection_manager._last_data = bytes([0x00, 0x01, 0x01])  # Слишком короткий, не 0x55

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=set_bad_response):
        with pytest.raises(IOError, match="Некорректный формат ответа"):
            await connection_manager.command(0x01, [])


@pytest.mark.asyncio
async def test_command_invalid_response_wrong_header():
    """Тест command: len>=4 но неверный заголовок (r[0]!=0x55 или r[-1]!=0xAA)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    async def set_bad_response(delay):
        connection_manager._last_data = bytes([0x00, 0x01, 0x01, 0x01, 0xAA])  # r[0]!=0x55

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=set_bad_response):
        with pytest.raises(IOError, match="Некорректный формат ответа"):
            await connection_manager.command(0x01, [])


@pytest.mark.asyncio
async def test_command_wrong_iter_then_ok():
    """Тест command при неправильном iter, затем правильном."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    call_count = [0]

    async def set_response(delay):
        call_count[0] += 1
        if call_count[0] == 1:
            connection_manager._last_data = bytes([0x55, 0x99, 0x01, 0x01, 0xAA])  # Неверный iter
        else:
            connection_manager._last_data = bytes([0x55, 0x01, 0x01, 0x01, 0xAA])

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=set_response):
        result = await connection_manager.command(0x01, [])
    assert result == bytes([0x01])


@pytest.mark.asyncio
async def test_command_turn_on_gets_status():
    """Тест command: TURN_ON получает GET_STATUS в ответе (строки 108-111)."""
    from custom_components.skycooker.const import COMMAND_TURN_ON, COMMAND_GET_STATUS

    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    async def set_response(delay):
        connection_manager._last_data = bytes([0x55, 0x01, COMMAND_GET_STATUS, 0x01, 0xAA])

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=set_response):
        result = await connection_manager.command(COMMAND_TURN_ON, [])
    assert result == bytes([0x01])


@pytest.mark.asyncio
async def test_command_get_status_gets_delayed_response():
    """Тест command: GET_STATUS получает отложенный ответ (строки 114-117)."""
    from custom_components.skycooker.const import COMMAND_GET_STATUS, COMMAND_SELECT_PROGRAM

    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    async def set_response(delay):
        connection_manager._last_data = bytes([0x55, 0x01, COMMAND_SELECT_PROGRAM, 0x01, 0x02, 0xAA])

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=set_response):
        result = await connection_manager.command(COMMAND_GET_STATUS, [])
    assert result == bytes([0x01, 0x02])


@pytest.mark.asyncio
async def test_command_unexpected_response_raises():
    """Тест command: неожиданная команда ответа, ветка else (строки 119-120)."""
    from custom_components.skycooker.const import COMMAND_GET_STATUS, COMMAND_AUTH

    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    async def set_response(delay):
        connection_manager._last_data = bytes([0x55, 0x01, COMMAND_AUTH, 0x01, 0xAA])

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=set_response):
        with pytest.raises(IOError, match="Некорректная команда ответа"):
            await connection_manager.command(COMMAND_GET_STATUS, [])


@pytest.mark.asyncio
async def test_command_status_instead_of_select():
    """Тест command: GET_STATUS вместо SELECT_PROGRAM — принимается как успех."""
    from custom_components.skycooker.const import COMMAND_SELECT_PROGRAM, COMMAND_GET_STATUS

    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.write_gatt_char = AsyncMock()
    connection_manager._client = mock_client
    connection_manager._iter = 0

    async def set_response(delay):
        connection_manager._last_data = bytes([0x55, 0x01, COMMAND_GET_STATUS, 0x01, 0xAA])

    with patch('custom_components.skycooker.skycooker_connection_manager.asyncio.sleep', side_effect=set_response):
        result = await connection_manager.command(COMMAND_SELECT_PROGRAM, [1, 0])
    assert result == bytes([0x01])


@pytest.mark.asyncio
async def test_connect_out_of_connection_slots():
    """Тест _connect при ошибке 'out of connection slots' (строки 152-156)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_device = MagicMock()
    mock_device.name = "RMC-M40S"

    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=mock_device):
        with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', side_effect=Exception("out of connection slots")):
            with pytest.raises(Exception, match="out of connection slots"):
                await connection_manager._connect()


@pytest.mark.asyncio
async def test_connect_general_exception():
    """Тест _connect при общей ошибке подключения (строка 161)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_device = MagicMock()

    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=mock_device):
        with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', side_effect=RuntimeError("BLE error")):
            with pytest.raises(RuntimeError, match="BLE error"):
                await connection_manager._connect()


@pytest.mark.asyncio
async def test_cleanup_previous_connections_public():
    """Тест публичного метода cleanup_previous_connections (строка 204)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    with patch.object(connection_manager, '_cleanup_previous_connections', new_callable=AsyncMock) as mock_cleanup:
        await connection_manager.cleanup_previous_connections()
    mock_cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_connect_if_need_connection_lost_calls_disconnect():
    """Тест _connect_if_need: ветка 'подключение потеряно' (строка 223)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = False
    connection_manager._client = mock_client

    with patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
        with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=MagicMock()):
            with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', return_value=AsyncMock(is_connected=True, start_notify=AsyncMock())):
                with patch.object(connection_manager, 'auth', new_callable=AsyncMock, return_value=True):
                    with patch.object(connection_manager, 'get_version', new_callable=AsyncMock, return_value="1.0"):
                        await connection_manager._connect_if_need()
    mock_disconnect.assert_called()


@pytest.mark.asyncio
async def test_disconnect_if_need_public():
    """Тест публичного метода disconnect_if_need (строка 227)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=False,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager._client = AsyncMock(is_connected=True)
    with patch.object(connection_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
        await connection_manager.disconnect_if_need()
    mock_disconnect.assert_called_once()


def test_sw_version_none():
    """Тест sw_version при _sw_version=None (строка 325)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager._sw_version = None
    assert connection_manager.sw_version == "0.0"


@pytest.mark.asyncio
async def test_get_version_delegation():
    """Тест get_version делегирует в super (строка 329)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager._client = AsyncMock(is_connected=True)
    connection_manager._auth_ok = True
    with patch.object(connection_manager.__class__.__bases__[0], 'get_version', new_callable=AsyncMock, return_value="2.0") as mock_super:
        result = await connection_manager.get_version()
    assert result == "2.0"


@pytest.mark.asyncio
async def test_get_status_delegation():
    """Тест get_status делегирует (строка 334)."""
    from custom_components.skycooker.status import Status

    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager._client = AsyncMock(is_connected=True)
    mock_status = MagicMock(spec=Status)
    with patch('custom_components.skycooker.skycooker_connection_manager.get_status', new_callable=AsyncMock, return_value=mock_status) as mock_get:
        result = await connection_manager.get_status()
    mock_get.assert_called_once_with(connection_manager)
    assert result == mock_status


@pytest.mark.asyncio
async def test_select_program_delegation():
    """Тест select_program делегирует в super."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    with patch.object(connection_manager.__class__.__bases__[0], 'select_program', new_callable=AsyncMock) as mock_super:
        await connection_manager.select_program(1, 0)
    mock_super.assert_called_once_with(1, 0)


@pytest.mark.asyncio
async def test_set_main_program_delegation():
    """Тест set_main_program делегирует в super (строка 349)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    with patch.object(connection_manager.__class__.__bases__[0], 'set_main_program', new_callable=AsyncMock) as mock_super:
        await connection_manager.set_main_program(1, 0, 90, 1, 30, 0, 0, 0, 0)
    mock_super.assert_called_once()


@pytest.mark.asyncio
async def test_turn_on_delegation():
    """Тест turn_on делегирует в super (строка 363)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    with patch.object(connection_manager.__class__.__bases__[0], 'turn_on', new_callable=AsyncMock) as mock_super:
        await connection_manager.turn_on()
    mock_super.assert_called_once()


@pytest.mark.asyncio
async def test_turn_off_delegation():
    """Тест turn_off делегирует в super (строка 367)."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    with patch.object(connection_manager.__class__.__bases__[0], 'turn_off', new_callable=AsyncMock) as mock_super:
        await connection_manager.turn_off()
    mock_super.assert_called_once()


@pytest.mark.asyncio
async def test_connect_already_connected():
    """Тест _connect когда уже подключено."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = True
    connection_manager._client = mock_client

    await connection_manager._connect()

    # Не должно вызывать bluetooth/establish_connection
    assert connection_manager._client is not None


def test_rx_callback_public():
    """Тест публичного rx_callback."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager.rx_callback(None, bytes([0x55, 0x01, 0x01, 0x01, 0xAA]))
    assert connection_manager._last_data == bytes([0x55, 0x01, 0x01, 0x01, 0xAA])


@pytest.mark.asyncio
async def test_connect_public():
    """Тест публичного connect."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_device = MagicMock()
    mock_device.name = "RMC-M40S"
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.start_notify = AsyncMock()

    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=mock_device):
        with patch('custom_components.skycooker.skycooker_connection_manager.establish_connection', return_value=mock_client):
            await connection_manager.connect()
    assert connection_manager._client == mock_client


@pytest.mark.asyncio
async def test_connect_if_need_connection_lost_reconnect_fails():
    """Тест _connect_if_need при потере соединения и ошибке переподключения."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    mock_client = AsyncMock()
    mock_client.is_connected = False
    connection_manager._client = mock_client

    with patch('custom_components.skycooker.skycooker_connection_manager.bluetooth.async_ble_device_from_address', return_value=None):
        with pytest.raises(IOError):
            await connection_manager._connect_if_need()
    assert connection_manager._last_connect_ok is False


def test_sw_version_empty():
    """Тест sw_version при пустой строке."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    connection_manager._sw_version = ""
    assert connection_manager.sw_version == "0.0"


@pytest.mark.asyncio
async def test_sync_time():
    """Тест sync_time."""
    mock_hass = MagicMock()
    connection_manager = SkyCookerConnectionManager(
        mac_address="AA:BB:CC:DD:EE:FF",
        key=b"test_key",
        persistent=True,
        adapter=None,
        hass=mock_hass,
        model_name="RMC-M40S"
    )
    with patch('custom_components.skycooker.time.sync_time', new_callable=AsyncMock) as mock_sync:
        await connection_manager.sync_time()
    mock_sync.assert_called_once_with(connection_manager)