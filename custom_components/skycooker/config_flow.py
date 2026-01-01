"""Config flow for SkyCooker integration."""

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
from .cooker_connection import CookerConnection
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
        _LOGGER.debug("Init SkyCookerConfigFlow")
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
            if not SkyCooker.get_model_code(name):
                # Model is not supported
                _LOGGER.debug("Model is not supported")
                return self.async_abort(reason='unknown_model')
            if not await self.init_mac(mac):
                # This cooker already configured
                _LOGGER.debug("This cooker already configured")
                return self.async_abort(reason='already_configured')
            if name: self.config[CONF_FRIENDLY_NAME] = name
            # Continue to connect step
            return await self.async_step_connect()

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                _LOGGER.info("🔍 Scanning for Bluetooth devices...")
                
                # Собираем все доступные устройства
                all_devices = []
                skycooker_devices = []
                
                for device in scanner.discovered_devices:
                    name = device.name or "Unknown"
                    address = device.address
                    rssi = device.rssi if hasattr(device, 'rssi') else "N/A"
                    
                    all_devices.append(f"{address} - {name} (RSSI: {rssi})")
                    _LOGGER.debug(f"📡 Found device: {address} - {name} (RSSI: {rssi})")
                    
                    # Фильтрация устройств SkyCooker
                    if device.name and (
                        device.name.startswith("RMC-") or
                        "SkyCooker" in device.name or
                        "Redmond" in device.name or
                        address == "DA:D8:9F:9E:0B:4C"  # Известный MAC адрес
                    ):
                        skycooker_devices.append(device)
                        _LOGGER.info(f"🎯 Found SkyCooker device: {address} - {name} (RSSI: {rssi})")
                
                # Логируем все найденные устройства для диагностики
                if all_devices:
                    _LOGGER.info(f"📋 All discovered devices ({len(all_devices)}):")
                    for device_info in all_devices:
                        _LOGGER.info(f"  - {device_info}")
                else:
                    _LOGGER.warning("⚠️ No Bluetooth devices found")
                
            except Exception as e:
                _LOGGER.error(f"❌ Bluetooth scanner error: {e}")
                return self.async_abort(reason='no_bluetooth')
            
            if len(skycooker_devices) == 0:
                _LOGGER.warning("⚠️ No SkyCooker devices found")
                _LOGGER.info("💡 Tips:")
                _LOGGER.info("  1. Ensure your RMC-M40S is powered on and in pairing mode")
                _LOGGER.info("  2. Check that Bluetooth is enabled on your HomeAssistant server")
                _LOGGER.info("  3. Make sure the device is within range (5-10 meters)")
                _LOGGER.info("  4. Try restarting your RMC-M40S device")
                return self.async_abort(reason='cooker_not_found')
            
            # Создаем список для выбора
            mac_list = [f"{device.address} ({device.name})" for device in skycooker_devices]
            _LOGGER.info(f"✅ Found {len(mac_list)} SkyCooker devices for selection")
            
            schema = vol.Schema(
            {
                vol.Required(CONF_MAC): vol.In(mac_list)
            })
        except Exception as e:
            _LOGGER.error(f"❌ Configuration flow error: {e}")
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
            _LOGGER.debug("Attempting to connect to cooker...")
            cooker = CookerConnection(
                mac=self.config[CONF_MAC],
                key=self.config[CONF_PASSWORD],
                persistent=True,
                adapter=self.config.get(CONF_DEVICE, None),
                hass=self.hass,
                model=self.config.get(CONF_FRIENDLY_NAME, None)
            )
            tries = 3
            while tries > 0 and not cooker._last_connect_ok:
                _LOGGER.debug(f"Connection attempt {4-tries}/3")
                await cooker.update()
                tries = tries - 1
            
            connect_ok = cooker._last_connect_ok
            auth_ok = cooker._last_auth_ok
            cooker.stop()
        
            if not connect_ok:
                errors["base"] = "cant_connect"
                _LOGGER.error("Cannot connect to device")
            elif not auth_ok:
                errors["base"] = "cant_auth"
                _LOGGER.error("Authentication failed")
            else:
                _LOGGER.debug("Connection successful, proceeding to init step")
                return await self.async_step_init()

        # Show form with connection attempt button
        schema = vol.Schema({})
        
        return self.async_show_form(
            step_id="connect",
            errors=errors,
            description_placeholders={
                "mac": self.config[CONF_MAC],
                "model": self.config.get(CONF_FRIENDLY_NAME, "Unknown")
            },
            data_schema=schema
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
