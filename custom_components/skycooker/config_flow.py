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

        # Агрессивное сканирование перед показом формы
        _LOGGER.info("🚀 Starting SkyCooker discovery process...")
        
        try:
            # Пытаемся найти устройства несколько раз с паузами
            scanner = bluetooth.async_get_scanner(self.hass)
            found_devices = []
            
            for scan_attempt in range(5):
                _LOGGER.debug(f"🔍 Scan attempt {scan_attempt + 1}/5")
                
                # Делаем сканирование
                current_devices = scanner.discovered_devices
                _LOGGER.debug(f"📡 Found {len(current_devices)} devices")
                
                # Фильтруем SkyCooker устройства
                for device in current_devices:
                    if device.name and (
                        device.name.startswith("RMC-") or
                        "SkyCooker" in device.name or
                        "Redmond" in device.name or
                        "Multicooker" in device.name or
                        "Cooker" in device.name or
                        device.address.upper() in ["DA:D8:9F:9E:0B:4C", "DA-D8-9F-9E-0B-4C", "DAD89F9E0B4C"]
                    ):
                        if device not in found_devices:
                            found_devices.append(device)
                            rssi = getattr(device, 'rssi', None)
                            rssi_info = f" (RSSI: {rssi})" if rssi is not None else ""
                            _LOGGER.info(f"🎯 SkyCooker candidate: {device.name} - {device.address}{rssi_info}")
                
                # Если нашли устройства, можно остановиться
                if found_devices:
                    _LOGGER.info(f"✅ Found {len(found_devices)} SkyCooker devices, proceeding to selection")
                    break
                
                # Пауза между попытками
                await asyncio.sleep(1.0)
            
            if not found_devices:
                _LOGGER.warning("⚠️ No SkyCooker devices found in any scan attempt")
                _LOGGER.info("💡 Try these steps:")
                _LOGGER.info("  1. Power cycle your RMC-M40S (turn off and on)")
                _LOGGER.info("  2. Put device in pairing mode (hold bluetooth button)")
                _LOGGER.info("  3. Move closer to HomeAssistant server")
                _LOGGER.info("  4. Check Bluetooth adapter status")
                
                # Показываем все найденные устройства для диагностики
                all_devices = scanner.discovered_devices
                if all_devices:
                    _LOGGER.info("📋 All discovered Bluetooth devices:")
                    for device in all_devices:
                        rssi = getattr(device, 'rssi', None)
                        rssi_info = f" (RSSI: {rssi})" if rssi is not None else ""
                        _LOGGER.info(f"  - {device.name or 'Unknown'} - {device.address}{rssi_info}")
                else:
                    _LOGGER.info("📋 No Bluetooth devices discovered at all")
                
                return self.async_abort(reason='cooker_not_found')

        except Exception as e:
            _LOGGER.error(f"❌ Scan preparation error: {e}")
            return self.async_abort(reason='no_bluetooth')

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                _LOGGER.info("🔍 Starting aggressive Bluetooth scan for SkyCooker devices...")
                
                # Агрессивное сканирование - пробуем несколько раз
                all_devices = []
                skycooker_devices = []
                scan_attempts = 3
                
                for attempt in range(scan_attempts):
                    _LOGGER.debug(f"📡 Scan attempt {attempt + 1}/{scan_attempts}")
                    
                    # Делаем паузу между попытками для стабильности
                    if attempt > 0:
                        await asyncio.sleep(2.0)
                    
                    current_devices = scanner.discovered_devices
                    _LOGGER.debug(f"📡 Found {len(current_devices)} devices in attempt {attempt + 1}")
                    
                    for device in current_devices:
                        name = device.name or "Unknown"
                        address = device.address
                        rssi = getattr(device, 'rssi', None)
                        
                        # Собираем все устройства для диагностики
                        rssi_str = f"RSSI: {rssi}" if rssi is not None else "RSSI: N/A"
                        device_info = f"{address} - {name} ({rssi_str})"
                        
                        # Избегаем дубликатов
                        if device_info not in all_devices:
                            all_devices.append(device_info)
                            _LOGGER.debug(f"📡 Device discovered: {device_info}")
                            
                            # Расширенная фильтрация SkyCooker устройств
                            is_skycooker = False
                            reasons = []
                            
                            if device.name:
                                if device.name.startswith("RMC-"):
                                    is_skycooker = True
                                    reasons.append("RMC- prefix")
                                if "SkyCooker" in device.name:
                                    is_skycooker = True
                                    reasons.append("SkyCooker in name")
                                if "Redmond" in device.name:
                                    is_skycooker = True
                                    reasons.append("Redmond in name")
                                if "Multicooker" in device.name:
                                    is_skycooker = True
                                    reasons.append("Multicooker in name")
                                if "Cooker" in device.name:
                                    is_skycooker = True
                                    reasons.append("Cooker in name")
                            
                            # Проверка по MAC адресу (если известен)
                            if address.upper() in ["DA:D8:9F:9E:0B:4C", "DA-D8-9F-9E-0B-4C", "DAD89F9E0B4C"]:
                                is_skycooker = True
                                reasons.append("Known MAC address")
                            
                            # Проверка по силе сигнала (если устройство близко)
                            if rssi is not None and rssi > -80:  # Сильный сигнал
                                # Дополнительная проверка для устройств с нестандартными именами
                                if any(keyword in name.lower() for keyword in ['r', 'm', 'c', 'sky', 'red']):
                                    is_skycooker = True
                                    reasons.append("Signal strength + name pattern")
                            
                            if is_skycooker:
                                # Проверяем, не добавлено ли уже это устройство
                                if not any(d.address == address for d in skycooker_devices):
                                    skycooker_devices.append(device)
                                    reasons_str = ", ".join(reasons) if reasons else "Unknown reason"
                                    _LOGGER.info(f"🎯 SkyCooker candidate found: {address} - {name} ({rssi_str}) [{reasons_str}]")
                
                # Логируем все найденные устройства для диагностики
                if all_devices:
                    _LOGGER.info(f"📋 Total devices discovered: {len(all_devices)}")
                    for device_info in sorted(all_devices):
                        _LOGGER.info(f"  - {device_info}")
                else:
                    _LOGGER.warning("⚠️ No Bluetooth devices found in any scan attempt")
                
            except Exception as e:
                _LOGGER.error(f"❌ Bluetooth scanner error: {e}")
                _LOGGER.error(traceback.format_exc())
                return self.async_abort(reason='no_bluetooth')
            
            if len(skycooker_devices) == 0:
                _LOGGER.warning("⚠️ No SkyCooker devices found after aggressive scanning")
                _LOGGER.info("💡 Troubleshooting tips:")
                _LOGGER.info("  1. Ensure your RMC-M40S is powered ON and in pairing mode (bluetooth indicator blinking)")
                _LOGGER.info("  2. Check that Bluetooth is enabled and working on your HomeAssistant server")
                _LOGGER.info("  3. Make sure the device is within close range (3-5 meters recommended)")
                _LOGGER.info("  4. Try restarting your RMC-M40S device and putting it in pairing mode again")
                _LOGGER.info("  5. Check if the device is already connected to another application")
                _LOGGER.info("  6. Verify that your Bluetooth adapter supports the required Bluetooth Low Energy features")
                
                # Показываем все найденные устройства, даже если они не распознаны как SkyCooker
                if all_devices:
                    _LOGGER.info("🔍 All discovered devices (check if your RMC-M40S is listed):")
                    for device_info in all_devices:
                        _LOGGER.info(f"  - {device_info}")
                
                return self.async_abort(reason='cooker_not_found')
            
            # Создаем список для выбора с дополнительной информацией
            mac_list = []
            for device in skycooker_devices:
                rssi = getattr(device, 'rssi', None)
                rssi_info = f" RSSI:{rssi}" if rssi is not None else ""
                device_entry = f"{device.address} ({device.name}{rssi_info})"
                mac_list.append(device_entry)
                _LOGGER.info(f"✅ Device added to selection list: {device_entry}")
            
            _LOGGER.info(f"🎯 Final selection list created with {len(mac_list)} devices")
            
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
