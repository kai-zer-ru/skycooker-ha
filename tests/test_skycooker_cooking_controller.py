# Тесты для модуля skycooker_cooking_controller.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.skycooker_cooking_controller import SkyCookerCookingController, SkyCookerError
from custom_components.skycooker.const import PROGRAM_STANDBY, PROGRAM_NONE


def test_cooking_controller_initialization():
    """Тест инициализации контроллера приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        controller = SkyCookerCookingController(mock_connection_manager)
    
    assert controller is not None
    assert controller.connection_manager == mock_connection_manager
    assert controller._target_program_name == "standby"
    assert controller._target_program_name == "standby"
    assert controller._target_temperature == 100
    assert controller._target_main_hours == 0
    assert controller._target_main_minutes == 0
    assert controller._target_additional_hours == 0
    assert controller._target_additional_minutes == 0
    assert controller._auto_warm_enabled == True


def test_is_mode_supported():
    """Тест проверки поддержки режима."""
    mock_hass = MagicMock()
    
    # Тест с поддерживаемым режимом
    from custom_components.skycooker.skycooker_cooking_controller import is_mode_supported
    with patch('custom_components.skycooker.skycooker_cooking_controller.is_program_supported', return_value=True):
        result = is_mode_supported(mock_hass, "multi_chef", 3)
        assert result is True
    
    # Тест с неподдерживаемым режимом
    with patch('custom_components.skycooker.skycooker_cooking_controller.is_program_supported', return_value=False):
        result = is_mode_supported(mock_hass, "unknown_program", 3)
        assert result is False


@pytest.mark.asyncio
async def test_select_program_success():
    """Тест успешного выбора программы."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{}]}):
                    await controller.select_program(1, 0)
    
    mock_connection_manager.select_program.assert_called_once()


@pytest.mark.asyncio
async def test_select_program_unsupported():
    """Тест выбора неподдерживаемой программы."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="unknown_program"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=False):
                with pytest.raises(ValueError):
                    await controller.select_program(1, 0)


@pytest.mark.asyncio
async def test_select_program_none():
    """Тест выбора программы PROGRAM_NONE."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="none_program"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants', return_value=[PROGRAM_NONE]):
                with pytest.raises(ValueError):
                    await controller.select_program(0, 0)


@pytest.mark.asyncio
async def test_select_program_standby():
    """Тест выбора программы PROGRAM_STANDBY."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants', return_value=[PROGRAM_STANDBY]):
                await controller.select_program(0, 0)

    assert controller._target_temperature == 100
    assert controller._target_main_hours == 0
    assert controller._target_main_minutes == 0
    assert controller._target_additional_hours == 0
    assert controller._target_additional_minutes == 0


@pytest.mark.asyncio
async def test_start_success():
    """Тест успешного запуска приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.disconnect_if_need = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=1):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    with patch.object(controller, '_execute_cooking_sequence', new_callable=AsyncMock) as mock_execute:
                        await controller.start()

    mock_connection_manager.connect_if_need.assert_called_once()
    mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_start_standby_mode():
    """Тест запуска приготовления в режиме ожидания."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        controller._target_program_name = "standby"
        await controller.start()

    # Проверяем, что ничего не произошло
    assert controller._target_program_name == "standby"


@pytest.mark.asyncio
async def test_start_not_connected():
    """Тест запуска приготовления при отсутствии соединения."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = False
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    with pytest.raises(SkyCookerError):
        await controller.start()


@pytest.mark.asyncio
async def test_stop_cooking():
    """Тест остановки приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.turn_off = AsyncMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value=PROGRAM_STANDBY):
            with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=16):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_NAMES', {3: ["standby"]}):
                        await controller.stop_cooking()
    
    mock_connection_manager.turn_off.assert_called_once()
    assert controller._target_program_name == "standby"
    assert controller._target_temperature == 100
    assert controller._target_main_hours == 0
    assert controller._target_main_minutes == 0
    assert controller._target_additional_hours == 0
    assert controller._target_additional_minutes == 0
    assert controller._auto_warm_enabled == True



@pytest.mark.asyncio
async def test_enable_auto_warm(mocker):
    """Тест включения автоподогрева."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    controller = SkyCookerCookingController(mock_connection_manager)
    mocker.patch.object(controller, "_apply_auto_warm_to_device", new_callable=AsyncMock)

    await controller.enable_auto_warm()

    assert controller._auto_warm_enabled is True
    controller._apply_auto_warm_to_device.assert_called_once()


