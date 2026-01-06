"""SkyCoocker switches."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import *

_LOGGER = logging.getLogger(__name__)


SWITCH_TYPE_POWER = "power"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCoocker switches."""
    async_add_entities([
        SkyCoockerSwitch(hass, entry, SWITCH_TYPE_POWER),
    ])


class SkyCoockerSwitch(SwitchEntity):
    """Representation of a SkyCoocker switch."""

    def __init__(self, hass, entry, switch_type):
        """Initialize the switch."""
        self.hass = hass
        self.entry = entry
        self.switch_type = switch_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the switch."""
        self.schedule_update_ha_state()

    @property
    def multicooker(self):
        """Get the multicooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.switch_type}"

    @property
    def device_info(self):
        """Return device info."""
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def assumed_state(self):
        """Return true if unable to access real state of the entity."""
        return False

    @property
    def name(self):
        """Return the name of the switch."""
        base_name = (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        if self.switch_type == SWITCH_TYPE_POWER:
            return f"{base_name} питание"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.switch_type == SWITCH_TYPE_POWER:
            return "mdi:power"
        return None

    @property
    def available(self):
        """Return if switch is available."""
        return self.multicooker.available

    @property
    def is_on(self):
        """Return true if switch is on."""
        if self.switch_type == SWITCH_TYPE_POWER:
            status_code = self.multicooker.status_code
            return status_code not in [STATUS_OFF, STATUS_FULL_OFF]
        return False

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if self.switch_type == SWITCH_TYPE_POWER:
            await self.multicooker.start()
            self.update()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if self.switch_type == SWITCH_TYPE_POWER:
            await self.multicooker.stop()
            self.update()