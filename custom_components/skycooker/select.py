"""SkyCoocker select entities."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import *

_LOGGER = logging.getLogger(__name__)


SELECT_TYPE_MODE = "mode"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCoocker select entities."""
    async_add_entities([
        SkyCoockerSelect(hass, entry, SELECT_TYPE_MODE),
    ])


class SkyCoockerSelect(SelectEntity):
    """Representation of a SkyCoocker select entity."""

    def __init__(self, hass, entry, select_type):
        """Initialize the select entity."""
        self.hass = hass
        self.entry = entry
        self.select_type = select_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the select entity."""
        self.schedule_update_ha_state()

    @property
    def multicooker(self):
        """Get the multicooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.select_type}"

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
        """Return the name of the select entity."""
        base_name = (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        if self.select_type == SELECT_TYPE_MODE:
            return f"{base_name} режим"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.select_type == SELECT_TYPE_MODE:
            return "mdi:chef-hat"
        return None

    @property
    def available(self):
        """Return if select entity is available."""
        return self.multicooker.available

    @property
    def current_option(self):
        """Return the current selected option."""
        if self.select_type == SELECT_TYPE_MODE:
            mode_id = self.multicooker.current_mode
            if mode_id is not None:
                return MODES.get(mode_id, f"Неизвестно ({mode_id})")
        return None

    @property
    def options(self):
        """Return the available options."""
        if self.select_type == SELECT_TYPE_MODE:
            return list(MODES.values())
        return []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.select_type == SELECT_TYPE_MODE:
            # Find the mode ID by name
            mode_id = None
            for key, value in MODES.items():
                if value == option:
                    mode_id = key
                    break
            
            if mode_id is not None:
                await self.multicooker.set_mode(mode_id)
                self.update()