@pytest.mark.asyncio
async def test_disable_auto_warm(mocker):
    """Тест выключения автоподогрева."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    controller = SkyCookerCookingController(mock_connection_manager)
    mocker.patch.object(controller, "_apply_auto_warm_to_device", new_callable=AsyncMock)

    await controller.disable_auto_warm()

    assert controller._auto_warm_enabled is False
    controller._apply_auto_warm_to_device.assert_called_once()


@pytest.mark.asyncio
async def test_set_target_temp():
    """Тест установки целевой температуры."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_target_temp(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_temp_same_value():
    """Тест установки целевой температуры с тем же значением."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = 90

    await controller.set_target_temp(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_program():
    """Тест установки целевой программы."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    # Температура по умолчанию 90, если не установлена
    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_program_standby():
    """Тест установки целевой программы в режим ожидания."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value=PROGRAM_STANDBY):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            await controller.set_target_program("standby")

    assert controller._target_program_name == "standby"
    assert controller._target_temperature == 100
    assert controller._target_main_hours == 0
    assert controller._target_main_minutes == 0
    assert controller._target_additional_hours == 0
    assert controller._target_additional_minutes == 0
    assert controller._auto_warm_enabled == True


@pytest.mark.asyncio
async def test_set_target_program_unsupported():
    """Тест установки неподдерживаемой программы."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="unknown"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=False):
            await controller.set_target_program("unknown")

    assert controller._target_program_name != "unknown"


@pytest.mark.asyncio
async def test_set_boil_time():
    """Тест установки времени приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_boil_time(1, 30)

    assert controller._target_main_hours == 1
    assert controller._target_main_minutes == 30


@pytest.mark.asyncio
async def test_set_temperature():
    """Тест установки температуры."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_temperature(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_delayed_start():
    """Тест установки отложенного старта."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_delayed_start(2, 30)

    assert controller._target_additional_hours == 2
    assert controller._target_additional_minutes == 30


@pytest.mark.asyncio
async def test_set_temperature():
    """Тест установки температуры."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_temperature(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_delayed_start():
    """Тест установки отложенного старта."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_delayed_start(2, 30)

    assert controller._target_additional_hours == 2
    assert controller._target_additional_minutes == 30


@pytest.mark.asyncio
async def test_set_delayed_start():
    """Тест установки отложенного старта."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_delayed_start(2, 30)

    assert controller._target_additional_hours == 2
    assert controller._target_additional_minutes == 30


@pytest.mark.asyncio
async def test_set_boil_time():
    """Тест установки времени приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_boil_time(1, 30)

    assert controller._target_main_hours == 1
    assert controller._target_main_minutes == 30


@pytest.mark.asyncio
async def test_set_temperature():
    """Тест установки температуры."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_temperature(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_delayed_start():
    """Тест установки отложенного старта."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_delayed_start(2, 30)

    assert controller._target_additional_hours == 2
    assert controller._target_additional_minutes == 30


@pytest.mark.asyncio
async def test_set_boil_time():
    """Тест установки времени приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_boil_time(1, 30)

    assert controller._target_main_hours == 1
    assert controller._target_main_minutes == 30


@pytest.mark.asyncio
async def test_set_temperature():
    """Тест установки температуры."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_temperature(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_delayed_start():
    """Тест установки отложенного старта."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    await controller.set_delayed_start(2, 30)

    assert controller._target_additional_hours == 2
    assert controller._target_additional_minutes == 30


@pytest.mark.asyncio
async def test_set_target_program_same_value():
    """Тест установки целевой программы с тем же значением."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_program_name = "multi_chef"

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"


@pytest.mark.asyncio
async def test_set_target_program_with_additional_hours():
    """Тест установки целевой программы с дополнительными часами."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_additional_hours = 2

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_additional_hours == 2


@pytest.mark.asyncio
async def test_set_target_program_with_additional_minutes():
    """Тест установки целевой программы с дополнительными минутами."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_additional_minutes = 30

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_additional_minutes == 30


@pytest.mark.asyncio
async def test_set_target_program_with_none_additional_hours():
    """Тест установки целевой программы с None дополнительными часами."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_additional_hours = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_additional_hours == 0


