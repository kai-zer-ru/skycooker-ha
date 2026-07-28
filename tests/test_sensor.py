# Тесты для модуля sensor.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.sensor import SkyCookerSensor, async_setup_entry
from custom_components.skycooker.const import (
    SENSOR_TYPE_STATUS,
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPE_REMAINING_TIME,
    SENSOR_TYPE_COOKING_TIME,
    SENSOR_TYPE_AUTO_WARM_TIME,
    SENSOR_TYPE_SUCCESS_RATE,
    SENSOR_TYPE_DELAYED_LAUNCH_TIME,
    SENSOR_TYPE_CURRENT_PROGRAM,
    SENSOR_TYPE_SUBPROGRAM,
    DOMAIN,
    DATA_CONNECTION,
    STATUS_OFF
)


def test_sensor_initialization():
    """Тест инициализации сенсора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    
    assert sensor_entity is not None
    assert sensor_entity.sensor_type == SENSOR_TYPE_STATUS


@pytest.mark.asyncio
async def test_async_setup_entry():
    """Тест настройки сенсоров."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1
    mock_hass.data = {
        DOMAIN: {
            mock_entry.entry_id: {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    mock_async_add_entities = AsyncMock()
    
    await async_setup_entry(mock_hass, mock_entry, mock_async_add_entities)
    
    # Проверяем, что сущности были добавлены
    assert mock_async_add_entities.call_count == 1
    entities = mock_async_add_entities.call_args[0][0]
    # 8 базовых + 1 подпрограмма + 2 диагностических (error_code, sound_enabled)
    assert len(entities) == 11


def test_sensor_unique_id():
    """Тест уникального идентификатора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    
    assert sensor_entity.unique_id == "test_entry_" + SENSOR_TYPE_STATUS


def test_sensor_name():
    """Тест имени сенсора."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"friendly_name": "RMC-M40S"}
    mock_skycooker = MagicMock()
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    sensor_types_names = {
        SENSOR_TYPE_STATUS: ("Status", "Статус"),
        SENSOR_TYPE_TEMPERATURE: ("Temperature", "Температура"),
        SENSOR_TYPE_REMAINING_TIME: ("Remaining time", "Оставшееся время"),
        SENSOR_TYPE_COOKING_TIME: ("Cooking time", "Время приготовления"),
        SENSOR_TYPE_AUTO_WARM_TIME: ("Auto warm time", "Время автоподогрева"),
        SENSOR_TYPE_SUCCESS_RATE: ("Success rate", "Процент успеха"),
        SENSOR_TYPE_DELAYED_LAUNCH_TIME: ("Delayed launch time", "Время до отложенного запуска"),
        SENSOR_TYPE_CURRENT_PROGRAM: ("Current mode", "Текущий режим"),
        SENSOR_TYPE_SUBPROGRAM: ("Current subprogram", "Текущая подпрограмма"),
    }
    for sensor_type, (en_name, ru_name) in sensor_types_names.items():
        sensor = SkyCookerSensor(mock_hass, mock_entry, sensor_type)
        assert en_name in sensor.name or ru_name in sensor.name or "SkyCooker" in sensor.name


def test_sensor_icon():
    """Тест иконки сенсора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    assert sensor_entity.icon == "mdi:information"
    
    sensor_entity.sensor_type = SENSOR_TYPE_TEMPERATURE
    assert sensor_entity.icon == "mdi:thermometer"


def test_sensor_entity_category():
    """Тест категории сущности."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_SUCCESS_RATE)
    assert sensor_entity.entity_category == "diagnostic"
    
    sensor_entity.sensor_type = SENSOR_TYPE_STATUS
    assert sensor_entity.entity_category is None


def test_sensor_device_class():
    """Тест класса устройства."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor_entity.device_class == "temperature"
    
    sensor_entity.sensor_type = SENSOR_TYPE_STATUS
    assert sensor_entity.device_class is None


def test_sensor_state_class():
    """Тест класса состояния."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor_entity.state_class == "measurement"
    
    sensor_entity.sensor_type = SENSOR_TYPE_STATUS
    assert sensor_entity.state_class is None


def test_sensor_native_unit_of_measurement():
    """Тест единицы измерения."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor_entity.native_unit_of_measurement == "°C"
    
    sensor_entity.sensor_type = SENSOR_TYPE_SUCCESS_RATE
    assert sensor_entity.native_unit_of_measurement == "%"
    
    sensor_entity.sensor_type = SENSOR_TYPE_STATUS
    assert sensor_entity.native_unit_of_measurement is None


def test_sensor_available():
    """Тест доступности сенсора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.available = True
    mock_skycooker.status = MagicMock()
    mock_skycooker.status_code = 1
    mock_skycooker.target_temperature = 100
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30
    mock_skycooker.target_additional_hours = 2
    mock_skycooker.target_additional_minutes = 15
    mock_skycooker.success_rate = 75
    mock_skycooker.status.subprogram_id = 1
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_TEMPERATURE
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_REMAINING_TIME
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_COOKING_TIME
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_AUTO_WARM_TIME
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_SUCCESS_RATE
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_DELAYED_LAUNCH_TIME
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_CURRENT_PROGRAM
    assert sensor_entity.available is True
    
    sensor_entity.sensor_type = SENSOR_TYPE_SUBPROGRAM
    assert sensor_entity.available is True


def test_sensor_native_value():
    """Тест состояния сенсора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.status = MagicMock()
    mock_skycooker.status_code = STATUS_OFF
    mock_skycooker.target_temperature = 100
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30
    mock_skycooker.target_additional_hours = 2
    mock_skycooker.target_additional_minutes = 15
    mock_skycooker.success_rate = 75
    mock_skycooker.status.subprogram_id = 1
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    sensor_entity = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    
    # Мокаем get_status_text
    with patch('custom_components.skycooker.sensor.get_status_text', return_value="Off"):
        assert sensor_entity.native_value == "Off"
    
    sensor_entity.sensor_type = SENSOR_TYPE_TEMPERATURE
    assert sensor_entity.native_value == 0
    
    mock_skycooker.status_code = 1
    assert sensor_entity.native_value == 100
    
    sensor_entity.sensor_type = SENSOR_TYPE_REMAINING_TIME
    with patch('custom_components.skycooker.sensor.calculate_remaining_time', return_value="1 hour"):
        assert sensor_entity.native_value == "1 hour"
    
    sensor_entity.sensor_type = SENSOR_TYPE_COOKING_TIME
    with patch('custom_components.skycooker.sensor.get_cooking_time', return_value="1:30"):
        assert sensor_entity.native_value == "1:30"
    
    sensor_entity.sensor_type = SENSOR_TYPE_AUTO_WARM_TIME
    with patch('custom_components.skycooker.sensor.get_auto_warm_time', return_value="2:15"):
        assert sensor_entity.native_value == "2:15"
    
    sensor_entity.sensor_type = SENSOR_TYPE_SUCCESS_RATE
    assert sensor_entity.native_value == 75
    
    sensor_entity.sensor_type = SENSOR_TYPE_DELAYED_LAUNCH_TIME
    with patch('custom_components.skycooker.sensor.get_delayed_launch_time', return_value="2:15"):
        assert sensor_entity.native_value == "2:15"
    
    sensor_entity.sensor_type = SENSOR_TYPE_CURRENT_PROGRAM
    with patch('custom_components.skycooker.sensor.get_current_program_text', return_value="Program 1"):
        assert sensor_entity.native_value == "Program 1"
    
    sensor_entity.sensor_type = SENSOR_TYPE_SUBPROGRAM
    assert sensor_entity.native_value == "1"


def test_sensor_name_unknown_type():
    """Тест имени сенсора с неизвестным типом (fallback)."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"friendly_name": "RMC-M40S"}
    mock_skycooker = MagicMock()
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    sensor = SkyCookerSensor(mock_hass, mock_entry, "unknown_sensor_type")
    assert "SkyCooker" in sensor.name


def test_sensor_last_reset():
    """Тест last_reset сенсора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    sensor = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    assert sensor.last_reset is None


def test_sensor_icon_all_types():
    """Тест иконок для всех типов сенсоров."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    icons = {
        SENSOR_TYPE_STATUS: "mdi:information",
        SENSOR_TYPE_TEMPERATURE: "mdi:thermometer",
        SENSOR_TYPE_REMAINING_TIME: "mdi:timer",
        SENSOR_TYPE_COOKING_TIME: "mdi:clock",
        SENSOR_TYPE_AUTO_WARM_TIME: "mdi:clock-start",
        SENSOR_TYPE_SUCCESS_RATE: "mdi:bluetooth-connect",
        SENSOR_TYPE_DELAYED_LAUNCH_TIME: "mdi:timer-sand",
        SENSOR_TYPE_CURRENT_PROGRAM: "mdi:chef-hat",
        SENSOR_TYPE_SUBPROGRAM: "mdi:cog-outline",
    }
    for sensor_type, expected_icon in icons.items():
        sensor = SkyCookerSensor(mock_hass, mock_entry, sensor_type)
        assert sensor.icon == expected_icon


def test_sensor_available_unavailable_skycooker():
    """Тест доступности при недоступном skycooker."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.available = False
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    sensor = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    assert sensor.available is False


def test_sensor_native_value_temperature_none():
    """Тест native_value температуры при target_temperature=None."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.status = MagicMock()
    mock_skycooker.status_code = 1
    mock_skycooker.target_temperature = None
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    sensor = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_TEMPERATURE)
    assert sensor.native_value == 0


def test_sensor_native_value_status_no_status():
    """Тест native_value статуса при отсутствии status."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.status = None
    mock_skycooker.status_code = None
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    sensor = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_STATUS)
    with patch('custom_components.skycooker.sensor.get_status_text', return_value="Unknown"):
        assert sensor.native_value == "Unknown"


def test_sensor_native_value_subprogram_none():
    """Тест native_value подпрограммы при subprogram_id=None."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_status = MagicMock()
    mock_status.subprogram_id = None
    mock_skycooker.status = mock_status
    mock_skycooker.available = True
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    sensor = SkyCookerSensor(mock_hass, mock_entry, SENSOR_TYPE_SUBPROGRAM)
    assert sensor.native_value == "0"


def test_sensor_available_unknown_type():
    """Тест available для сенсора с неизвестным типом."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.available = True
    mock_skycooker.status_code = 1
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    sensor = SkyCookerSensor(mock_hass, mock_entry, "unknown_sensor_type")
    assert sensor.available is False


def test_sensor_native_value_unknown_type():
    """Тест native_value для сенсора с неизвестным типом."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.available = True
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    sensor = SkyCookerSensor(mock_hass, mock_entry, "unknown_sensor_type")
    assert sensor.native_value is None