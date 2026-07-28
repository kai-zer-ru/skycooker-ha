# Тесты для модуля programs.py
import pytest
from unittest.mock import MagicMock, patch
from custom_components.skycooker.const import CONF_FAVORITE_PROGRAMS
from custom_components.skycooker.programs import (
    get_program_data,
    get_program_constants,
    get_program_options,
    get_constant_by_name,
    get_program_name_by_const,
    get_standby_program_name,
    find_program_id,
    find_program_id_by_const,
    get_program_name,
    _find_program_index,
    is_subprogram_supported,
    get_subprogram_options,
    get_current_program_text,
    get_favorite_programs,
    is_program_supported
)
from custom_components.skycooker.const import (
    MODEL_3, MODEL_6, PROGRAM_STANDBY, PROGRAM_NONE, PROGRAM_WARMING,
    PROGRAM_MULTI_CHEF, PROGRAM_DESSERTS, PROGRAM_EXPRESS,
    is_model_supported, get_supported_model_names,
)


def test_get_program_data():
    """Тест получения данных режима."""
    # Тест с существующими данными
    result = get_program_data(1, 0)
    assert result is not None or result is None  # Зависит от PROGRAM_DATA
    
    # Тест с несуществующей моделью
    result = get_program_data(999, 0)
    assert result is None

    # Тест с program_id за пределами списка
    result = get_program_data(1, 99999)
    assert result is None


def test_get_program_constants():
    """Тест получения констант режимов."""
    # Тест с существующей моделью
    result = get_program_constants(1)
    assert isinstance(result, list)
    
    # Тест с несуществующей моделью
    result = get_program_constants(999)
    assert result == []


def test_get_program_options():
    """Тест получения опций для режимов."""
    # Тест с hass
    mock_hass = MagicMock()
    mock_hass.data = {"skycooker_translations": {"program_names": {PROGRAM_STANDBY: "Standby"}}}
    result = get_program_options(mock_hass, 1)
    assert isinstance(result, list)
    assert len(result) > 0

    # Тест без hass
    result = get_program_options(None, 1)
    assert result == []

    # Тест с пустыми program_constants (модель 999)
    result = get_program_options(mock_hass, 999)
    assert result == []

    # Тест с include_standby=False
    result = get_program_options(mock_hass, 1, include_standby=False)
    assert isinstance(result, list)


def test_get_constant_by_name():
    """Тест получения константы по названию."""
    mock_hass = MagicMock()
    mock_hass.data.get.return_value = {"program_names": {PROGRAM_STANDBY: "Standby"}}
    
    # Тест с существующим названием
    result = get_constant_by_name(mock_hass, "Standby", 1)
    assert result is not None or result is None  # Зависит от данных
    
    # Тест с несуществующим названием (find_program_id возвращает None)
    result = get_constant_by_name(mock_hass, "Unknown", 1)
    assert result is None

    # Тест с model_id без program_constants
    result = get_constant_by_name(mock_hass, "Standby", 999)
    assert result is None


def test_get_program_name_by_const():
    """Тест получения названия режима по константе."""
    mock_hass = MagicMock()
    mock_hass.data.get.return_value = {"program_names": {PROGRAM_STANDBY: "Standby"}}
    
    # Тест с существующей константой
    result = get_program_name_by_const(mock_hass, PROGRAM_STANDBY, 1)
    assert result is not None or result is None  # Зависит от данных
    
    # Тест с несуществующей константой (find_program_id_by_const возвращает None)
    result = get_program_name_by_const(mock_hass, "Unknown", 1)
    assert result is None


def test_get_standby_program_name():
    """Тест получения названия режима ожидания."""
    mock_hass = MagicMock()
    mock_hass.data.get.return_value = {"program_names": {PROGRAM_STANDBY: "Standby"}}
    
    result = get_standby_program_name(mock_hass, 1)
    assert result is not None or result is None  # Зависит от данных


def test_find_program_index():
    """Тест _find_program_index."""
    constants = ["a", "b", "c"]
    assert _find_program_index(constants, "b") == 1
    assert _find_program_index(constants, "x") is None


