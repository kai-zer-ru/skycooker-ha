"""Бинарные сенсоры SkyCooker."""

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorEntity,
)

from .const import (
    DOMAIN,
    DATA_CONNECTION,
    BINARY_SENSOR_TYPE_COOKING,
    BINARY_SENSOR_TYPE_AUTO_WARM_ACTIVE,
    BINARY_SENSOR_TYPE_DELAYED_START_ACTIVE,
)
from .entity_base import SkyCookerEntity
from .utils import get_base_name, get_entity_name, build_entity_id


async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка бинарных сенсоров SkyCooker."""
    entities: list[SkyCookerBinarySensor] = [
        SkyCookerBinarySensor(hass, entry, BINARY_SENSOR_TYPE_COOKING),
        SkyCookerBinarySensor(hass, entry, BINARY_SENSOR_TYPE_AUTO_WARM_ACTIVE),
        SkyCookerBinarySensor(hass, entry, BINARY_SENSOR_TYPE_DELAYED_START_ACTIVE),
    ]

    async_add_entities(entities)


class SkyCookerBinarySensor(SkyCookerEntity, BinarySensorEntity):
    """Представление бинарного сенсора SkyCooker."""

    def __init__(self, hass, entry, sensor_type: str) -> None:
        super().__init__(hass, entry)
        self.sensor_type = sensor_type
        # Стабильный английский entity_id, независимо от языка интерфейса
        self.entity_id = build_entity_id(BINARY_SENSOR_DOMAIN, hass, entry, sensor_type)

    @property
    def unique_id(self):
        """Возвращает уникальный идентификатор."""
        return f"{self.entry.entry_id}_{self.sensor_type}"

    @property
    def name(self):
        """Возвращает имя сенсора."""
        if self.sensor_type == BINARY_SENSOR_TYPE_COOKING:
            return get_entity_name(
                self.hass,
                self.entry,
                self.sensor_type,
                "Cooking active",
                "Готовка/разогрев активны",
            )
        if self.sensor_type == BINARY_SENSOR_TYPE_AUTO_WARM_ACTIVE:
            return get_entity_name(
                self.hass,
                self.entry,
                self.sensor_type,
                "Auto warm active",
                "Автоподогрев активен",
            )
        if self.sensor_type == BINARY_SENSOR_TYPE_DELAYED_START_ACTIVE:
            return get_entity_name(
                self.hass,
                self.entry,
                self.sensor_type,
                "Delayed start active",
                "Отложенный старт активен",
            )

        return get_base_name(self.entry)

    @property
    def is_on(self):
        """Возвращает состояние бинарного сенсора."""
        if not self.skycooker:
            return False

        if self.sensor_type == BINARY_SENSOR_TYPE_COOKING:
            return bool(getattr(self.skycooker, "is_cooking", False))
        if self.sensor_type == BINARY_SENSOR_TYPE_AUTO_WARM_ACTIVE:
            return bool(getattr(self.skycooker, "is_auto_warm_active", False))
        if self.sensor_type == BINARY_SENSOR_TYPE_DELAYED_START_ACTIVE:
            return bool(getattr(self.skycooker, "is_delayed_start_active", False))

        return False
