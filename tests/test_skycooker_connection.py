# Тесты для модуля skycooker_connection.py
import pytest
from custom_components.skycooker.skycooker_connection import SkyCookerConnection
from unittest.mock import MagicMock, AsyncMock, patch


def test_connection_initialization(mock_connection):
    """Тест инициализации соединения."""
    assert mock_connection._mac == "00:00:00:00:00:00"
    assert mock_connection.connection_manager._key == b"test_key"


@pytest.mark.asyncio
async def test_connection_connect(mock_connection, mocker):
    """Тест подключения к Skycooker."""
    mocker.patch.object(mock_connection.connection_manager, "connect", return_value=True)
    result = await mock_connection._connect()
    assert result is None


@pytest.mark.asyncio
async def test_connection_disconnect(mock_connection, mocker):
    """Тест отключения от Skycooker."""
    mocker.patch.object(mock_connection.connection_manager, "disconnect", return_value=True)
    result = await mock_connection.disconnect()
    assert result is None


@pytest.mark.asyncio
async def test_connection_command(mock_connection, mocker):
    """Тест выполнения команды."""
    mocker.patch.object(mock_connection.connection_manager, "command", return_value=True)
    result = await mock_connection.command(1, {"param": "value"})
    assert result is True


def test_connection_rx_callback(mock_connection, mocker):
    """Тест обработчика получения данных."""
    mocker.patch.object(mock_connection.connection_manager, "rx_callback", return_value=None)
    mock_connection._rx_callback("sender", "data")
    mock_connection.connection_manager.rx_callback.assert_called_once()


@pytest.mark.asyncio
async def test_connection_cleanup_previous_connections(mock_connection, mocker):
    """Тест очистки предыдущих соединений."""
    mocker.patch.object(mock_connection.connection_manager, "cleanup_previous_connections", return_value=None)
    result = await mock_connection._cleanup_previous_connections()
    assert result is None


@pytest.mark.asyncio
async def test_connection_auth(mock_connection, mocker):
    """Тест аутентификации."""
    mocker.patch.object(mock_connection.connection_manager, "auth", return_value=True)
    result = await mock_connection.auth()
    assert result is True


@pytest.mark.asyncio
async def test_connection_stop(mock_connection, mocker):
    """Тест остановки соединения."""
    mocker.patch.object(mock_connection.connection_manager, "stop", return_value=None)
    result = await mock_connection.stop()
    assert result is None


def test_connection_success_rate(mock_connection):
    """Тест success_rate."""
    assert mock_connection.success_rate == mock_connection.state_manager.success_rate


@pytest.mark.asyncio
async def test_connection_commit(mock_connection, mocker):
    """Тест commit."""
    mocker.patch.object(mock_connection.state_manager, "commit", return_value=None)
    await mock_connection.commit()
    mock_connection.state_manager.commit.assert_called_once()


@pytest.mark.asyncio
async def test_connection_update(mock_connection, mocker):
    """Тест update."""
    mocker.patch.object(mock_connection.state_manager, "update", return_value=None)
    result = await mock_connection.update()
    mock_connection.state_manager.update.assert_called_once()
    assert result is None


def test_connection_is_program_supported(mock_connection, mocker):
    """Тест _is_program_supported."""
    mocker.patch.object(mock_connection.cooking_controller, "is_program_supported", return_value=True)
    assert mock_connection._is_program_supported("Yogurt") is True


def test_connection_properties(mock_connection):
    """Тест свойств соединения."""
    assert mock_connection.available == mock_connection.connection_manager.available
    assert mock_connection.last_connect_ok == mock_connection.connection_manager.last_connect_ok
    assert mock_connection.last_auth_ok == mock_connection.connection_manager.last_auth_ok
    assert mock_connection.connected == mock_connection.connection_manager.connected
    assert mock_connection.auth_ok == mock_connection.connection_manager.auth_ok
    assert mock_connection.sw_version == mock_connection.connection_manager.sw_version
    assert mock_connection.status_code == mock_connection.state_manager.status_code
    assert mock_connection.auto_warm == mock_connection.state_manager.auto_warm
    assert mock_connection.subprog == mock_connection.state_manager.subprog
    assert mock_connection.current_program_id == mock_connection.cooking_controller.current_program_id
    assert mock_connection.target_temperature == mock_connection.cooking_controller.target_temperature
    assert mock_connection.target_program_name == mock_connection.cooking_controller.target_program_name
    assert mock_connection.target_main_hours == mock_connection.cooking_controller.target_main_hours
    assert mock_connection.target_main_minutes == mock_connection.cooking_controller.target_main_minutes
    assert mock_connection.target_additional_hours == mock_connection.cooking_controller.target_additional_hours
    assert mock_connection.target_additional_minutes == mock_connection.cooking_controller.target_additional_minutes
    assert mock_connection.target_subprogram_id == mock_connection.cooking_controller.target_subprogram_id
    assert mock_connection.status == mock_connection.cooking_controller.status