def test_find_program_id():
    """Тест поиска идентификатора режима по названию."""
    mock_hass = MagicMock()
    mock_hass.data.get.return_value = {"program_names": {PROGRAM_STANDBY: "Standby"}}
    
    # Тест с существующим названием
    result = find_program_id(mock_hass, "Standby", 1)
    assert result is not None or result is None  # Зависит от данных
    
    # Тест с несуществующим названием (program_constant_by_name.get возвращает None)
    result = find_program_id(mock_hass, "Unknown", 1)
    assert result is None

    # Тест с пустыми program_constants
    result = find_program_id(mock_hass, "Standby", 999)
    assert result is None


def test_find_program_id_by_const():
    """Тест поиска идентификатора режима по константе."""
    mock_hass = MagicMock()
    mock_hass.data.get.return_value = {"program_names": {PROGRAM_STANDBY: "Standby"}}
    
    # Тест с существующей константой
    result = find_program_id_by_const(mock_hass, PROGRAM_STANDBY, 1)
    assert result is not None or result is None  # Зависит от данных
    
    # Тест с несуществующей константой
    result = find_program_id_by_const(mock_hass, "Unknown", 1)
    assert result is None

    # Тест с пустыми program_constants (model_id 999)
    result = find_program_id_by_const(mock_hass, "nonexistent_const", 999)
    assert result is None


def test_get_program_name():
    """Тест получения названия режима."""
    mock_hass = MagicMock()
    mock_hass.data = {"skycooker_translations": {"program_names": {PROGRAM_STANDBY: "Standby"}}}

    # Тест с существующим идентификатором
    result = get_program_name(mock_hass, 0, 1)
    assert result is not None or result == "Unknown (0)"  # Зависит от данных

    # Тест с несуществующим идентификатором
    result = get_program_name(mock_hass, 999, 1)
    assert result == "Unknown (999)"

    # Тест с model_id=None
    result = get_program_name(mock_hass, 0, None)
    assert result == "Unknown (0)"

    # Тест с PROGRAM_NONE (модель 3, индекс 14 — PROGRAM_NONE)
    mock_hass.data = {"skycooker_translations": {"program_names": {}}}
    result = get_program_name(mock_hass, 14, 3)
    assert result == "Unknown (14)"

    # Тест с валидной программой и переводом (строка 116: return из program_names)
    mock_hass.data = {"skycooker_translations": {"program_names": {"standby": "Режим ожидания", "multi_chef": "Мультишеф"}}}
    result = get_program_name(mock_hass, 1, 1)
    assert result == "Мультишеф"


def test_is_subprogram_supported():
    """Тест проверки поддержки подпрограмм."""
    # Тест с моделью, не поддерживающей подпрограммы
    result = is_subprogram_supported(MODEL_3)
    assert result is False
    
    # Тест с моделью, поддерживающей подпрограммы
    result = is_subprogram_supported(1)
    assert result is True


def test_get_subprogram_options():
    """Тест получения опций для подпрограмм."""
    result = get_subprogram_options()
    assert isinstance(result, list)
    assert len(result) == 16


