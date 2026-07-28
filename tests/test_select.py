# Тесты для модуля select.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.select import SkyCookerSelect, async_setup_entry
from custom_components.skycooker.const import (
    SELECT_TYPE_PROGRAM,
    SELECT_TYPE_TEMPERATURE,
    SELECT_TYPE_COOKING_TIME_HOURS,
    SELECT_TYPE_COOKING_TIME_MINUTES,
    SELECT_TYPE_DELAYED_START_HOURS,
    SELECT_TYPE_DELAYED_START_MINUTES,
    SELECT_TYPE_SUBPROGRAM,
    SELECT_TYPE_FAVORITES,
    DOMAIN,
    DATA_CONNECTION,
    PROGRAM_NONE,
    DISPATCHER_UPDATE,
)


def test_select_initialization():
    """Тест инициализации сущности выбора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    
    assert select_entity is not None
    assert select_entity.select_type == SELECT_TYPE_PROGRAM


@pytest.mark.asyncio
async def test_async_setup_entry():
    """Тест настройки сущностей выбора."""
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
    assert len(entities) == 8  # 5 базовых + 1 подпрограмма + 1 избранное + 1 температура


@pytest.mark.asyncio
async def test_select_unique_id():
    """Тест уникального идентификатора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    
    assert select_entity.unique_id == "test_entry_" + SELECT_TYPE_PROGRAM


def test_select_name():
    """Тест имени сущности выбора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_entry.title = "Test Device"
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    
    # Мокаем get_entity_name
    with patch('custom_components.skycooker.select.get_entity_name', return_value="Test Program"):
        assert select_entity.name == "Test Program"


def test_select_icon():
    """Тест иконки сущности выбора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    assert select_entity.icon == "mdi:chef-hat"

    select_entity.select_type = SELECT_TYPE_TEMPERATURE
    assert select_entity.icon == "mdi:thermometer"


def test_select_name_all_types():
    """Тест имён для всех типов селектов."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"friendly_name": "RMC-M40S"}
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    types_and_keys = [
        (SELECT_TYPE_PROGRAM, "Программа"),
        (SELECT_TYPE_SUBPROGRAM, "Подпрограмма"),
        (SELECT_TYPE_TEMPERATURE, "Температура"),
        (SELECT_TYPE_COOKING_TIME_HOURS, "часы"),
        (SELECT_TYPE_COOKING_TIME_MINUTES, "минуты"),
        (SELECT_TYPE_DELAYED_START_HOURS, "часы"),
        (SELECT_TYPE_DELAYED_START_MINUTES, "минуты"),
        (SELECT_TYPE_FAVORITES, "Избранное"),
    ]
    for select_type, expected_part in types_and_keys:
        select_entity = SkyCookerSelect(mock_hass, mock_entry, select_type)
        assert expected_part in select_entity.name or "SkyCooker" in select_entity.name


def test_select_current_option():
    """Тест текущего выбранного варианта."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.target_program_name = "Test Program"
    mock_skycooker.target_temperature = 100
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30
    mock_skycooker.target_additional_hours = 2
    mock_skycooker.target_additional_minutes = 15
    mock_skycooker.target_subprogram_id = 1
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)

    assert select_entity.current_option == "Test Program"

    # Тест current_option для температуры None
    select_entity.select_type = SELECT_TYPE_TEMPERATURE
    mock_skycooker.target_temperature = None
    assert select_entity.current_option == "0"

    # Тест current_option для времени
    select_entity.select_type = SELECT_TYPE_COOKING_TIME_HOURS
    mock_skycooker.target_main_hours = None
    assert select_entity.current_option == "0"

    select_entity.select_type = SELECT_TYPE_COOKING_TIME_MINUTES
    mock_skycooker.target_main_minutes = None
    assert select_entity.current_option == "0"

    select_entity.select_type = SELECT_TYPE_DELAYED_START_HOURS
    mock_skycooker.target_additional_hours = 2
    assert select_entity.current_option == "2"

    select_entity.select_type = SELECT_TYPE_DELAYED_START_MINUTES
    mock_skycooker.target_additional_minutes = 15
    assert select_entity.current_option == "15"

    # Тест current_option для подпрограммы
    select_entity.select_type = SELECT_TYPE_SUBPROGRAM
    mock_skycooker.target_subprogram_id = None
    assert select_entity.current_option == "0"

    # Восстанавливаем значения для проверки отображения установленных опций
    mock_skycooker.target_temperature = 100
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30
    mock_skycooker.target_subprogram_id = 1

    select_entity.select_type = SELECT_TYPE_TEMPERATURE
    assert select_entity.current_option == "100"
    
    select_entity.select_type = SELECT_TYPE_COOKING_TIME_HOURS
    assert select_entity.current_option == "1"
    
    select_entity.select_type = SELECT_TYPE_COOKING_TIME_MINUTES
    assert select_entity.current_option == "30"
    
    select_entity.select_type = SELECT_TYPE_DELAYED_START_HOURS
    assert select_entity.current_option == "2"
    
    select_entity.select_type = SELECT_TYPE_DELAYED_START_MINUTES
    assert select_entity.current_option == "15"
    
    select_entity.select_type = SELECT_TYPE_SUBPROGRAM
    assert select_entity.current_option == "1"


