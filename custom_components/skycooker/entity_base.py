"""Базовый класс для сущностей SkyCooker."""

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DISPATCHER_UPDATE, DOMAIN, DATA_CONNECTION, DATA_DEVICE_INFO


class SkyCookerEntity(Entity):
    """Базовый класс для сущностей SkyCooker."""

    def __init__(self, hass, entry):
        """Инициализация сущности."""
        self.hass = hass
        self.entry = entry

    async def async_added_to_hass(self):
            """Когда сущность добавлена в hass."""
            self.update()
            self.async_on_remove(
                async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update)
            )

    def update(self):
        """Обновление сущности."""
        self.schedule_update_ha_state()

    @property
    def skycooker(self):
        """Получение соединения skycooker."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def device_info(self):
        """Возвращает информацию об устройстве."""
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        """Опрос не требуется."""
        return False

    @property
    def assumed_state(self):
        """Возвращает true, если невозможно получить реальное состояние сущности."""
        return False

    @property
    def available(self):
        """Возвращает доступность сущности."""
        return self.skycooker.available