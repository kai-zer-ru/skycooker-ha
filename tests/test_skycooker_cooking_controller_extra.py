# Дополнительные тесты для повышения покрытия skycooker_cooking_controller
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.skycooker_cooking_controller import SkyCookerCookingController, SkyCookerError
from custom_components.skycooker.const import PROGRAM_STANDBY, PROGRAM_NONE


def test_target_temperature_from_status():
    """Тест target_temperature когда берётся из _status."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None

    mock_status = MagicMock()
    mock_status.is_on = True
    mock_status.target_temperature = 85
    controller._status = mock_status
    assert controller.target_temperature == 85

    mock_status.is_on = False
    assert controller.target_temperature == 25


def test_target_program_name_from_status():
    """Тест target_program_name когда берётся из _status."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = None

    mock_status = MagicMock()
    mock_status.is_on = True
    mock_status.program_name = "Yogurt"
    controller._status = mock_status
    assert controller.target_program_name == "Yogurt"


def test_target_program_name_from_status_device_off():
    """Тест target_program_name: None когда _status есть но is_on=False."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = None

    mock_status = MagicMock()
    mock_status.is_on = False
    mock_status.program_name = "Yogurt"
    controller._status = mock_status
    assert controller.target_program_name is None


@pytest.mark.asyncio
async def test_execute_cooking_sequence_public_method():
    """Тест публичного метода execute_cooking_sequence."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._status = MagicMock()
    controller._status.program_id = 0
    controller._status.is_on = False

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            await controller.execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)
    mock_connection_manager.select_program.assert_called()
    mock_connection_manager.set_main_program.assert_called_once()


def test_get_delayed_start_parameters_public_method():
    """Тест публичного метода get_delayed_start_parameters."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_additional_hours = 1
    controller._target_additional_minutes = 30

    result = controller.get_delayed_start_parameters()
    assert result == (1, 30)


def test_get_program_parameters_public_method():
    """Тест публичного метода get_program_parameters (не standby)."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # PROGRAM_YOGURT at index 12 in model 3
    program_data_list = [None] * 13
    program_data_list[12] = {"temperature": 85, "hours": 1, "minutes": 30}
    with patch.object(controller, '_get_constant_by_name', return_value="yogurt"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=12):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_NAMES', {3: ["multi_chef"] * 12 + ["yogurt"] + ["standby"]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: program_data_list}):
                    result = controller.get_program_parameters("Yogurt")
    assert result == (85, 1, 30)


def test_get_program_parameters_standby():
    """Тест _get_program_parameters для PROGRAM_STANDBY."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value=PROGRAM_STANDBY):
        result = controller._get_program_parameters("standby")
    assert result == (100, 0, 0)


def test_target_main_hours_deleter():
    """Тест deleter для target_main_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_hours = 2

    del controller.target_main_hours
    assert not hasattr(controller, '_target_main_hours')


def test_target_main_minutes_deleter():
    """Тест deleter для target_main_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_minutes = 30

    del controller.target_main_minutes
    assert not hasattr(controller, '_target_main_minutes')


def test_target_additional_hours_deleter():
    """Тест deleter для target_additional_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_additional_hours = 1

    del controller.target_additional_hours
    assert not hasattr(controller, '_target_additional_hours')


def test_target_additional_minutes_deleter():
    """Тест deleter для target_additional_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_additional_minutes = 15

    del controller.target_additional_minutes
    assert not hasattr(controller, '_target_additional_minutes')


@pytest.mark.asyncio
async def test_start_exception_with_status_message():
    """Тест start при исключении с сообщением о размере статуса."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.disconnect_if_need = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=1):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    with patch.object(controller, '_execute_cooking_sequence', new_callable=AsyncMock, side_effect=ValueError("Некорректный размер данных статуса")):
                        with pytest.raises(ValueError):
                            await controller.start()