def test_select_options():
    """Тест доступных вариантов."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    
    # Мокаем get_program_options
    with patch('custom_components.skycooker.select.get_program_options', return_value=["Program 1", "Program 2"]):
        assert select_entity.options == ["Program 1", "Program 2"]
    
    select_entity.select_type = SELECT_TYPE_TEMPERATURE
    with patch('custom_components.skycooker.select.get_temperature_options', return_value=["50", "100", "150"]):
        assert select_entity.options == ["50", "100", "150"]


@pytest.mark.asyncio
async def test_select_option_program():
    """Тест изменения выбранного варианта для программы."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1
    mock_skycooker.target_program_name = None
    mock_skycooker.target_temperature = None
    mock_skycooker.target_main_hours = None
    mock_skycooker.target_main_minutes = None
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    
    # Мокаем get_program_data
    with patch('custom_components.skycooker.select.get_program_data', return_value={'temperature': 100, 'hours': 1, 'minutes': 30}):
        with patch('custom_components.skycooker.select.get_constant_by_name', return_value="PROGRAM_1"):
            with patch('custom_components.skycooker.select.find_program_id', return_value=0):
                await select_entity.async_select_option("Test Program")
    
    assert mock_skycooker.target_program_name == "Test Program"
    assert mock_skycooker.target_temperature == 100
    assert mock_skycooker.target_main_hours == 1
    assert mock_skycooker.target_main_minutes == 30


@pytest.mark.asyncio
async def test_select_option_temperature():
    """Тест изменения выбранного варианта для температуры."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.target_temperature = None
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_TEMPERATURE)
    
    await select_entity.async_select_option("100")
    
    assert mock_skycooker.target_temperature == 100


@pytest.mark.asyncio
async def test_select_option_time():
    """Тест изменения выбранного варианта для времени."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.target_main_hours = None
    mock_skycooker.target_main_minutes = None
    mock_skycooker.target_additional_hours = None
    mock_skycooker.target_additional_minutes = None
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_COOKING_TIME_HOURS)
    
    await select_entity.async_select_option("2")
    
    assert mock_skycooker.target_main_hours == 2
    
    select_entity.select_type = SELECT_TYPE_COOKING_TIME_MINUTES
    await select_entity.async_select_option("30")
    
    assert mock_skycooker.target_main_minutes == 30
    
    select_entity.select_type = SELECT_TYPE_DELAYED_START_HOURS
    await select_entity.async_select_option("1")
    
    assert mock_skycooker.target_additional_hours == 1
    
    select_entity.select_type = SELECT_TYPE_DELAYED_START_MINUTES
    await select_entity.async_select_option("15")
    
    assert mock_skycooker.target_additional_minutes == 15


