"""SkyCooker."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import (ATTR_SW_VERSION, CONF_FRIENDLY_NAME, CONF_SCAN_INTERVAL)
from homeassistant.helpers.dispatcher import (async_dispatcher_connect)

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the SkyCooker entry."""
    async_add_entities([SkyWaterHeater(hass, entry)])


class SkyWaterHeater(ButtonEntity):
    """Representation of a SkyCooker water_heater device."""

    def __init__(self, hass, entry):
        """Initialize the water_heater device."""
        self.hass = hass
        self.entry = entry

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
        return self.entry.entry_id + "_cooker"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()

    @property
    def icon(self):
        return "mdi:kettle"

    @property
    def device_class(self):
        return None

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
    def available(self):
        return self.cooker.available

    @property
    def entity_category(self):
        return None

    @property
    def extra_state_attributes(self):
        sw_version = self.cooker.sw_version
        if sw_version:
            major, minor = sw_version
            sw_version = f"{major}.{minor}"
            updates = {ATTR_SW_VERSION: sw_version}
            self.hass.config_entries.async_update_entry(
                self.entry, data={**self.entry.data, **updates}
            )
        data = {
            "connected": self.cooker.connected,
            "cook_hours": self.cooker.cook_hours,
            "cook_minutes": self.cooker.cook_minutes,
            "wait_hours": self.cooker.wait_hours,
            "wait_minutes": self.cooker.wait_minutes,
            "current_program": self.cooker.current_program,
            "auth_ok": self.cooker.auth_ok,
            "sw_version": sw_version,
            "success_rate": self.cooker.success_rate,
            "persistent_connection": self.cooker.persistent,
            "poll_interval": self.entry.data.get(CONF_SCAN_INTERVAL, 0),
            "error_code": self.cooker.error_code,
        }
        return data

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        _LOGGER.warning(f"TargetMode: {self.cooker.current_program != None}")
        return self.cooker.current_program != None

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.cooker.set_target_program(SkyCooker.MODE_NAMES[SkyCooker.MODE_BOIL])

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.cooker.set_target_program(None)
