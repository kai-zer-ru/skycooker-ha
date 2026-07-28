# Тесты для модуля button.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.skycooker.button import SkyCookerButton, async_setup_entry
from custom_components.skycooker.const import BUTTON_TYPE_START, BUTTON_TYPE_STOP, BUTTON_TYPE_START_DELAYED, DOMAIN, DATA_CONNECTION


def test_button_initialization():
    """Тест инициализации кнопки."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    # Тест инициализации кнопки START
    start_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
    assert start_button is not None
    assert start_button.button_type == BUTTON_TYPE_START
    assert start_button.unique_id == f"{mock_entry.entry_id}_{BUTTON_TYPE_START}"
    
    # Тест инициализации кнопки STOP
    stop_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_STOP)
    assert stop_button is not None
    assert stop_button.button_type == BUTTON_TYPE_STOP
    assert stop_button.unique_id == f"{mock_entry.entry_id}_{BUTTON_TYPE_STOP}"
    
    # Тест инициализации кнопки START_DELAYED
    delayed_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START_DELAYED)
    assert delayed_button is not None
    assert delayed_button.button_type == BUTTON_TYPE_START_DELAYED
    assert delayed_button.unique_id == f"{mock_entry.entry_id}_{BUTTON_TYPE_START_DELAYED}"


def test_button_name():
    """Тест получения имени кнопки."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    # Тест имени кнопки START
    start_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
    assert start_button.name is not None
    
    # Тест имени кнопки STOP
    stop_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_STOP)
    assert stop_button.name is not None
    
    # Тест имени кнопки START_DELAYED
    delayed_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START_DELAYED)
    assert delayed_button.name is not None


def test_button_icon():
    """Тест получения иконки кнопки."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    
    # Тест иконки кнопки START
    start_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
    assert start_button.icon == "mdi:play"
    
    # Тест иконки кнопки STOP
    stop_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_STOP)
    assert stop_button.icon == "mdi:stop"
    
    # Тест иконки кнопки START_DELAYED
    delayed_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START_DELAYED)
    assert delayed_button.icon == "mdi:timer-play"


@pytest.mark.asyncio
async def test_button_press_start(mocker):
    """Тест нажатия кнопки START."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    # Мокаем skycooker объект
    mock_skycooker = AsyncMock()
    mock_skycooker.start = AsyncMock()
    mock_skycooker.update = AsyncMock()
    
    # Настраиваем mock для hass.data
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    start_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
    
    # Тест нажатия кнопки
    await start_button.async_press()
    
    # Проверяем, что метод start был вызван
    mock_skycooker.start.assert_called_once()
    mock_skycooker.update.assert_called_once()


@pytest.mark.asyncio
async def test_button_press_stop(mocker):
    """Тест нажатия кнопки STOP."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    # Мокаем skycooker объект
    mock_skycooker = AsyncMock()
    mock_skycooker.stop_cooking = AsyncMock()
    mock_skycooker.update = AsyncMock()
    
    # Настраиваем mock для hass.data
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    stop_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_STOP)
    
    # Тест нажатия кнопки
    await stop_button.async_press()
    
    # Проверяем, что метод stop_cooking был вызван
    mock_skycooker.stop_cooking.assert_called_once()
    mock_skycooker.update.assert_called_once()


@pytest.mark.asyncio
async def test_button_press_start_delayed(mocker):
    """Тест нажатия кнопки START_DELAYED."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    # Мокаем skycooker объект
    mock_skycooker = AsyncMock()
    mock_skycooker.start_delayed = AsyncMock()
    mock_skycooker.update = AsyncMock()
    
    # Настраиваем mock для hass.data
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    delayed_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START_DELAYED)
    
    # Тест нажатия кнопки
    await delayed_button.async_press()
    
    # Проверяем, что метод start_delayed был вызван
    mock_skycooker.start_delayed.assert_called_once()
    mock_skycooker.update.assert_called_once()


@pytest.mark.asyncio
async def test_button_press_error(mocker):
    """Тест нажатия кнопки с ошибкой."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    
    # Мокаем skycooker объект с ошибкой
    mock_skycooker = AsyncMock()
    mock_skycooker.start = AsyncMock(side_effect=Exception("Test error"))
    
    # Настраиваем mock для hass.data
    mock_hass.data = {
        DOMAIN: {
            "test_entry": {
                DATA_CONNECTION: mock_skycooker
            }
        }
    }
    
    start_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)
    
    # Тест нажатия кнопки с ошибкой
    with pytest.raises(Exception):
        await start_button.async_press()


def test_button_name_unknown_type():
    """Тест имени кнопки с неизвестным типом (fallback)."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"friendly_name": "RMC-M40S"}
    mock_skycooker = MagicMock()
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    button = SkyCookerButton(mock_hass, mock_entry, "unknown_type")
    assert "SkyCooker" in button.name


@pytest.mark.asyncio
async def test_button_press_skycooker_error():
    """Тест нажатия кнопки с SkyCookerError (не пробрасывает исключение)."""
    from custom_components.skycooker.skycooker import SkyCookerError

    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = AsyncMock()
    mock_skycooker.start = AsyncMock(side_effect=SkyCookerError("Device error"))
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}

    start_button = SkyCookerButton(mock_hass, mock_entry, BUTTON_TYPE_START)

    await start_button.async_press()
    mock_skycooker.start.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry(mocker):
    """Тест настройки сущностей кнопок."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_async_add_entities = MagicMock()
    
    # Мокаем функцию async_add_entities
    await async_setup_entry(mock_hass, mock_entry, mock_async_add_entities)
    
    # Проверяем, что были добавлены 3 сущности кнопок
    assert mock_async_add_entities.called
    args = mock_async_add_entities.call_args[0][0]
    assert len(args) == 3
    assert all(isinstance(btn, SkyCookerButton) for btn in args)
    assert {btn.button_type for btn in args} == {BUTTON_TYPE_START, BUTTON_TYPE_STOP, BUTTON_TYPE_START_DELAYED}