"""Config flow for SkyCooker integration."""

import logging
import traceback
from typing import Optional, Dict, Any, List

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
    """Поток настройки для интеграции SkyCooker."""
    
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry) -> "SkyCookerConfigFlow":
        """Получение потока опций для этого обработчика.
        
        Args:
            entry: Конфигурационный вход для получения опций.
            
        Returns:
            Экземпляр SkyCookerConfigFlow для обработки опций.
        """
        return SkyCookerConfigFlow(entry=entry)

    def __init__(self, entry: Optional[config_entries.ConfigEntry] = None):
        """Инициализация нового потока настройки SkyCooker.
        
        Args:
            entry: Необязательный конфигурационный вход для существующей конфигурации.
        """
        self.entry = entry
        self.config: Dict[str, Any] = {} if not entry else dict(entry.data.items())

    async def init_mac(self, mac: str) -> bool:
        """Инициализация и проверка MAC-адреса.
        
        Args:
            mac: MAC-адрес для инициализации.
            
        Returns:
            True, если MAC-адрес корректен и не настроен, False в противном случае.
        """
        mac = mac.upper()
        mac = mac.replace(':', '').replace('-', '').replace(' ', '')
        mac = ':'.join([mac[p*2:(p*2)+2] for p in range(6)])
        unique_id = f"{DOMAIN}-{mac}"
        if unique_id in self._async_current_ids():
            return False
        await self.async_set_unique_id(unique_id)
        self.config[CONF_MAC] = mac
        self.config[CONF_PASSWORD] = list(bytes.fromhex("0000000000000000"))
        return True

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обработка шага пользователя.
        
        Args:
            user_input: Необязательные данные ввода пользователя.
            
        Returns:
            Результат шага сканирования.
        """
        return await self.async_step_scan()
    
    async def async_step_scan(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обработка шага сканирования.
        
        Args:
            user_input: Необязательные данные ввода пользователя.
            
        Returns:
            Форма для отображения или результат следующего шага.
        """
        errors: Dict[str, str] = {}
        if user_input is not None:
            spl = user_input[CONF_MAC].split(' ', maxsplit=1)
            mac = spl[0]
            name = spl[1][1:-1] if len(spl) >= 2 else None
            if not SkyCooker.get_model_code(name):
                return self.async_abort(reason='unknown_model')
            if not await self.init_mac(mac):
                return self.async_abort(reason='already_configured')
            if name:
                self.config[CONF_FRIENDLY_NAME] = name
            return await self.async_step_connect()

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                for device in scanner.discovered_devices:
                    _LOGGER.debug(f"Device found: {device.address} - {device.name}")
            except Exception as e:
                _LOGGER.error(f"Интеграция Bluetooth не работает: {e}")
                return self.async_abort(reason='no_bluetooth')
            
            devices_filtered: List[Any] = [
                device for device in scanner.discovered_devices
                if device.name and (device.name.startswith("RMC-") or device.name.startswith("RFS-"))
            ]
            if len(devices_filtered) == 0:
                return self.async_abort(reason='skycooker_not_found')
            
            mac_list: List[str] = [f"{r.address} ({r.name})" for r in devices_filtered]
            schema = vol.Schema({
                vol.Required(CONF_MAC): vol.In(mac_list)
            })
        except Exception as e:
            _LOGGER.error(f"Ошибка во время сканирования: {traceback.format_exc()}")
            return self.async_abort(reason='unknown')
        
        return self.async_show_form(
            step_id="scan",
            errors=errors,
            data_schema=schema
        )

    async def async_step_connect(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обработка шага подключения.
        
        Args:
            user_input: Необязательные данные ввода пользователя.
            
        Returns:
            Форма для отображения или результат следующего шага.
        """
        errors: Dict[str, str] = {}
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
                tries -= 1
              
            connect_ok = skycooker.last_connect_ok
            auth_ok = skycooker.last_auth_ok
            await skycooker.stop()
          
            if not connect_ok:
                errors["base"] = "не_удается_подключиться"
            elif not auth_ok:
                errors["base"] = "не_удается_аутентифицироваться"
            else:
                return await self.async_step_init()

        return self.async_show_form(
            step_id="connect",
            errors=errors,
            data_schema=vol.Schema({})
        )

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обработка шага инициализации.
        
        Args:
            user_input: Необязательные данные ввода пользователя.
            
        Returns:
            Форма для отображения или результат создания входа.
        """
        errors: Dict[str, str] = {}
        if user_input is not None:
            self.config[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.config[CONF_PERSISTENT_CONNECTION] = user_input[CONF_PERSISTENT_CONNECTION]
            fname = f"{self.config.get(CONF_FRIENDLY_NAME, SKYCOOKER_NAME)} ({self.config[CONF_MAC]})"
            if self.entry:
                self.hass.config_entries.async_update_entry(self.entry, data=self.config)
            _LOGGER.debug(f"Конфигурация сохранена")
            return self.async_create_entry(
                title=fname, data=self.config if not self.entry else {}
            )

        schema = vol.Schema({
            vol.Required(
                CONF_PERSISTENT_CONNECTION,
                default=self.config.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)
            ): cv.boolean,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=self.config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        })

        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=schema
        )