@pytest.mark.asyncio
async def test_select_option_subprogram():
    """Тест изменения выбранного варианта для подпрограммы."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.target_subprogram_id = None
    
    # Настраиваем hass.data для возврата mock_skycooker
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_SUBPROGRAM)
    
    await select_entity.async_select_option("1")

    assert mock_skycooker.target_subprogram_id == 1


@pytest.mark.asyncio
async def test_async_added_to_hass_set_default_time_values():
    """Тест установки значений по умолчанию для селектов времени при добавлении в hass."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1
    mock_skycooker.target_main_hours = None
    mock_skycooker.target_main_minutes = None
    mock_skycooker.target_additional_hours = None
    mock_skycooker.target_additional_minutes = None
    mock_skycooker.target_temperature = None

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    for select_type in [
        SELECT_TYPE_COOKING_TIME_HOURS,
        SELECT_TYPE_COOKING_TIME_MINUTES,
        SELECT_TYPE_DELAYED_START_HOURS,
        SELECT_TYPE_DELAYED_START_MINUTES,
        SELECT_TYPE_TEMPERATURE,
    ]:
        select_entity = SkyCookerSelect(mock_hass, mock_entry, select_type)
        with patch.object(select_entity, "update"):
            await select_entity.async_added_to_hass()

    assert mock_skycooker.target_main_hours == 0
    assert mock_skycooker.target_main_minutes == 0
    assert mock_skycooker.target_additional_hours == 0
    assert mock_skycooker.target_additional_minutes == 0
    assert mock_skycooker.target_temperature == 100


@pytest.mark.asyncio
async def test_async_added_to_hass_set_default_mode():
    """Тест установки режима ожидания по умолчанию для селекта программ."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    with patch.object(select_entity, "update"):
        with patch("custom_components.skycooker.select.get_standby_program_name", return_value="Standby"):
            await select_entity.async_added_to_hass()

    assert mock_skycooker.target_program_name == "Standby"


def test_select_current_option_favorites_not_in_list():
    """Тест current_option для избранного: при программе не из избранного показывается «Другое»."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.target_program_name = "Unknown Program"
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_FAVORITES)
    with patch("custom_components.skycooker.select.get_favorite_programs", return_value=["Program A", "Program B", "Other"]):
        with patch("custom_components.skycooker.select.get_favorites_other_label", return_value="Other"):
            assert select_entity.current_option == "Other"


def test_select_current_option_delayed_start_no_attr():
    """Тест current_option для отложенного старта, когда атрибут отсутствует."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    # Объект без target_additional_hours/target_additional_minutes
    mock_skycooker = type("MinimalSkycooker", (), {})()

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_DELAYED_START_HOURS)
    assert select_entity.current_option == "0"

    select_entity.select_type = SELECT_TYPE_DELAYED_START_MINUTES
    assert select_entity.current_option == "0"


def test_select_current_option_unknown_type():
    """Тест current_option для неизвестного типа возвращает None."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    select_entity.select_type = "unknown_type"
    assert select_entity.current_option is None


def test_select_options_unknown_type():
    """Тест options для неизвестного типа возвращает пустой список."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    select_entity.select_type = "unknown_type"
    assert select_entity.options == []


def test_select_options_all_types():
    """Тест options для всех типов селектов."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    with patch("custom_components.skycooker.select.get_program_options", return_value=["P1"]):
        select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
        assert select_entity.options == ["P1"]

    with patch("custom_components.skycooker.select.get_subprogram_options", return_value=["0", "1"]):
        select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_SUBPROGRAM)
        assert select_entity.options == ["0", "1"]

    with patch("custom_components.skycooker.select.get_time_options") as mock_time:
        mock_time.return_value = ["0", "1", "2"]
        select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_COOKING_TIME_HOURS)
        assert select_entity.options == ["0", "1", "2"]
        mock_time.assert_called_with(hours=True)

        select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_DELAYED_START_MINUTES)
        assert select_entity.options == ["0", "1", "2"]
        mock_time.assert_called_with(hours=False)

    with patch("custom_components.skycooker.select.get_favorite_programs", return_value=["Fav1"]):
        select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_FAVORITES)
        assert select_entity.options == ["Fav1"]


@pytest.mark.asyncio
async def test_async_select_option_unknown_type():
    """Тест async_select_option для неизвестного типа — ранний выход."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    select_entity.select_type = "unknown_type"

    with patch.object(select_entity, "async_schedule_update_ha_state") as mock_update:
        result = await select_entity.async_select_option("any")
        assert result is None
        mock_update.assert_not_called()


@pytest.mark.asyncio
async def test_handle_program_selection_empty_string():
    """Тест _handle_program_selection при пустой строке — устанавливается standby."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    with patch("custom_components.skycooker.select.get_standby_program_name", return_value="Standby"):
        await select_entity._handle_program_selection("")

    assert mock_skycooker.target_program_name == "Standby"