@pytest.mark.asyncio
async def test_set_target_program_with_none_additional_minutes():
    """Тест установки целевой программы с None дополнительными минутами."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_additional_minutes = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_additional_minutes == 0


@pytest.mark.asyncio
async def test_set_target_program_with_none_temperature():
    """Тест установки целевой программы с None температурой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_program_with_none_main_hours():
    """Тест установки целевой программы с None часами приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_hours = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_main_hours == 0


@pytest.mark.asyncio
async def test_set_target_program_with_none_main_minutes():
    """Тест установки целевой программы с None минутами приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_minutes = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_main_minutes == 0


@pytest.mark.asyncio
async def test_set_target_program_with_none_subprogram_id():
    """Тест установки целевой программы с None подпрограммой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_subprogram_id = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_subprogram_id is None


def test_get_delayed_start_parameters():
    """Тест получения параметров отложенного старта."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест без установленных значений
    target_additional_hours, target_additional_minutes = controller._get_delayed_start_parameters()
    assert target_additional_hours == 0
    assert target_additional_minutes == 0
    
    # Тест с установленными значениями
    controller._target_additional_hours = 2
    controller._target_additional_minutes = 30
    target_additional_hours, target_additional_minutes = controller._get_delayed_start_parameters()
    assert target_additional_hours == 2
    assert target_additional_minutes == 30


