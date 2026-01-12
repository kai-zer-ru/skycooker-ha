"""SkyCooker button entities."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_FRIENDLY_NAME

from .const import *
from .entity_base import SkyCookerEntity
from .skycooker import SkyCookerError
from .utils import get_base_name, get_localized_string, get_entity_name

_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка сущностей кнопок SkyCooker."""
    async_add_entities([
        SkyCookerButton(hass, entry, BUTTON_TYPE_START),
        SkyCookerButton(hass, entry, BUTTON_TYPE_STOP),
        SkyCookerButton(hass, entry, BUTTON_TYPE_START_DELAYED),
    ])


class SkyCookerButton(SkyCookerEntity, ButtonEntity):
    """Представление сущности кнопки SkyCooker."""

    def __init__(self, hass, entry, button_type):
        """Инициализация сущности кнопки."""
        super().__init__(hass, entry)
        self.button_type = button_type

    @property
    def unique_id(self):
        """Возвращает уникальный идентификатор."""
        return f"{self.entry.entry_id}_{self.button_type}"

    @property
    def name(self):
        """Возвращает имя сущности кнопки."""
        if self.button_type == BUTTON_TYPE_START:
            return get_entity_name(self.hass, self.entry, self.button_type, 'Start', 'Старт')
        elif self.button_type == BUTTON_TYPE_STOP:
            return get_entity_name(self.hass, self.entry, self.button_type, 'Stop', 'Стоп')
        elif self.button_type == BUTTON_TYPE_START_DELAYED:
            return get_entity_name(self.hass, self.entry, self.button_type, 'Delayed start', 'Отложенный старт')
        
        return get_base_name(self.entry)

    @property
    def icon(self):
        """Возвращает иконку."""
        icons = {
            BUTTON_TYPE_START: "mdi:play",
            BUTTON_TYPE_STOP: "mdi:stop",
            BUTTON_TYPE_START_DELAYED: "mdi:timer-play",
        }
        return icons.get(self.button_type)

    async def async_press(self) -> None:
        """Нажатие кнопки."""
        actions = {
            BUTTON_TYPE_START: self.skycooker.start,
            BUTTON_TYPE_STOP: self.skycooker.stop_cooking,
            BUTTON_TYPE_START_DELAYED: self.skycooker.start_delayed,
        }
        
        try:
            if self.button_type in actions:
                await actions[self.button_type]()
        except SkyCookerError as e:
            _LOGGER.error(f"❌ Ошибка при нажатии кнопки: {str(e)}")
        except Exception as e:
            _LOGGER.error(f"❌ Неожиданная ошибка при нажатии кнопки: {str(e)}")
        
        # Планирование обновления для всех сущностей, чтобы отразить изменения немедленно
        self.async_schedule_update_ha_state(True)
        
        # Также обновление соединения skycooker для отражения изменений
        self.update()