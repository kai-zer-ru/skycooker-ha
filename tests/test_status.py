# Тесты для модуля status.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.status import get_status_text, get_status
from custom_components.skycooker.const import COMMAND_GET_STATUS, Status
from custom_components.skycooker.skycooker import SkyCookerError


def test_get_status_text():
    """Тест получения текста статуса."""
    # Тест с None
    mock_hass = MagicMock()
    mock_hass.config.language = "en"
    result = get_status_text(mock_hass, None)
    assert result == "Unknown"

    mock_hass.config.language = "ru"
    result = get_status_text(mock_hass, None)
    assert result == "Неизвестно"

    # Тест с известным кодом статуса и переводами
    mock_hass.data = {"skycooker_translations": {"status_codes": {"off": "Выключена"}}}
    result = get_status_text(mock_hass, 0)
    assert result == "Выключена"

    # Тест с fallback переводами (пустой status_codes)
    mock_hass.data = {"skycooker_translations": {"status_codes": {}}}
    mock_hass.config.language = "ru"
    result = get_status_text(mock_hass, 0)
    assert result == "Выключена"

    mock_hass.config.language = "en"
    result = get_status_text(mock_hass, 1)
    assert result == "Waiting"

    mock_hass.config.language = "ru"
    result = get_status_text(mock_hass, 4)
    assert result == "Ожидание загрузки продуктов"

    mock_hass.config.language = "en"
    result = get_status_text(mock_hass, 7)
    assert result == "Error"

    # Тест с неизвестным кодом статуса
    mock_hass.config.language = "en"
    result = get_status_text(mock_hass, 999)
    assert result == "Unknown (999)"

    mock_hass.config.language = "ru"
    result = get_status_text(mock_hass, 999)
    assert result == "Неизвестно (999)"


@pytest.mark.asyncio
async def test_get_status_success():
    """Тест успешного получения статуса."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.hass.config.language = "en"
    mock_connection_manager.model_id = 1
    
    # Мокаем команду
    mock_connection_manager.command = AsyncMock(return_value=bytes([
        1,  # program_id
        2,  # subprogram_id
        100,  # target_temperature
        1,  # target_main_hours
        30,  # target_main_minutes
        2,  # target_additional_hours
        15,  # target_additional_minutes
        1,  # auto_warm
        1,  # status
        1,  # sound_enabled
        0, 0, 0, 0, 0, 0, 0  # остальные байты
    ]))
    
    # Мокаем get_program_name
    with patch('custom_components.skycooker.status.get_program_name', return_value="Program 1"):
        result = await get_status(mock_connection_manager)
    
    assert result is not None
    assert result.program_id == 1
    assert result.subprogram_id == 2
    assert result.target_temperature == 100
    assert result.target_main_hours == 1
    assert result.target_main_minutes == 30
    assert result.target_additional_hours == 2
    assert result.target_additional_minutes == 15
    assert result.auto_warm == 1
    assert result.status == 1
    assert result.is_on is True
    assert result.sound_enabled is True
    assert result.program_name == "Program 1"


@pytest.mark.asyncio
async def test_get_status_invalid_length():
    """Тест получения статуса с некорректной длиной."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.command = AsyncMock(return_value=bytes([1, 2, 3]))
    
    with pytest.raises(SkyCookerError) as excinfo:
        await get_status(mock_connection_manager)
    
    assert "Некорректный размер данных статуса" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_status_error():
    """Тест получения статуса с ошибкой."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.command = AsyncMock(side_effect=Exception("Test error"))

    with pytest.raises(Exception) as excinfo:
        await get_status(mock_connection_manager)

    assert "Test error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_status_parse_error():
    """Тест получения статуса с ошибкой парсинга."""
    mock_connection_manager = MagicMock()
    mock_connection_manager.hass = MagicMock()
    mock_connection_manager.model_id = 1
    mock_connection_manager.command = AsyncMock(return_value=bytes(16))

    with patch('custom_components.skycooker.status.get_program_name', side_effect=Exception("Parse error")):
        with pytest.raises(SkyCookerError) as excinfo:
            await get_status(mock_connection_manager)
        assert "Ошибка распаковки статуса" in str(excinfo.value)