def test_get_cooking_parameters():
    """Тест получения параметров приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=1):
        with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
            controller._target_program_name = "multi_chef"
            controller._target_temperature = 90
            controller._target_main_hours = 1
            controller._target_main_minutes = 30
            controller._target_subprogram_id = 0
            
            result = controller._get_cooking_parameters("multi_chef")
            assert result == [1, 0, 90, 1, 30]


def test_get_cooking_parameters_none_subprogram_defaults_to_zero():
    """Тест _get_cooking_parameters: None подпрограмма трактуется как 0 (RMC-M92S)."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 6
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_subprogram_id = None

    with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=1):
        with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {6: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
            controller._target_program_name = "multi_chef"
            controller._target_temperature = 90
            controller._target_main_hours = 1
            controller._target_main_minutes = 30

            result = controller._get_cooking_parameters("multi_chef")
            assert result == [1, 0, 90, 1, 30]


def test_get_program_parameters():
    """Тест получения параметров программы."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=0):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_NAMES', {3: ["multi_chef"]}):
                    result = controller._get_program_parameters("multi_chef")
                    # Проверяем, что возвращаются значения из PROGRAM_DATA
                    assert result == (100, 1, 30)


def test_get_auto_warm_flag():
    """Тест получения флага автоподогрева."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест с включенным автоподогревом
    controller._auto_warm_enabled = True
    assert controller._get_auto_warm_flag() == 1
    
    # Тест с выключенным автоподогревом
    controller._auto_warm_enabled = False
    assert controller._get_auto_warm_flag() == 0


def test_get_standby_program_name():
    """Тест получения названия программы ожидания."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Мокаем метод
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        result = controller._get_standby_program_name()
        assert result == "standby"


def test_get_constant_by_name():
    """Тест получения константы по названию программы."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Мокаем метод
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        result = controller._get_constant_by_name("multi_chef")
        assert result == "multi_chef"


@pytest.mark.asyncio
async def test_execute_cooking_sequence():
    """Тест выполнения последовательности приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            controller._status = None
            controller._target_program_name = "multi_chef"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called_once()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_standby():
    """Тест выполнения последовательности приготовления в режиме ожидания."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value=PROGRAM_STANDBY):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            mock_status = MagicMock()
            mock_status.is_on = False
            mock_status.program_id = None
            controller._status = mock_status
            controller._target_program_name = "standby"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called_once()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_same_program():
    """Тест выполнения последовательности приготовления с совпадающей программой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            mock_status = MagicMock()
            mock_status.is_on = True
            mock_status.program_id = 1
            controller._status = mock_status
            controller._target_program_name = "multi_chef"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_not_called()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_different_program():
    """Тест выполнения последовательности приготовления с разными программами."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            mock_status = MagicMock()
            mock_status.is_on = True
            mock_status.program_id = 2
            controller._status = mock_status
            controller._target_program_name = "multi_chef"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called_once()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cooking_sequence_unknown_state():
    """Тест выполнения последовательности приготовления в неизвестном состоянии."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            mock_status = MagicMock()
            mock_status.is_on = False
            mock_status.program_id = None
            controller._status = mock_status
            controller._target_program_name = "multi_chef"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_start_delayed():
    """Тест запуска приготовления с отложенным стартом."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.disconnect_if_need = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=1):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    with patch.object(controller, '_execute_cooking_sequence', new_callable=AsyncMock) as mock_execute:
                        await controller.start_delayed()

    mock_connection_manager.connect_if_need.assert_called_once()
    mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_start_delayed_standby():
    """Тест запуска приготовления с отложенным стартом в режиме ожидания."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        controller._target_program_name = "standby"
        await controller.start_delayed()

    # Проверяем, что ничего не произошло
    assert controller._target_program_name == "standby"


def test_target_temperature_property():
    """Тест свойства target_temperature."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки температуры
    controller.target_temperature = 90
    assert controller._target_temperature == 90
    
    # Тест получения температуры
    assert controller.target_temperature == 90


def test_target_program_name_property():
    """Тест свойства target_program_name."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки программы
    controller.target_program_name = "multi_chef"
    assert controller._target_program_name == "multi_chef"
    
    # Тест получения программы
    assert controller.target_program_name == "multi_chef"


def test_target_main_hours_property():
    """Тест свойства target_main_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки часов
    controller.target_main_hours = 1
    assert controller._target_main_hours == 1
    
    # Тест получения часов
    assert controller.target_main_hours == 1


def test_target_main_minutes_property():
    """Тест свойства target_main_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки минут
    controller.target_main_minutes = 30
    assert controller._target_main_minutes == 30
    
    # Тест получения минут
    assert controller.target_main_minutes == 30


def test_target_additional_hours_property():
    """Тест свойства target_additional_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки часов
    controller.target_additional_hours = 2
    assert controller._target_additional_hours == 2
    
    # Тест получения часов
    assert controller.target_additional_hours == 2


def test_target_additional_minutes_property():
    """Тест свойства target_additional_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки минут
    controller.target_additional_minutes = 30
    assert controller._target_additional_minutes == 30
    
    # Тест получения минут
    assert controller.target_additional_minutes == 30


def test_auto_warm_enabled_property():
    """Тест свойства auto_warm_enabled."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки автоподогрева
    controller.auto_warm_enabled = True
    assert controller._auto_warm_enabled is True
    
    # Тест получения автоподогрева
    assert controller.auto_warm_enabled is True


def test_status_property():
    """Тест свойства status."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест установки статуса
    mock_status = MagicMock()
    controller.status = mock_status
    assert controller._status == mock_status
    
    # Тест получения статуса
    assert controller.status == mock_status


def test_current_program_id_property():
    """Тест свойства current_program_id."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест без статуса
    assert controller.current_program_id is None
    
    # Тест со статусом
    mock_status = MagicMock()
    mock_status.is_on = True
    mock_status.program_id = 1
    controller._status = mock_status
    assert controller.current_program_id == 1


def test_last_set_target_property():
    """Тест свойства last_set_target."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    
    controller = SkyCookerCookingController(mock_connection_manager)
    
    # Тест получения времени
    assert controller.last_set_target == 0


@pytest.mark.asyncio
async def test_select_program_none():
    """Тест выбора программы PROGRAM_NONE."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="none_program"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants', return_value=[PROGRAM_NONE]):
                with pytest.raises(ValueError):
                    await controller.select_program(0, 0)


@pytest.mark.asyncio
async def test_select_program_standby():
    """Тест выбора программы PROGRAM_STANDBY."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_constants', return_value=[PROGRAM_STANDBY]):
                await controller.select_program(0, 0)

    assert controller._target_temperature == 100
    assert controller._target_main_hours == 0
    assert controller._target_main_minutes == 0
    assert controller._target_additional_hours == 0
    assert controller._target_additional_minutes == 0


@pytest.mark.asyncio
async def test_select_program_with_temperature():
    """Тест выбора программы с температурой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    await controller.select_program(1, 0)

    assert controller._target_temperature == 100




@pytest.mark.asyncio
async def test_select_program_with_additional_time():
    """Тест выбора программы с дополнительным временем."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    await controller.select_program(1, 0)

    assert controller._target_additional_hours == 0
    assert controller._target_additional_minutes == 0


@pytest.mark.asyncio
async def test_execute_cooking_sequence_unknown_state():
    """Тест выполнения последовательности приготовления в неизвестном состоянии."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            mock_status = MagicMock()
            mock_status.is_on = False
            mock_status.program_id = None
            controller._status = mock_status
            controller._target_program_name = "multi_chef"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_start_delayed():
    """Тест запуска приготовления с отложенным стартом."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.disconnect_if_need = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=1):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    with patch.object(controller, '_execute_cooking_sequence', new_callable=AsyncMock) as mock_execute:
                        await controller.start_delayed()

    mock_connection_manager.connect_if_need.assert_called_once()
    mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_start_delayed_standby():
    """Тест запуска приготовления с отложенным стартом в режиме ожидания."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        controller._target_program_name = "standby"
        await controller.start_delayed()

    # Проверяем, что ничего не произошло
    assert controller._target_program_name == "standby"


def test_target_temperature_property():
    """Тест свойства target_temperature."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки температуры
    controller.target_temperature = 90
    assert controller._target_temperature == 90

    # Тест получения температуры
    assert controller.target_temperature == 90


def test_target_program_name_property():
    """Тест свойства target_program_name."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки программы
    controller.target_program_name = "multi_chef"
    assert controller._target_program_name == "multi_chef"

    # Тест получения программы
    assert controller.target_program_name == "multi_chef"


def test_target_main_hours_property():
    """Тест свойства target_main_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки часов
    controller.target_main_hours = 1
    assert controller._target_main_hours == 1

    # Тест получения часов
    assert controller.target_main_hours == 1


def test_target_main_minutes_property():
    """Тест свойства target_main_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки минут
    controller.target_main_minutes = 30
    assert controller._target_main_minutes == 30

    # Тест получения минут
    assert controller.target_main_minutes == 30


def test_target_additional_hours_property():
    """Тест свойства target_additional_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки часов
    controller.target_additional_hours = 2
    assert controller._target_additional_hours == 2

    # Тест получения часов
    assert controller.target_additional_hours == 2


def test_target_additional_minutes_property():
    """Тест свойства target_additional_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки минут
    controller.target_additional_minutes = 30
    assert controller._target_additional_minutes == 30

    # Тест получения минут
    assert controller.target_additional_minutes == 30


def test_auto_warm_enabled_property():
    """Тест свойства auto_warm_enabled."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки автоподогрева
    controller.auto_warm_enabled = True
    assert controller._auto_warm_enabled is True

    # Тест получения автоподогрева
    assert controller.auto_warm_enabled is True


def test_status_property():
    """Тест свойства status."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки статуса
    mock_status = MagicMock()
    controller.status = mock_status
    assert controller._status == mock_status

    # Тест получения статуса
    assert controller.status == mock_status


def test_current_program_id_property():
    """Тест свойства current_program_id."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест без статуса
    assert controller.current_program_id is None

    # Тест со статусом
    mock_status = MagicMock()
    mock_status.is_on = True
    mock_status.program_id = 1
    controller._status = mock_status
    assert controller.current_program_id == 1


def test_last_set_target_property():
    """Тест свойства last_set_target."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест получения времени
    assert controller.last_set_target == 0


@pytest.mark.asyncio
async def test_set_target_temp_none_value():
    """Тест установки целевой температуры с None значением."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None

    await controller.set_target_temp(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_program_none_temperature():
    """Тест установки целевой программы с None температурой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_program_none_main_hours():
    """Тест установки целевой программы с None часами приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_hours = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_main_hours == 0


@pytest.mark.asyncio
async def test_set_target_program_none_main_minutes():
    """Тест установки целевой программы с None минутами приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_minutes = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_main_minutes == 0


@pytest.mark.asyncio
async def test_set_target_program_none_subprogram_id():
    """Тест установки целевой программы с None подпрограммой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_subprogram_id = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_subprogram_id is None


@pytest.mark.asyncio
async def test_set_target_temp_none_value():
    """Тест установки целевой температуры с None значением."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None

    await controller.set_target_temp(90)

    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_program_none_temperature():
    """Тест установки целевой программы с None температурой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_temperature = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_temperature == 90


@pytest.mark.asyncio
async def test_set_target_program_none_main_hours():
    """Тест установки целевой программы с None часами приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_hours = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_main_hours == 0


@pytest.mark.asyncio
async def test_set_target_program_none_main_minutes():
    """Тест установки целевой программы с None минутами приготовления."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_main_minutes = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_main_minutes == 0


@pytest.mark.asyncio
async def test_set_target_program_none_subprogram_id():
    """Тест установки целевой программы с None подпрограммой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)
    controller._target_subprogram_id = None

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id_by_const', return_value=1):
            with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                with patch('custom_components.skycooker.skycooker_cooking_controller.is_mode_supported', return_value=True):
                    await controller.set_target_program("multi_chef")

    assert controller._target_program_name == "multi_chef"
    assert controller._target_subprogram_id is None


