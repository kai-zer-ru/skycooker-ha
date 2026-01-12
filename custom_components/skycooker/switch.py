"""Переключатели SkyCooker."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_FRIENDLY_NAME

from .const import *
from .entity_base import SkyCookerEntity
from .utils import get_base_name, get_localized_string, get_entity_name




async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка переключателей SkyCooker."""
    async_add_entities([
        SkyCookerSwitch(hass, entry, SWITCH_TYPE_AUTO_WARM),
    ])


class SkyCookerSwitch(SkyCookerEntity, SwitchEntity):
    """Представление переключателя SkyCooker."""

    def __init__(self, hass, entry, switch_type):
        """Инициализация переключателя."""
        super().__init__(hass, entry)
        self.switch_type = switch_type

    @property
    def unique_id(self):
        """Возвращает уникальный идентификатор."""
        return f"{self.entry.entry_id}_{self.switch_type}"

    @property
    def name(self):
        """Возвращает имя переключателя."""
        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            return get_entity_name(self.hass, self.entry, self.switch_type, 'Auto warm', 'Автоподогрев')
        
        return get_base_name(self.entry)

    @property
    def icon(self):
        """Возвращает иконку."""
        return "mdi:heat-wave" if self.switch_type == SWITCH_TYPE_AUTO_WARM else None

    @property
    def is_on(self):
        """Возвращает true, если переключатель включен."""
        return self.switch_type == SWITCH_TYPE_AUTO_WARM and getattr(self.skycooker, '_auto_warm_enabled', False)

    async def async_turn_on(self, **kwargs):
        """Включение переключателя."""
        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            self.skycooker._auto_warm_enabled = True
            self.update()

    async def async_turn_off(self, **kwargs):
        """Выключение переключателя."""
        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            self.skycooker._auto_warm_enabled = False
            self.update()