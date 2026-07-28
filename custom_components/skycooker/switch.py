"""Переключатели SkyCooker."""
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchEntity

from .const import *
from .entity_base import SkyCookerEntity
from .utils import get_base_name, get_entity_name, build_entity_id


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
        # Стабильный английский entity_id, независимо от языка интерфейса
        self.entity_id = build_entity_id(SWITCH_DOMAIN, hass, entry, switch_type)

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
        if not self.skycooker:
            return False
        return self.switch_type == SWITCH_TYPE_AUTO_WARM and getattr(self.skycooker, 'auto_warm_enabled', False)

    async def async_turn_on(self, **kwargs):
        """Включение переключателя."""
        if not self.skycooker or self.switch_type != SWITCH_TYPE_AUTO_WARM:
            return
        await self.skycooker.enable_auto_warm()
        self.update()

    async def async_turn_off(self, **kwargs):
        """Выключение переключателя."""
        if not self.skycooker or self.switch_type != SWITCH_TYPE_AUTO_WARM:
            return
        await self.skycooker.disable_auto_warm()
        self.update()
