"""Config flow for SkyCooker integration."""

import logging
from typing import Optional, Dict, Any, List

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import (CONF_DEVICE, CONF_FRIENDLY_NAME, CONF_MAC,
                                   CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_PERSISTENT_CONNECTION, CONF_MODEL, CONF_FAVORITE_PROGRAMS,
    DEFAULT_SCAN_INTERVAL, DEFAULT_PERSISTENT_CONNECTION, MAX_FAVORITE_PROGRAMS,
    SKYCOOKER_NAME, MODEL_3
)
from .programs import get_program_options

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
            try:
                spl = user_input[CONF_MAC].split(' ', maxsplit=1)
                mac = spl[0]
                name = spl[1][1:-1] if len(spl) >= 2 else None
                if not SkyCooker.get_model_id(name):
                    return self.async_abort(reason='unknown_model')
                if not await self.init_mac(mac):
                    return self.async_abort(reason='already_configured')
                if name:
                    self.config[CONF_FRIENDLY_NAME] = name
                    self.config[CONF_MODEL] = SkyCooker.get_model_id(name)
                return await self.async_step_connect()
            except Exception as e:
                _LOGGER.error(f"Ошибка при обработке ввода пользователя: {e}")
                return self.async_abort(reason='invalid_input')
       
        try:
            scanner = bluetooth.async_get_scanner(self.hass)
            if not scanner:
                _LOGGER.error("Сканер Bluetooth не инициализирован")
                return self.async_abort(reason='no_bluetooth')
           
            devices_filtered: List[Any] = [
                device for device in scanner.discovered_devices
                if device.name and (device.name.startswith("RMC-") or device.name.startswith("RFS-"))
            ]
            if len(devices_filtered) == 0:
                _LOGGER.error("Устройство не найдено")
                return self.async_abort(reason='device_not_found')
            
            mac_list: List[str] = [f"{r.address} ({r.name})" for r in devices_filtered]
            schema = vol.Schema({
                vol.Required(CONF_MAC): vol.In(mac_list)
            })
        except Exception as e:
            _LOGGER.error(f"Ошибка во время сканирования: {e}")
            return self.async_abort(reason='scan_failed')
       
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
            try:
                # Проверка наличия необходимых параметров
                if not self.config.get(CONF_MAC):
                    _LOGGER.error("Отсутствует MAC-адрес для подключения")
                    return self.async_abort(reason='invalid_config')
                if not self.config.get(CONF_PASSWORD):
                    _LOGGER.error("Отсутствует пароль для подключения")
                    return self.async_abort(reason='invalid_config')
                
                skycooker = SkyCookerConnection(
                    mac=self.config[CONF_MAC],
                    key=self.config[CONF_PASSWORD],
                    persistent=True,
                    adapter=self.config.get(CONF_DEVICE, None),
                    hass=self.hass,
                    model_name=self.config.get(CONF_FRIENDLY_NAME, None)
                )
                tries = 3
                while tries > 0 and not skycooker.last_connect_ok:
                    await skycooker.update()
                    tries -= 1
                 
                connect_ok = getattr(skycooker, 'last_connect_ok', False)
                auth_ok = getattr(skycooker, 'last_auth_ok', False)
                await skycooker.stop()
                
                if not connect_ok:
                    errors["base"] = "cant_connect"
                elif not auth_ok:
                    errors["base"] = "cant_auth"
                else:
                    return await self.async_step_init()
            except Exception as e:
                _LOGGER.error(f"Ошибка при подключении: {e}")
                return self.async_abort(reason='connection_failed')
    
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
        
        # Получение модели устройства
        model = self.config.get(CONF_MODEL, MODEL_3)
       
        # Получение списка доступных программ для модели, исключая PROGRAM_STANDBY и PROGRAM_NONE
        available_programs = get_program_options(self.hass, model, False)
        
        if user_input is not None:
            try:
                # Проверка наличия необходимых параметров
                if not self.config.get(CONF_MAC):
                    _LOGGER.error("Отсутствует MAC-адрес в конфигурации")
                    return self.async_abort(reason='invalid_config')
                if not self.config.get(CONF_PASSWORD):
                    _LOGGER.error("Отсутствует пароль в конфигурации")
                    return self.async_abort(reason='invalid_config')
                  
                # Проверка и обработка CONF_SCAN_INTERVAL
                try:
                    scan_interval = user_input[CONF_SCAN_INTERVAL]
                    if isinstance(scan_interval, str):
                        scan_interval = int(scan_interval)
                    self.config[CONF_SCAN_INTERVAL] = scan_interval
                except (ValueError, KeyError) as e:
                    _LOGGER.error(f"Некорректное значение CONF_SCAN_INTERVAL: {e}")
                    return self.async_abort(reason='invalid_input')
                  
                # Проверка и обработка CONF_PERSISTENT_CONNECTION
                try:
                    persistent_connection = user_input[CONF_PERSISTENT_CONNECTION]
                    if isinstance(persistent_connection, str):
                        persistent_connection = persistent_connection.lower() == 'true'
                    self.config[CONF_PERSISTENT_CONNECTION] = persistent_connection
                except (ValueError, KeyError) as e:
                    _LOGGER.error(f"Некорректное значение CONF_PERSISTENT_CONNECTION: {e}")
                    return self.async_abort(reason='invalid_input')
                  
                # Сохранение избранных программ
                if CONF_FAVORITE_PROGRAMS in user_input:
                    favorite_programs = user_input[CONF_FAVORITE_PROGRAMS]
                    # Ограничение до MAX_FAVORITE_PROGRAMS
                    if len(favorite_programs) > MAX_FAVORITE_PROGRAMS:
                        favorite_programs = favorite_programs[:MAX_FAVORITE_PROGRAMS]
                    self.config[CONF_FAVORITE_PROGRAMS] = favorite_programs
                   
                fname = f"{self.config.get(CONF_FRIENDLY_NAME, SKYCOOKER_NAME)} ({self.config[CONF_MAC]})"
                if self.entry:
                    try:
                        self.hass.config_entries.async_update_entry(self.entry, data=self.config)
                    except Exception as e:
                        _LOGGER.error(f"Ошибка при обновлении существующей записи: {e}")
                        return self.async_abort(reason='update_failed')
                return self.async_create_entry(
                    title=fname, data=self.config
                )
            except Exception as e:
                _LOGGER.error(f"Ошибка при сохранении конфигурации: {e}")
                return self.async_abort(reason='config_save_failed')
               
        try:
            # Удаляем пустую строку из начала списка программ (она используется как подсказка)
            available_programs_without_hint = [program for program in available_programs if program]
            
            # Создание схемы для выбора избранных программ
            favorite_programs_validator = cv.multi_select(available_programs_without_hint)
                  
            schema = vol.Schema({
                vol.Required(
                    CONF_PERSISTENT_CONNECTION,
                    default=self.config.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)
                ): cv.boolean,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                vol.Optional(
                    CONF_FAVORITE_PROGRAMS,
                    default=self.config.get(CONF_FAVORITE_PROGRAMS, [])
                ): favorite_programs_validator,
            })
                
            # Получение описания для избранных программ из переводов
            translations = self.hass.data.get("skycooker_translations", {})
            favorite_program_description = translations.get("config", {}).get("step", {}).get("init", {}).get("data", {}).get("favorite_programs", "Favorite programs (select up to 5 programs to display as favorites)")
                 
            return self.async_show_form(
                step_id="init",
                errors=errors,
                data_schema=schema,
                description_placeholders={"favorite_program_description": favorite_program_description}
            )
        except Exception as e:
            _LOGGER.error(f"Ошибка при инициализации формы: {e}")
            return self.async_abort(reason='init_failed')

