"""SkyCoocker button entities."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import *

_LOGGER = logging.getLogger(__name__)


BUTTON_TYPE_START = "start"
BUTTON_TYPE_STOP = "stop"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCoocker button entities."""
    async_add_entities([
        SkyCoockerButton(hass, entry, BUTTON_TYPE_START),
        SkyCoockerButton(hass, entry, BUTTON_TYPE_STOP),
    ])


class SkyCoockerButton(ButtonEntity):
    """Representation of a SkyCoocker button entity."""

    def __init__(self, hass, entry, button_type):
        """Initialize the button entity."""
        self.hass = hass
        self.entry = entry
        self.button_type = button_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the button entity."""
        self.schedule_update_ha_state()

    @property
    def multicooker(self):
        """Get the multicooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.button_type}"

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
        """Return the name of the button entity."""
        base_name = (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        if self.button_type == BUTTON_TYPE_START:
            return f"{base_name} запуск"
        elif self.button_type == BUTTON_TYPE_STOP:
            return f"{base_name} стоп"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.button_type == BUTTON_TYPE_START:
            return "mdi:play"
        elif self.button_type == BUTTON_TYPE_STOP:
            return "mdi:stop"
        return None

    @property
    def available(self):
        """Return if button entity is available."""
        return self.multicooker.available

    async def async_press(self) -> None:
        """Press the button."""
        if self.button_type == BUTTON_TYPE_START:
            await self.multicooker.start()
        elif self.button_type == BUTTON_TYPE_STOP:
            await self.multicooker.stop()
        
        self.update()