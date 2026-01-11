"""Config flow for SkyCooker integration."""

import logging
import traceback

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import (CONF_DEVICE, CONF_FRIENDLY_NAME, CONF_MAC,
                                  CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.core import callback

from .const import *
from .skycooker_connection import SkyCookerConnection
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


class SkyCookerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

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
        self.config[CONF_PASSWORD] = list(bytes.fromhex("0000000000000000"))
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
            if not SkyCooker.get_model_code(name):
                return self.async_abort(reason='unknown_model')
            if not await self.init_mac(mac):
                return self.async_abort(reason='already_configured')
            if name: self.config[CONF_FRIENDLY_NAME] = name
            return await self.async_step_connect()

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                for device in scanner.discovered_devices:
                    _LOGGER.debug(f"Device found: {device.address} - {device.name}")
            except:
                _LOGGER.error("Bluetooth integration not working")
                return self.async_abort(reason='no_bluetooth')
            devices_filtered = [device for device in scanner.discovered_devices if device.name and (device.name.startswith("RMC-") or device.name.startswith("RFS-"))]
            if len(devices_filtered) == 0:
                return self.async_abort(reason='skycooker_not_found')
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
            skycooker = SkyCookerConnection(
                mac=self.config[CONF_MAC],
                key=self.config[CONF_PASSWORD],
                persistent=True,
                adapter=self.config.get(CONF_DEVICE, None),
                hass=self.hass,
                model=self.config.get(CONF_FRIENDLY_NAME, None)
            )
            tries = 3
            while tries > 0 and not skycooker.last_connect_ok:
                await skycooker.update()
                tries = tries - 1
              
            connect_ok = skycooker.last_connect_ok
            auth_ok = skycooker.last_auth_ok
            await skycooker.stop()
         
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
            fname = f"{self.config.get(CONF_FRIENDLY_NAME, SKYCOOKER_NAME)} ({self.config[CONF_MAC]})"
            if self.entry:
                self.hass.config_entries.async_update_entry(self.entry, data=self.config)
            _LOGGER.debug(f"Config saved")
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