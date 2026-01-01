"""SkyCooker Select Entities."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.dispatcher import (async_dispatcher_connect)

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the SkyCooker select entities entry."""
    cooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    
    # Check if this is a multicooker (RMC-M40S or similar)
    if cooker.model_code in [SkyCooker.MODELS_3, SkyCooker.MODELS_4, SkyCooker.MODELS_5, SkyCooker.MODELS_6, SkyCooker.MODELS_7]:
        entities = [
            SkyCookerModeSelect(hass, entry),
        ]
        async_add_entities(entities)


class SkyCookerModeSelect(SelectEntity):
    """Representation of a SkyCooker mode selector."""

    def __init__(self, hass, entry):
        """Initialize the mode selector."""
        self.hass = hass
        self.entry = entry
        self._attr_options = list(SkyCooker.MODE_NAMES.values())

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
        return self.entry.entry_id + "_mode_select"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get("name", "") + " Mode").strip()

    @property
    def icon(self):
        return "mdi:stove"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    @property
    def current_option(self):
        """Return the current selected mode."""
        status = self.cooker._status
        if status:
            return SkyCooker.MODE_NAMES.get(status.mode, "Standby")
        return "Standby"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Find the mode code for the selected option
        mode_code = None
        for code, name in SkyCooker.MODE_NAMES.items():
            if name == option:
                mode_code = code
                break
        
        if mode_code is not None:
            await self.cooker.set_target_program(mode_code)
            self.async_write_ha_state()