@pytest.mark.asyncio
async def test_start_delayed_not_connected():
    """Тест start_delayed при отсутствии соединения."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = False

    controller = SkyCookerCookingController(mock_connection_manager)

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        controller._target_program_name = "multi_chef"
        with pytest.raises(SkyCookerError):
            await controller.start_delayed()


@pytest.mark.asyncio
async def test_start_delayed_exception_during_execution():
    """Тест start_delayed: исключение в try блоке (except + raise)."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = "multi_chef"

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        with patch.object(mock_connection_manager, 'connect_if_need', new_callable=AsyncMock):
            with patch.object(controller, '_get_cooking_parameters', return_value=[1, 0, 90, 1, 30]):
                with patch.object(controller, '_get_delayed_start_parameters', return_value=(0, 0)):
                    with patch.object(controller, '_execute_cooking_sequence', new_callable=AsyncMock, side_effect=RuntimeError("test")):
                        disconnect_mock = AsyncMock()
                        mock_connection_manager.disconnect_if_need = disconnect_mock
                        with pytest.raises(RuntimeError):
                            await controller.start_delayed()
    disconnect_mock.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_else_branch():
    """Тест _execute_cooking_sequence — ветка else (неизвестное состояние)."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            mock_status = MagicMock()
            mock_status.is_on = False
            mock_status.program_id = 1
            controller._status = mock_status
            controller._target_program_name = "multi_chef"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


# --- select_program с температурой из программы ---


@pytest.mark.asyncio
async def test_select_program_program_none_raises():
    """Тест select_program: PROGRAM_NONE вызывает ValueError."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # MODEL 3: PROGRAM_NONE at index 14
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="None"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants') as mock_constants:
                    mock_constants.return_value = [PROGRAM_NONE]  # index 0 = PROGRAM_NONE
                    with pytest.raises(ValueError, match="PROGRAM_NONE"):
                        await controller.select_program(0, 0)


@pytest.mark.asyncio
async def test_select_program_temperature_from_program_when_none():
    """Тест select_program: температура берётся из программы когда _target_temperature is None."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None
    controller._target_main_hours = None
    controller._target_main_minutes = None
    controller._target_additional_hours = None
    controller._target_additional_minutes = None

    program_data = {"temperature": 120, "hours": 2, "minutes": 15}
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="Yogurt"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants', return_value=["PROGRAM_YOGURT"]):
                    with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [program_data]}):
                        await controller.select_program(0, 0)

    assert controller._target_temperature == 120
    assert controller._target_main_hours == 2
    assert controller._target_main_minutes == 15
    assert controller._target_additional_hours == 0
    assert controller._target_additional_minutes == 0


# --- _get_cooking_parameters ---


def test_get_cooking_parameters_temperature_from_program_data():
    """Тест _get_cooking_parameters: температура из PROGRAM_DATA когда target_temperature is None."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None
    controller._target_main_hours = 0
    controller._target_main_minutes = 0
    controller._target_program_name = "Yogurt"

    program_data = {"temperature": 85, "hours": 1, "minutes": 30}
    with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=0):
        with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [program_data]}):
            result = controller._get_cooking_parameters("Yogurt")

    assert result[2] == 85
    assert result[3] == 1
    assert result[4] == 30


def test_get_cooking_parameters_hours_minutes_from_program_data():
    """Тест _get_cooking_parameters: часы и минуты из PROGRAM_DATA когда оба 0."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = 90
    controller._target_main_hours = 0
    controller._target_main_minutes = 0
    controller._target_program_name = "Yogurt"

    program_data = {"temperature": 85, "hours": 2, "minutes": 45}
    with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=0):
        with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [program_data]}):
            result = controller._get_cooking_parameters("Yogurt")

    assert result[2] == 90
    assert result[3] == 2
    assert result[4] == 45


# --- is_in_standby в _execute_cooking_sequence ---


@pytest.mark.asyncio
async def test_execute_cooking_sequence_is_in_standby():
    """Тест _execute_cooking_sequence: ветка is_in_standby (устройство в режиме ожидания)."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = "standby"
    controller._status = MagicMock()
    controller._status.program_id = 0
    controller._status.is_on = False

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value=PROGRAM_STANDBY):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="Yogurt"):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                        with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants', return_value=["PROGRAM_YOGURT"]):
                            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called_once_with(1, 0)
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_same_program_device_on():
    """Тест _execute_cooking_sequence: ветка current_program_id == target_program_id и device_is_on."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = "Yogurt"
    mock_status = MagicMock()
    mock_status.program_id = 1
    mock_status.is_on = True
    controller._status = mock_status

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="PROGRAM_YOGURT"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_not_called()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_wait_product_resume():
    """Тест _execute_cooking_sequence: статус 4 — только turn_on без set_main_program."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 6
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = "pasta"
    mock_status = MagicMock()
    mock_status.program_id = 6
    mock_status.is_on = True
    mock_status.status = 4
    controller._status = mock_status

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="pasta"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            await controller._execute_cooking_sequence(6, 0, 100, 0, 8, 0, 0, 0)

    mock_connection_manager.select_program.assert_not_called()
    mock_connection_manager.set_main_program.assert_not_called()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_different_program():
    """Тест _execute_cooking_sequence: ветка current_program_id != target_program_id."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = "Yogurt"
    mock_status = MagicMock()
    mock_status.program_id = 2
    mock_status.is_on = True
    controller._status = mock_status

    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="PROGRAM_YOGURT"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="Yogurt"):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                        with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants', return_value=["PROGRAM_YOGURT"]):
                            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called_once_with(1, 0)
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()
