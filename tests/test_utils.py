# Тесты для модуля utils.py
from unittest.mock import MagicMock
from custom_components.skycooker.utils import (
    get_base_name,
    get_lower_model_name,
    get_language_index,
    is_russian,
    get_localized_string,
    get_entity_name,
    get_temperature_options
)


def test_get_base_name():
    """Тест получения базового имени устройства."""
    mock_entry = MagicMock()
    mock_entry.data.get.return_value = "Test Device"
    
    result = get_base_name(mock_entry)
    assert result == "SkyCooker Test Device"
    
    mock_entry.data.get.return_value = ""
    result = get_base_name(mock_entry)
    assert result == "SkyCooker"


def test_get_lower_model_name():
    """Тест получения имени модели в нижнем регистре."""
    result = get_lower_model_name("Test-Device")
    assert result == "test_device"
    
    result = get_lower_model_name("AnotherDevice")
    assert result == "anotherdevice"


def test_get_language_index():
    """Тест получения индекса языка."""
    mock_hass = MagicMock()
    mock_hass.config.language = "en"
    
    result = get_language_index(mock_hass)
    assert result == 0
    
    mock_hass.config.language = "ru"
    result = get_language_index(mock_hass)
    assert result == 1


def test_is_russian():
    """Тест проверки русского языка."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    
    result = is_russian(mock_hass)
    assert result is True
    
    mock_hass.config.language = "en"
    result = is_russian(mock_hass)
    assert result is False


def test_get_localized_string():
    """Тест получения локализованной строки."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    
    result = get_localized_string(mock_hass, "English", "Русский")
    assert result == "Русский"
    
    mock_hass.config.language = "en"
    result = get_localized_string(mock_hass, "English", "Русский")
    assert result == "English"


def test_get_entity_name():
    """Тест получения имени сущности."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.data.get.return_value = "Test Device"
    
    mock_hass.config.language = "ru"
    result = get_entity_name(mock_hass, mock_entry, "test_type", "Test Name", "Тестовое имя")
    assert result == "SkyCooker Test Device Тестовое имя"
    
    mock_hass.config.language = "en"
    result = get_entity_name(mock_hass, mock_entry, "test_type", "Test Name", "Тестовое имя")
    assert result == "SkyCooker Test Device Test Name"


def test_get_temperature_options():
    """Тест получения опций для температуры."""
    result = get_temperature_options()
    assert isinstance(result, list)
    assert len(result) == 33
    assert result[0] == "40"
    assert result[-1] == "200"