@pytest.mark.asyncio
async def test_connection_connect_if_need(mock_connection, mocker):
    """Тест подключения при необходимости."""
    mocker.patch.object(mock_connection.connection_manager, "connect_if_need", return_value=True)
    result = await mock_connection._connect_if_need()
    assert result is None


@pytest.mark.asyncio
async def test_connection_disconnect_if_need(mock_connection, mocker):
    """Тест отключения при необходимости."""
    mocker.patch.object(mock_connection.connection_manager, "disconnect_if_need", return_value=True)
    result = await mock_connection._disconnect_if_need()
    assert result is None


@pytest.mark.asyncio
async def test_connection_disconnect_internal(mock_connection, mocker):
    """Тест _disconnect (внутренний метод)."""
    mocker.patch.object(mock_connection.connection_manager, "disconnect", return_value=None)
    await mock_connection._disconnect()
    mock_connection.connection_manager.disconnect.assert_called_once()


def test_connection_add_stat(mock_connection, mocker):
    """Тест add_stat."""
    mocker.patch.object(mock_connection.connection_manager, "add_stat")
    mock_connection.add_stat(42)
    mock_connection.connection_manager.add_stat.assert_called_once_with(42)


def test_connection_setters(mock_connection):
    """Тест сеттеров target_*."""
    mock_connection.target_program_name = "NewProgram"
    assert mock_connection.cooking_controller.target_program_name == "NewProgram"

    mock_connection.target_main_hours = 2
    assert mock_connection.cooking_controller.target_main_hours == 2

    mock_connection.target_main_minutes = 45
    assert mock_connection.cooking_controller.target_main_minutes == 45

    mock_connection.target_additional_hours = 1
    assert mock_connection.cooking_controller.target_additional_hours == 1

    mock_connection.target_additional_minutes = 30
    assert mock_connection.cooking_controller.target_additional_minutes == 30

    mock_connection.target_subprogram_id = 1
    assert mock_connection.cooking_controller.target_subprogram_id == 1

    mock_connection.target_temperature = 120
    assert mock_connection.cooking_controller.target_temperature == 120


def test_connection_auto_warm_enabled(mock_connection):
    """Тест auto_warm_enabled getter и setter."""
    mock_connection.auto_warm_enabled = True
    assert mock_connection.auto_warm_enabled is True

    mock_connection.auto_warm_enabled = False
    assert mock_connection.auto_warm_enabled is False


def test_connection_private_properties(mock_connection):
    """Тест _successes, _disposed, _mac."""
    assert mock_connection._successes == mock_connection.connection_manager.successes
    assert mock_connection._disposed == mock_connection.connection_manager.disposed
    assert mock_connection._mac == mock_connection.connection_manager.mac_address


@pytest.mark.asyncio
async def test_connection_select_program(mock_connection, mocker):
    """Тест select_program."""
    mocker.patch("custom_components.skycooker.skycooker_connection.find_program_id", return_value=1)
    mocker.patch.object(mock_connection.cooking_controller, "select_program", return_value=None)
    await mock_connection.select_program("Yogurt", 0)
    mock_connection.cooking_controller.select_program.assert_called_once_with(1, 0)


@pytest.mark.asyncio
async def test_connection_set_boil_time(mock_connection, mocker):
    """Тест set_boil_time."""
    mocker.patch.object(mock_connection.cooking_controller, "set_boil_time", return_value=None)
    await mock_connection.set_boil_time(2, 30)
    mock_connection.cooking_controller.set_boil_time.assert_called_once_with(2, 30)