@pytest.mark.asyncio
async def test_execute_cooking_sequence_unknown_state():
    """Тест выполнения последовательности приготовления в неизвестном состоянии."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.select_program = AsyncMock()
    mock_connection_manager.set_main_program = AsyncMock()
    mock_connection_manager.turn_on = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_constant_by_name', return_value="multi_chef"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
            mock_status = MagicMock()
            mock_status.is_on = False
            mock_status.program_id = None
            controller._status = mock_status
            controller._target_program_name = "multi_chef"
            await controller._execute_cooking_sequence(1, 0, 90, 1, 30, 0, 0, 1)

    mock_connection_manager.select_program.assert_called()
    mock_connection_manager.set_main_program.assert_called_once()
    mock_connection_manager.turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_start_delayed():
    """Тест запуска приготовления с отложенным стартом."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.disconnect_if_need = AsyncMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        with patch('custom_components.skycooker.skycooker_cooking_controller.get_program_name', return_value="multi_chef"):
            with patch('custom_components.skycooker.skycooker_cooking_controller.find_program_id', return_value=1):
                with patch('custom_components.skycooker.skycooker_cooking_controller.PROGRAM_DATA', {3: [{"temperature": 100, "hours": 1, "minutes": 30}]}):
                    with patch.object(controller, '_execute_cooking_sequence', new_callable=AsyncMock) as mock_execute:
                        await controller.start_delayed()

    mock_connection_manager.connect_if_need.assert_called_once()
    mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_start_delayed_standby():
    """Тест запуска приготовления с отложенным стартом в режиме ожидания."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.connected = True

    controller = SkyCookerCookingController(mock_connection_manager)

    # Мокаем методы
    with patch('custom_components.skycooker.skycooker_cooking_controller.get_standby_program_name', return_value="standby"):
        controller._target_program_name = "standby"
        await controller.start_delayed()

    # Проверяем, что ничего не произошло
    assert controller._target_program_name == "standby"


def test_target_temperature_property():
    """Тест свойства target_temperature."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки температуры
    controller.target_temperature = 90
    assert controller._target_temperature == 90

    # Тест получения температуры
    assert controller.target_temperature == 90