@pytest.mark.asyncio
async def test_handle_program_selection_program_none():
    """Тест _handle_program_selection при PROGRAM_NONE — ранний выход."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    with patch("custom_components.skycooker.select.get_constant_by_name", return_value=PROGRAM_NONE):
        result = await select_entity._handle_program_selection("Some Program")

    assert result is None


@pytest.mark.asyncio
async def test_handle_program_selection_find_program_id_none():
    """Тест _handle_program_selection при find_program_id возвращает None."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    with patch("custom_components.skycooker.select.get_constant_by_name", return_value="PROGRAM_1"):
        with patch("custom_components.skycooker.select.find_program_id", return_value=None):
            result = await select_entity._handle_program_selection("Unknown")

    assert result is None


@pytest.mark.asyncio
async def test_handle_program_selection_model_id_none():
    """Тест _handle_program_selection при model_id is None."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = None

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    result = await select_entity._handle_program_selection("Program")

    assert result is None


@pytest.mark.asyncio
async def test_handle_program_selection_favorites():
    """Тест _handle_program_selection для селекта избранного."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_FAVORITES)
    with patch("custom_components.skycooker.select.get_program_data", return_value={"temperature": 80, "hours": 0, "minutes": 45}):
        with patch("custom_components.skycooker.select.get_constant_by_name", return_value="PROGRAM_YOGURT"):
            with patch("custom_components.skycooker.select.find_program_id", return_value=1):
                with patch("custom_components.skycooker.select.async_dispatcher_send"):
                    await select_entity._handle_program_selection("Yogurt")

    assert mock_skycooker.target_program_name == "Yogurt"
    assert mock_skycooker.target_temperature == 80
    assert mock_skycooker.target_main_minutes == 45


@pytest.mark.asyncio
async def test_handle_program_selection_favorites_other_does_not_change_temp_time():
    """При выборе «Другое» в избранном температура и время не меняются."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1
    mock_skycooker.target_program_name = "Плов"
    mock_skycooker.target_temperature = 120
    mock_skycooker.target_main_hours = 1
    mock_skycooker.target_main_minutes = 30

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_FAVORITES)
    with patch("custom_components.skycooker.select.get_favorites_other_label", return_value="Другое"):
        with patch("custom_components.skycooker.select.async_dispatcher_send"):
            await select_entity._handle_program_selection("Другое")

    assert mock_skycooker.target_program_name == "Плов"
    assert mock_skycooker.target_temperature == 120
    assert mock_skycooker.target_main_hours == 1
    assert mock_skycooker.target_main_minutes == 30


def test_select_name_unknown_type():
    """Тест name для неизвестного типа — возвращает get_base_name."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    select_entity.select_type = "unknown_type"

    with patch("custom_components.skycooker.select.get_base_name", return_value="SkyCooker Base"):
        assert select_entity.name == "SkyCooker Base"


@pytest.mark.asyncio
async def test_async_select_option_delayed_start_sets_defaults():
    """Тест что при выборе отложенного старта устанавливаются значения по умолчанию для парного селекта."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.target_additional_hours = None
    mock_skycooker.target_additional_minutes = None

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_DELAYED_START_HOURS)
    await select_entity.async_select_option("1")

    assert mock_skycooker.target_additional_hours == 1
    assert mock_skycooker.target_additional_minutes == 0

    # При выборе минут target_additional_hours тоже устанавливается в 0 если был None
    mock_skycooker.target_additional_hours = None
    mock_skycooker.target_additional_minutes = None
    select_entity.select_type = SELECT_TYPE_DELAYED_START_MINUTES
    await select_entity.async_select_option("15")

    assert mock_skycooker.target_additional_minutes == 15
    assert mock_skycooker.target_additional_hours == 0


@pytest.mark.asyncio
async def test_async_select_option_program_sends_dispatcher():
    """Тест что при выборе программы отправляется событие DISPATCHER_UPDATE."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.model_id = 1

    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    select_entity = SkyCookerSelect(mock_hass, mock_entry, SELECT_TYPE_PROGRAM)
    with patch("custom_components.skycooker.select.get_program_data", return_value={"temperature": 100, "hours": 1, "minutes": 30}):
        with patch("custom_components.skycooker.select.get_constant_by_name", return_value="PROGRAM_1"):
            with patch("custom_components.skycooker.select.find_program_id", return_value=0):
                with patch("custom_components.skycooker.select.async_dispatcher_send") as mock_send:
                    await select_entity.async_select_option("Test Program")

    mock_send.assert_called_with(mock_hass, DISPATCHER_UPDATE)