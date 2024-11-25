"""SkyCooker."""
import logging

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.const import (CONF_FRIENDLY_NAME, PERCENTAGE)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory

from .const import *

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPE_SUCCESS_RATE = "success_rate"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker entry."""
    async_add_entities([
        SkySensor(hass, entry, SENSOR_TYPE_SUCCESS_RATE),
    ])

class SkySensor(SensorEntity):
    """Representation of a SkyCooker sensor device."""

    def __init__(self, hass, entry, sensor_type):
        """Initialize the sensor device."""
        self.hass = hass
        self.entry = entry
        self.sensor_type = sensor_type

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_{self.sensor_type}"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def assumed_state(self):
        return False

    @property
    def last_reset(self):
        return None

    @property
    def name(self):
        """Name of the entity."""
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + " success rate"

    @property
    def icon(self):
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return "mdi:bluetooth-connect"
        return None

    @property
    def available(self):
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return True # Always readable

    @property
    def entity_category(self):
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def device_class(self):
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return SensorDeviceClass.HUMIDITY
        return None # Unusual class

    @property
    def state_class(self):
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self):
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return PERCENTAGE
        return None

    @property
    def native_value(self):
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return self.cooker.success_rate