@pytest.mark.asyncio
async def test_connection_set_temperature(mock_connection, mocker):
    """Тест set_temperature."""
    mocker.patch.object(mock_connection.cooking_controller, "set_temperature", return_value=None)
    await mock_connection.set_temperature(100)
    mock_connection.cooking_controller.set_temperature.assert_called_once_with(100)


@pytest.mark.asyncio
async def test_connection_set_delayed_start(mock_connection, mocker):
    """Тест set_delayed_start."""
    mocker.patch.object(mock_connection.cooking_controller, "set_delayed_start", return_value=None)
    await mock_connection.set_delayed_start(1, 15)
    mock_connection.cooking_controller.set_delayed_start.assert_called_once_with(1, 15)


@pytest.mark.asyncio
async def test_connection_start(mock_connection, mocker):
    """Тест start."""
    mocker.patch.object(mock_connection.cooking_controller, "start", return_value=None)
    await mock_connection.start()
    mock_connection.cooking_controller.start.assert_called_once()


@pytest.mark.asyncio
async def test_connection_enable_disable_auto_warm(mock_connection, mocker):
    """Тест enable_auto_warm и disable_auto_warm."""
    mocker.patch.object(mock_connection.cooking_controller, "enable_auto_warm", return_value=None)
    await mock_connection.enable_auto_warm()
    mock_connection.cooking_controller.enable_auto_warm.assert_called_once()

    mocker.patch.object(mock_connection.cooking_controller, "disable_auto_warm", return_value=None)
    await mock_connection.disable_auto_warm()
    mock_connection.cooking_controller.disable_auto_warm.assert_called_once()


@pytest.mark.asyncio
async def test_connection_stop_cooking(mock_connection, mocker):
    """Тест stop_cooking."""
    mocker.patch.object(mock_connection.cooking_controller, "stop_cooking", return_value=None)
    await mock_connection.stop_cooking()
    mock_connection.cooking_controller.stop_cooking.assert_called_once()


@pytest.mark.asyncio
async def test_connection_start_delayed(mock_connection, mocker):
    """Тест start_delayed."""
    mocker.patch.object(mock_connection.cooking_controller, "start_delayed", return_value=None)
    await mock_connection.start_delayed()
    mock_connection.cooking_controller.start_delayed.assert_called_once()


@pytest.mark.asyncio
async def test_connection_set_target_temp(mock_connection, mocker):
    """Тест set_target_temp."""
    mocker.patch.object(mock_connection.cooking_controller, "set_target_temp", return_value=None)
    await mock_connection.set_target_temp(80)
    mock_connection.cooking_controller.set_target_temp.assert_called_once_with(80)


def test_connection_get_delayed_start_parameters(mock_connection, mocker):
    """Тест _get_delayed_start_parameters."""
    mocker.patch.object(mock_connection.cooking_controller, "get_delayed_start_parameters", return_value=(1, 30))
    assert mock_connection._get_delayed_start_parameters() == (1, 30)


def test_connection_get_program_parameters(mock_connection, mocker):
    """Тест _get_program_parameters."""
    mocker.patch.object(mock_connection.cooking_controller, "get_program_parameters", return_value={})
    assert mock_connection._get_program_parameters("Yogurt") == {}


@pytest.mark.asyncio
async def test_connection_set_target_program(mock_connection, mocker):
    """Тест set_target_program."""
    mocker.patch.object(mock_connection.cooking_controller, "set_target_program", return_value=None)
    await mock_connection.set_target_program("Yogurt")
    mock_connection.cooking_controller.set_target_program.assert_called_once_with("Yogurt")


@pytest.mark.asyncio
async def test_connection_execute_cooking_sequence(mock_connection, mocker):
    """Тест _execute_cooking_sequence."""
    mocker.patch.object(mock_connection.cooking_controller, "execute_cooking_sequence", return_value=None)
    await mock_connection._execute_cooking_sequence(
        target_program_id=1,
        target_subprogram_id=0,
        target_temp=100,
        target_main_hours=1,
        target_main_minutes=30,
        target_additional_hours=0,
        target_additional_minutes=0,
        auto_warm_flag=False,
    )
    mock_connection.cooking_controller.execute_cooking_sequence.assert_called_once()
