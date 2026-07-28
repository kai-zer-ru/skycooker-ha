# Тесты для модуля time.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.time import (
    _validate_hours,
    _validate_minutes,
    sync_time,
    get_time,
    _get_time_str,
    format_time,
    get_time_options,
    get_time_from_status,
    _normalize_time,
    calculate_remaining_time,
    get_cooking_time,
    get_auto_warm_time,
    get_delayed_launch_time
)
from custom_components.skycooker.const import (
    STATUS_DELAYED_LAUNCH,
    STATUS_WARMING,
    STATUS_COOKING,
    STATUS_AUTO_WARM,
    Status
)


def test_validate_hours():
    """Тест валидации часов."""
    assert _validate_hours(10) == 10
    assert _validate_hours(25) == 23
    assert _validate_hours(23) == 23


def test_validate_minutes():
    """Тест валидации минут."""
    assert _validate_minutes(30) == 30
    assert _validate_minutes(65) == 59
    assert _validate_minutes(59) == 59


@pytest.mark.asyncio
async def test_sync_time_success():
    """Тест успешной синхронизации времени."""
    mock_self = MagicMock()
    mock_self.command = AsyncMock(return_value=bytes([0]))
    
    await sync_time(mock_self)
    
    mock_self.command.assert_called_once()


@pytest.mark.asyncio
async def test_sync_time_failure():
    """Тест неудачной синхронизации времени."""
    mock_self = MagicMock()
    mock_self.command = AsyncMock(return_value=bytes([1]))

    await sync_time(mock_self)

    mock_self.command.assert_called_once()


@pytest.mark.asyncio
async def test_sync_time_exception():
    """Тест синхронизации времени при исключении."""
    mock_self = MagicMock()
    mock_self.command = AsyncMock(side_effect=Exception("BLE error"))

    await sync_time(mock_self)

    mock_self.command.assert_called_once()


@pytest.mark.asyncio
async def test_get_time():
    """Тест получения времени."""
    mock_self = MagicMock()
    # Используем pack для создания корректных байтов
    import struct
    mock_self.command = AsyncMock(return_value=struct.pack("<ii", 1234567890, 10800))
    
    result = await get_time(mock_self)
    
    assert result == (1234567890, 10800)


def test_get_time_str():
    """Тест форматирования строки времени."""
    mock_hass_ru = MagicMock()
    mock_hass_ru.config.language = "ru"
    mock_hass_en = MagicMock()
    mock_hass_en.config.language = "en"

    # Тест на русском
    result = _get_time_str(1, 30, mock_hass_ru)
    assert result == "1 ч. 30 м."

    # Тест на английском
    result = _get_time_str(1, 30, mock_hass_en)
    assert result == "1 h. 30 m."

    # Тест с отрицательными значениями (нормализуются в 0)
    result = _get_time_str(-1, -5, mock_hass_ru)
    assert result == "0 ч. 0 м."


