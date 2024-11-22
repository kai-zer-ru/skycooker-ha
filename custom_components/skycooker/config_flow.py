"""Config flow for SkyCooker integration."""

import logging
import secrets
import traceback

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import (CONF_FRIENDLY_NAME, CONF_MAC,
                                 CONF_PASSWORD, CONF_SCAN_INTERVAL, Platform)
from homeassistant.core import callback


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

MODELS_0 = 0
MODELS_1 = 1
MODELS_2 = 2
MODELS_3 = 3
MODELS_4 = 4
MODELS_5 = 5
MODELS_6 = 6
MODELS_7 = 7

MODEL_TYPE = { # Source: https://github.com/KomX/ESPHome-Ready4Sky/blob/main/components/skycooker/__init__.py
    "RMC-M40S": MODELS_3,
    "RMC-M42S": MODELS_3,
    "RMC-M92S": MODELS_6, "RMC-M92S-A": MODELS_6, "RMC-M92S-C": MODELS_6, "RMC-M92S-E": MODELS_6,
    "RMC-M222S": MODELS_7, "RMC-M222S-A": MODELS_7,
    "RMC-M223S": MODELS_7,"RMC-M223S-E": MODELS_7,
    "RMC-M224S": MODELS_7,"RFS-KMC001": MODELS_7,
    "RMC-M225S": MODELS_7,"RMC-M225S-E": MODELS_7,
    "RMC-M226S": MODELS_7,"RMC-M226S-E": MODELS_7,"JK-MC501": MODELS_7,"NK-MC10": MODELS_7,
    "RMC-M227S": MODELS_7,
    "RMC-M800S": MODELS_0,
    "RMC-M903S": MODELS_5, "RFS-KMC005": MODELS_5,
    "RMC-961S": MODELS_4,
    "RMC-CBD100S": MODELS_1,
    "RMC-CBF390S": MODELS_2,
}

class SkyCookerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def get_model_code(model):
        if model in MODEL_TYPE:
            return MODEL_TYPE[model]
        if model.endswith("-E"):
            return MODEL_TYPE.get(model[:-2], None)
        return None
    @staticmethod
    @callback
    def async_get_options_flow(entry):
        """Get options flow for this handler."""
        return SkyCookerConfigFlow(entry=entry)

    def __init__(self, entry = None):
        """Initialize a new SkyCookerConfigFlow."""
        self.entry = entry
        self.config = {} if not entry else dict(entry.data.items())

    async def init_mac(self, mac):
        mac = mac.upper()
        mac = mac.replace(':','').replace('-','').replace(' ','')
        mac = ':'.join([mac[p*2:(p*2)+2] for p in range(6)])
        id = f"{DOMAIN}-{mac}"
        if id in self._async_current_ids():
            return False
        await self.async_set_unique_id(id)
        self.config[CONF_MAC] = mac
        # It's time to create random password
        self.config[CONF_PASSWORD] = list(secrets.token_bytes(8))
        return True

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        return await self.async_step_scan()
   
    async def async_step_scan(self, user_input=None):
        """Handle the scan step."""
        errors = {}
        if user_input is not None:
            spl = user_input[CONF_MAC].split(' ', maxsplit=1)
            mac = spl[0]
            name = spl[1][1:-1] if len(spl) >= 2 else None
            if not self.get_model_code(name):
                # Model is not supported
                return self.async_abort(reason='unknown_model')
            if not await self.init_mac(mac):
                # This cooker already configured
                return self.async_abort(reason='already_configured')
            if name: self.config[CONF_FRIENDLY_NAME] = name
            # Continue to connect step
            return await self.async_step_connect()

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                for device in scanner.discovered_devices:
                    _LOGGER.debug(f"Device found: {device.address} - {device.name}")
            except:
                _LOGGER.error("Bluetooth integration not working")
                return self.async_abort(reason='no_bluetooth')
            devices_filtered = [device for device in scanner.discovered_devices if device.name and (device.name.startswith("RK-") or device.name.startswith("RFS-"))]
            if len(devices_filtered) == 0:
                return self.async_abort(reason='cooker_not_found')
            mac_list = [f"{r.address} ({r.name})" for r in devices_filtered]
            schema = vol.Schema(
            {
                vol.Required(CONF_MAC): vol.In(mac_list)
            })
        except Exception:
            _LOGGER.error(traceback.format_exc())
            return self.async_abort(reason='unknown')
        return self.async_show_form(
            step_id="scan",
            errors=errors,
            data_schema=schema
        )

    async def async_step_connect(self, user_input=None):
        """Handle the connect step."""
        errors = {}
        if user_input is not None:
            cooker = None
            # tries = 3
            # while tries > 0 and not cooker._last_connect_ok:
            #     await cooker.update()
            #     tries = tries - 1
            #
            connect_ok = True
            auth_ok = True
            # cooker.stop()
        
            if not connect_ok:
                errors["base"] = "cant_connect"
            elif not auth_ok:
                errors["base"] = "cant_auth"
            else:
                return await self.async_step_init()

        return self.async_show_form(
            step_id="connect",
            errors=errors,
            data_schema=vol.Schema({})
        )  

    async def async_step_init(self, user_input=None):
        """Handle the options step."""
        errors = {}
        if user_input is not None:
            self.config[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.config[CONF_PERSISTENT_CONNECTION] = user_input[CONF_PERSISTENT_CONNECTION]
            fname = f"{self.config.get(CONF_FRIENDLY_NAME, FRIENDLY_NAME)} ({self.config[CONF_MAC]})"
            # _LOGGER.debug(f"saving config: {self.config}")
            if self.entry:
                self.hass.config_entries.async_update_entry(self.entry, data=self.config)
            _LOGGER.info(f"Config saved")
            return self.async_create_entry(
                title=fname, data=self.config if not self.entry else {}
            )

        schema = vol.Schema(
        {
            vol.Required(CONF_PERSISTENT_CONNECTION, default=self.config.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)): cv.boolean,
            vol.Required(CONF_SCAN_INTERVAL, default=self.config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        })

        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=schema
        )