def test_target_program_name_property():
    """Тест свойства target_program_name."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки программы
    controller.target_program_name = "multi_chef"
    assert controller._target_program_name == "multi_chef"

    # Тест получения программы
    assert controller.target_program_name == "multi_chef"


def test_target_main_hours_property():
    """Тест свойства target_main_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки часов
    controller.target_main_hours = 1
    assert controller._target_main_hours == 1

    # Тест получения часов
    assert controller.target_main_hours == 1


def test_target_main_minutes_property():
    """Тест свойства target_main_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки минут
    controller.target_main_minutes = 30
    assert controller._target_main_minutes == 30

    # Тест получения минут
    assert controller.target_main_minutes == 30


def test_target_additional_hours_property():
    """Тест свойства target_additional_hours."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки часов
    controller.target_additional_hours = 2
    assert controller._target_additional_hours == 2

    # Тест получения часов
    assert controller.target_additional_hours == 2


def test_target_additional_minutes_property():
    """Тест свойства target_additional_minutes."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки минут
    controller.target_additional_minutes = 30
    assert controller._target_additional_minutes == 30

    # Тест получения минут
    assert controller.target_additional_minutes == 30


def test_auto_warm_enabled_property():
    """Тест свойства auto_warm_enabled."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки автоподогрева
    controller.auto_warm_enabled = True
    assert controller._auto_warm_enabled is True

    # Тест получения автоподогрева
    assert controller.auto_warm_enabled is True


def test_status_property():
    """Тест свойства status."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест установки статуса
    mock_status = MagicMock()
    controller.status = mock_status
    assert controller._status == mock_status

    # Тест получения статуса
    assert controller.status == mock_status


def test_current_program_id_property():
    """Тест свойства current_program_id."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест без статуса
    assert controller.current_program_id is None

    # Тест со статусом
    mock_status = MagicMock()
    mock_status.is_on = True
    mock_status.program_id = 1
    controller._status = mock_status
    assert controller.current_program_id == 1


def test_last_set_target_property():
    """Тест свойства last_set_target."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.model_id = 3
    mock_connection_manager.hass = MagicMock()

    controller = SkyCookerCookingController(mock_connection_manager)

    # Тест получения времени
    assert controller.last_set_target == 0