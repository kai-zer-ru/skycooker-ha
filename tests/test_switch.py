# Тесты для модуля switch.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.skycooker.switch import SkyCookerSwitch, async_setup_entry
from custom_components.skycooker.const import (
    SWITCH_TYPE_AUTO_WARM,
    DOMAIN,
    DATA_CONNECTION,
)


def test_switch_initialization():
    """Тест инициализации переключателя."""
    switch = SkyCookerSwitch(None, None, SWITCH_TYPE_AUTO_WARM)
    assert switch is not None


def test_switch_state():
    """Тест состояния переключателя."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.auto_warm_enabled = False
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    switch = SkyCookerSwitch(mock_hass, mock_entry, SWITCH_TYPE_AUTO_WARM)
    assert switch.is_on is False


def test_switch_unique_id():
    """Тест уникального идентификатора."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    switch = SkyCookerSwitch(mock_hass, mock_entry, SWITCH_TYPE_AUTO_WARM)
    assert switch.unique_id == f"test_entry_{SWITCH_TYPE_AUTO_WARM}"


def test_switch_name():
    """Тест имени переключателя."""
    mock_hass = MagicMock()
    mock_hass.config.language = "ru"
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"friendly_name": "RMC-M40S"}
    switch = SkyCookerSwitch(mock_hass, mock_entry, SWITCH_TYPE_AUTO_WARM)
    assert "Автоподогрев" in switch.name or "Auto warm" in switch.name


def test_switch_icon():
    """Тест иконки переключателя."""
    switch = SkyCookerSwitch(None, None, SWITCH_TYPE_AUTO_WARM)
    assert switch.icon == "mdi:heat-wave"


def test_switch_name_unknown_type():
    """Тест имени переключателя с неизвестным типом (fallback)."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_entry.data = {"friendly_name": "RMC-M40S"}
    mock_skycooker = MagicMock()
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    switch = SkyCookerSwitch(mock_hass, mock_entry, "unknown_type")
    assert "SkyCooker" in switch.name


def test_switch_is_on_true():
    """Тест состояния включено."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.auto_warm_enabled = True
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    switch = SkyCookerSwitch(mock_hass, mock_entry, SWITCH_TYPE_AUTO_WARM)
    assert switch.is_on is True


def test_switch_is_on_false():
    """Тест состояния выключено."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.auto_warm_enabled = False
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    switch = SkyCookerSwitch(mock_hass, mock_entry, SWITCH_TYPE_AUTO_WARM)
    assert switch.is_on is False


@pytest.mark.asyncio
async def test_switch_turn_on():
    """Тест включения переключателя."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.auto_warm_enabled = False
    async def enable_auto_warm():
        mock_skycooker.auto_warm_enabled = True
    mock_skycooker.enable_auto_warm = AsyncMock(side_effect=enable_auto_warm)
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    switch = SkyCookerSwitch(mock_hass, mock_entry, SWITCH_TYPE_AUTO_WARM)
    switch.update = MagicMock()

    await switch.async_turn_on()

    assert mock_skycooker.auto_warm_enabled is True
    mock_skycooker.enable_auto_warm.assert_called_once()
    switch.update.assert_called_once()


@pytest.mark.asyncio
async def test_switch_turn_off():
    """Тест выключения переключателя."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_skycooker = MagicMock()
    mock_skycooker.auto_warm_enabled = True
    async def disable_auto_warm():
        mock_skycooker.auto_warm_enabled = False
    mock_skycooker.disable_auto_warm = AsyncMock(side_effect=disable_auto_warm)
    mock_hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_skycooker}}}
    switch = SkyCookerSwitch(mock_hass, mock_entry, SWITCH_TYPE_AUTO_WARM)
    switch.update = MagicMock()

    await switch.async_turn_off()

    assert mock_skycooker.auto_warm_enabled is False
    mock_skycooker.disable_auto_warm.assert_called_once()
    switch.update.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry():
    """Тест настройки переключателей."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_hass.data = {DOMAIN: {mock_entry.entry_id: {DATA_CONNECTION: MagicMock()}}}
    mock_async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_entry, mock_async_add_entities)

    assert mock_async_add_entities.called
    entities = mock_async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], SkyCookerSwitch)