def test_format_time():
    """Тест форматирования времени."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    
    result = format_time(mock_hass, 1, 30)
    assert result == "1 ч. 30 м."
    
    mock_hass.config.language = "en"
    result = format_time(mock_hass, 1, 30)
    assert result == "1 h. 30 m."


def test_get_time_options():
    """Тест получения опций для времени."""
    # Тест для часов
    result = get_time_options(hours=True)
    assert len(result) == 24
    assert result[0] == "0"
    assert result[23] == "23"
    
    # Тест для минут
    result = get_time_options(hours=False)
    assert len(result) == 60
    assert result[0] == "0"
    assert result[59] == "59"


def test_get_time_from_status():
    """Тест получения времени из статуса."""
    mock_skycooker = MagicMock()
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30

    # Тест с реальным Status (приоритет статуса над skycooker)
    mock_status = Status(
        program_id=0, subprogram_id=0, target_temperature=100, auto_warm=0,
        is_on=False, sound_enabled=False, parental_control=False, error_code=0,
        target_main_hours=2, target_main_minutes=45,
        target_additional_hours=1, target_additional_minutes=30,
        status=0, program_name="Test"
    )
    result = get_time_from_status(mock_skycooker, mock_status, 'target_main_hours')
    assert result == 2

    # Тест без статуса
    result = get_time_from_status(mock_skycooker, None, 'target_main_hours')
    assert result == 1

    # Тест с отсутствующим атрибутом
    result = get_time_from_status(mock_skycooker, None, 'target_main_minutes', 30)
    assert result == 30


def test_normalize_time():
    """Тест нормализации времени."""
    # Тест с нормальными значениями
    result = _normalize_time(1, 30)
    assert result == (1, 30)
    
    # Тест с переполнением минут
    result = _normalize_time(1, 65)
    assert result == (2, 5)
    
    # Тест с переполнением часов
    result = _normalize_time(25, 30)
    assert result == (23, 30)
    
    # Тест с переполнением минут и часов
    result = _normalize_time(25, 65)
    assert result == (23, 5)

    # Тест с минутами 60 (граничный случай)
    result = _normalize_time(0, 60)
    assert result == (1, 0)

    # Тест с минутами > 59 после нормализации (часы 24, минуты 59)
    result = _normalize_time(24, 59)
    assert result == (23, 59)


def test_calculate_remaining_time():
    """Тест расчета оставшегося времени."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_skycooker = MagicMock()
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30
    mock_skycooker.target_additional_hours = 2
    mock_skycooker.target_additional_minutes = 15
    mock_status = MagicMock()
    mock_status.target_main_hours = 1
    mock_status.target_main_minutes = 30
    mock_status.target_additional_hours = 2
    mock_status.target_additional_minutes = 15
    
    # Тест для отложенного запуска
    result = calculate_remaining_time(mock_hass, mock_skycooker, STATUS_DELAYED_LAUNCH)
    assert result == "3 ч. 45 м."
    
    # Тест для разогрева
    result = calculate_remaining_time(mock_hass, mock_skycooker, STATUS_WARMING)
    assert result == "2 ч. 15 м."
    
    # Тест для готовки
    result = calculate_remaining_time(mock_hass, mock_skycooker, STATUS_COOKING)
    assert result == "2 ч. 15 м."
    
    # Тест для других статусов
    result = calculate_remaining_time(mock_hass, mock_skycooker, 0)
    assert result == "0 ч. 0 м."


def test_get_cooking_time():
    """Тест получения времени приготовления."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_skycooker = MagicMock()
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30
    mock_status = MagicMock()
    mock_status.target_main_hours = 1
    mock_status.target_main_minutes = 30
    
    # Тест для отложенного запуска
    result = get_cooking_time(mock_hass, mock_skycooker, STATUS_DELAYED_LAUNCH)
    assert result == "1 ч. 30 м."
    
    # Тест для разогрева
    result = get_cooking_time(mock_hass, mock_skycooker, STATUS_WARMING)
    assert result == "1 ч. 30 м."
    
    # Тест для готовки
    result = get_cooking_time(mock_hass, mock_skycooker, STATUS_COOKING)
    assert result == "1 ч. 30 м."
    
    # Тест для других статусов
    result = get_cooking_time(mock_hass, mock_skycooker, 0)
    assert result == "0 ч. 0 м."


def test_get_auto_warm_time():
    """Тест получения времени автоподогрева."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_skycooker = MagicMock()
    mock_skycooker.target_additional_hours = 2
    mock_skycooker.target_additional_minutes = 15
    mock_status = MagicMock()
    mock_status.target_additional_hours = 2
    mock_status.target_additional_minutes = 15
    
    # Тест для автоподогрева
    result = get_auto_warm_time(mock_hass, mock_skycooker, STATUS_AUTO_WARM)
    assert result == "2 ч. 15 м."
    
    # Тест для других статусов
    result = get_auto_warm_time(mock_hass, mock_skycooker, 0)
    assert result == "0 ч. 0 м."


def test_get_delayed_launch_time():
    """Тест получения времени до отложенного запуска."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_skycooker = MagicMock()
    mock_skycooker.target_additional_hours = 2
    mock_skycooker.target_additional_minutes = 15
    mock_status = MagicMock()
    mock_status.target_additional_hours = 2
    mock_status.target_additional_minutes = 15
    
    # Тест для отложенного запуска
    result = get_delayed_launch_time(mock_hass, mock_skycooker, STATUS_DELAYED_LAUNCH)
    assert result == "2 ч. 15 м."
    
    # Тест для других статусов
    result = get_delayed_launch_time(mock_hass, mock_skycooker, 0)
    assert result == "0 ч. 0 м."