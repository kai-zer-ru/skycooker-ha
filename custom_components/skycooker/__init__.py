"""Support for SkyCooker."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ATTR_SW_VERSION,
                                 CONF_FRIENDLY_NAME, CONF_MAC,
                                 Platform)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo


DOMAIN = "skycoker"
FRIENDLY_NAME = "SkyCooker"
MANUFACTORER = "Redmond"
SUGGESTED_AREA = "kitchen"

CONF_PERSISTENT_CONNECTION = "persistent_connection"

DEFAULT_SCAN_INTERVAL = 5
DEFAULT_PERSISTENT_CONNECTION = True

DATA_CONNECTION = "connection"
DATA_CANCEL = "cancel"
DATA_WORKING = "working"
DATA_DEVICE_INFO = "device_info"

DISPATCHER_UPDATE = "update"

ROOM_TEMP = 25
BOIL_TEMP = 100

BLE_SCAN_TIME = 3

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.WATER_HEATER,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SkyCooker integration from a config entry."""
    entry.async_on_unload(entry.add_update_listener(entry_update_listener))

    if DOMAIN not in hass.data: hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data: hass.data[DOMAIN][entry.entry_id] = {}


    hass.data[DOMAIN][DATA_WORKING] = True
    hass.data[DOMAIN][DATA_DEVICE_INFO] = lambda: device_info(entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

def device_info(entry):
    return DeviceInfo(
        name=(FRIENDLY_NAME + " " + entry.data.get(CONF_FRIENDLY_NAME, "")).strip(),
        manufacturer=MANUFACTORER,
        model=entry.data.get(CONF_FRIENDLY_NAME, None),
        sw_version=entry.data.get(ATTR_SW_VERSION, None),
        identifiers={
            (DOMAIN, entry.data[CONF_MAC])
        },
        connections={
            ("mac", entry.data[CONF_MAC])
        }
    )

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading")
    hass.data[DOMAIN][DATA_WORKING] = False
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_unload(entry, component)
        )
    hass.data[DOMAIN][DATA_CANCEL]()
    hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION] = None
    _LOGGER.debug("Entry unloaded")
    return True

async def entry_update_listener(hass, entry):
    """Handle options update."""
    _LOGGER.debug("Options updated")
