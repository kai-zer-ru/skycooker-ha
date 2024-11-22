"""Support for SkyCooker."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_SW_VERSION, CONF_FRIENDLY_NAME, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SkyCooker integration from a config entry."""
    _LOGGER.info("async_setup_entry")
    entry.async_on_unload(entry.add_update_listener(entry_update_listener))

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data:
        hass.data[DOMAIN][entry.entry_id] = {}

    hass.data[DOMAIN][DATA_WORKING] = True
    hass.data[DOMAIN][DATA_DEVICE_INFO] = lambda: device_info(entry)

    await hass.config_entries.async_forward_entry_setups(entry, [])

    return True


def device_info(entry):
    return DeviceInfo(
        name=(FRIENDLY_NAME + " " + entry.data.get(CONF_FRIENDLY_NAME, "")).strip(),
        manufacturer=MANUFACTORER,
        model=entry.data.get(CONF_FRIENDLY_NAME, None),
        sw_version=entry.data.get(ATTR_SW_VERSION, None),
        identifiers={(DOMAIN, entry.data[CONF_MAC])},
        connections={("mac", entry.data[CONF_MAC])},
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info("Unloading")
    _LOGGER.info("Entry unloaded")
    return True


async def entry_update_listener(hass, entry):
    """Handle options update."""
    _LOGGER.info("Options updated")
