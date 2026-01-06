"""Config flow for SkyCoocker integration."""

import logging
import secrets
import traceback

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import (CONF_DEVICE, CONF_FRIENDLY_NAME, CONF_MAC,
                                  CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.core import callback

from .const import *
from .multicooker_connection import MulticookerConnection

_LOGGER = logging.getLogger(__name__)


class SkyCoockerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SkyCoocker."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        """Get the options flow for this handler."""
        return SkyCoockerConfigFlow(entry=entry)

    def __init__(self, entry = None):
        """Initialize a new SkyCoockerConfigFlow."""
        self.entry = entry
        self.config = {} if not entry else dict(entry.data.items())

    async def init_mac(self, mac):
        """Initialize MAC address."""
        mac = mac.upper()
        mac = mac.replace(':', '').replace('-', '').replace(' ', '')
        mac = ':'.join([mac[p*2:(p*2)+2] for p in range(6)])
        id = f"{DOMAIN}-{mac}"
        if id in self._async_current_ids():
            return False
        await self.async_set_unique_id(id)
        self.config[CONF_MAC] = mac
        # Use the correct fixed key for RMC-M40S as in the working library
        self.config[CONF_PASSWORD] = "0000000000000000"
        # Set default values for missing configuration options
        self.config[CONF_SCAN_INTERVAL] = self.config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self.config[CONF_PERSISTENT_CONNECTION] = self.config.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)
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
            
            # Check if model is supported
            if name and name not in SUPPORTED_MODELS:
                return self.async_abort(reason='unknown_model')
            
            if not await self.init_mac(mac):
                return self.async_abort(reason='already_configured')
            
            if name: self.config[CONF_FRIENDLY_NAME] = name
            
            return await self.async_step_connect()

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                for device in scanner.discovered_devices:
                    _LOGGER.debug(f"🔍 Найдено устройство: {device.address} - {device.name}")
            except:
                _LOGGER.error("🚫 Bluetooth интеграция не работает")
                return self.async_abort(reason='no_bluetooth')
            
            devices_filtered = [device for device in scanner.discovered_devices 
                              if device.name and (device.name.startswith("RMC") or device.name.startswith("RFS"))]
            
            if len(devices_filtered) == 0:
                return self.async_abort(reason='device_not_found')
            
            mac_list = [f"{r.address} ({r.name})" for r in devices_filtered]
            schema = vol.Schema({
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
        # If this is the first call (user_input is None), proceed directly to test connection
        if user_input is None:
            multicooker = MulticookerConnection(
                mac=self.config[CONF_MAC],
                key=self.config[CONF_PASSWORD],
                persistent=True,
                adapter=self.config.get(CONF_DEVICE, None),
                hass=self.hass,
                model=self.config.get(CONF_FRIENDLY_NAME, None)
            )
            tries = 3
            while tries > 0 and not multicooker._last_connect_ok:
                await multicooker.update()
                tries = tries - 1

            connect_ok = multicooker._last_connect_ok
            auth_ok = multicooker._last_auth_ok
            await multicooker.stop_connection()

            if not connect_ok:
                return self.async_abort(reason="cant_connect")
            elif not auth_ok:
                return self.async_abort(reason="cant_auth")
            else:
                # Connection successful, proceed to create entry
                return await self.async_step_init()

        # This should not be reached as we either abort or proceed to init step
        return self.async_abort(reason="unknown")

    async def async_step_init(self, user_input=None):
        """Handle the options step."""
        errors = {}
        if user_input is not None:
            self.config[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.config[CONF_PERSISTENT_CONNECTION] = user_input[CONF_PERSISTENT_CONNECTION]
            fname = f"{self.config.get(CONF_FRIENDLY_NAME, FRIENDLY_NAME)} ({self.config[CONF_MAC]})"
            
            if self.entry:
                self.hass.config_entries.async_update_entry(self.entry, data=self.config)
            
            _LOGGER.info("✅ Конфигурация сохранена")
            return self.async_create_entry(
                title=fname, data=self.config if not self.entry else {}
            )

        schema = vol.Schema({
            vol.Required(CONF_PERSISTENT_CONNECTION, 
                        default=self.config.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)): cv.boolean,
            vol.Required(CONF_SCAN_INTERVAL, 
                        default=self.config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): 
                vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        })

        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=schema
        )