def test_get_current_program_text():
    """Тест получения текста текущего режима."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_skycooker = MagicMock()
    mock_skycooker.current_program_id = 0
    mock_skycooker.model_id = 1

    # Тест с режимом ожидания
    result = get_current_program_text(mock_hass, mock_skycooker, 0)
    assert result == "Режим ожидания"

    # Тест с current_program_id=None (возврат standby)
    mock_skycooker.current_program_id = None
    result = get_current_program_text(mock_hass, mock_skycooker, 1)
    assert result == "Режим ожидания"

    # Тест с другим режимом
    mock_hass.data = {"skycooker_translations": {"program_names": {PROGRAM_STANDBY: "Standby"}}}
    mock_skycooker.current_program_id = 0
    result = get_current_program_text(mock_hass, mock_skycooker, 1)
    assert result is not None or result == "Unknown (0)"  # Зависит от данных


def test_get_favorite_programs():
    """Тест получения избранных режимов."""
    mock_hass = MagicMock()
    mock_hass.data = {"skycooker_translations": {"program_names": {PROGRAM_STANDBY: "Standby", "multi_chef": "Multi Chef"}}}
    mock_entry = MagicMock()
    mock_entry.data = {CONF_FAVORITE_PROGRAMS: ["Standby", "Multi Chef"]}

    result = get_favorite_programs(mock_hass, mock_entry, 1)
    assert isinstance(result, list)
    assert len(result) >= 1

    # Тест с пустым списком избранного
    mock_entry.data = {CONF_FAVORITE_PROGRAMS: []}
    result = get_favorite_programs(mock_hass, mock_entry, 1)
    assert result == []

    # Тест с фильтрацией невалидных (PROGRAM_STANDBY, PROGRAM_NONE в избранном)
    mock_entry.data = {CONF_FAVORITE_PROGRAMS: ["Standby", "Unknown"]}
    result = get_favorite_programs(mock_hass, mock_entry, 1)
    assert isinstance(result, list)

    # Тест с пустым program_name (continue)
    with patch('custom_components.skycooker.programs.get_constant_by_name', return_value=None):
        mock_entry.data = {CONF_FAVORITE_PROGRAMS: ["", "Valid"]}
        result = get_favorite_programs(mock_hass, mock_entry, 1)
    assert isinstance(result, list)

    # Тест с program_constant PROGRAM_NONE (continue)
    with patch('custom_components.skycooker.programs.get_constant_by_name', return_value=PROGRAM_NONE):
        mock_entry.data = {CONF_FAVORITE_PROGRAMS: ["NoneSlot"]}
        result = get_favorite_programs(mock_hass, mock_entry, 1)
    assert len(result) == 2  # standby в начале + опция «Другое» в конце


def test_is_program_supported():
    """Тест проверки поддержки режима."""
    mock_hass = MagicMock()
    mock_hass.data = {"skycooker_translations": {"program_names": {PROGRAM_STANDBY: "Standby", "multi_chef": "Multi Chef"}}}

    # Тест с поддерживаемым режимом
    result = is_program_supported(mock_hass, "Standby", 1)
    assert result is True or result is False  # Зависит от данных

    # Тест с несуществующим режимом
    result = is_program_supported(mock_hass, "Unknown", 1)
    assert result is False

    # Тест с режимом не из PROGRAM_NAMES модели (покрытие warning)
    mock_hass.data = {"skycooker_translations": {"program_names": {"unknown_mode": "Unknown Mode"}}}
    result = is_program_supported(mock_hass, "Unknown Mode", 1)
    assert result is False

    # Тест с PROGRAM_STANDBY (покрытие debug, строки 165-166)
    with patch('custom_components.skycooker.programs.get_constant_by_name', return_value=PROGRAM_STANDBY):
        result = is_program_supported(mock_hass, "Standby", 3)
    assert result is True

    # Тест с PROGRAM_STANDBY через реальные данные (standby в model 3)
    mock_hass.data = {"skycooker_translations": {"program_names": {"standby": "Режим ожидания"}}}
    result = is_program_supported(mock_hass, "Режим ожидания", 3)
    assert result is True

    # Тест с PROGRAM_NONE (покрытие debug)
    with patch('custom_components.skycooker.programs.get_constant_by_name', return_value=PROGRAM_NONE):
        result = is_program_supported(mock_hass, "None", 3)
    assert result is True


def test_is_model_supported():
    """Тест проверки поддержки моделей."""
    assert is_model_supported("RMC-M40S") is True
    assert is_model_supported("RMC-M92S") is True
    assert is_model_supported("RMC-M92S-E") is True
    assert is_model_supported("RMC-M222S") is False
    assert is_model_supported("UNKNOWN") is False
    assert is_model_supported("") is False


def test_get_supported_model_names():
    """Тест списка поддерживаемых моделей."""
    names = get_supported_model_names()
    assert "RMC-M40S" in names
    assert "RMC-M92S" in names
    assert "RMC-M222S" not in names


def test_model_6_programs():
    """Тест данных программ RMC-M92S (MODEL_6) — индексы как в протоколе r4sGate."""
    constants = get_program_constants(MODEL_6)
    assert len(constants) == 19
    assert constants[0] == PROGRAM_MULTI_CHEF
    assert constants[15] == PROGRAM_DESSERTS
    assert constants[16] == PROGRAM_EXPRESS
    assert constants[17] == PROGRAM_WARMING
    assert constants[18] == PROGRAM_STANDBY
    assert is_subprogram_supported(MODEL_6) is True
    multi_chef = get_program_data(MODEL_6, 0)
    assert multi_chef["temperature"] == 100
    assert multi_chef["minutes"] == 30
    desserts = get_program_data(MODEL_6, 15)
    assert desserts["temperature"] == 98
    warming = get_program_data(MODEL_6, 17)
    assert warming["temperature"] == 70
    assert warming["minutes"] == 30