"""Config flow for SkyCooker integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS, CONF_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_AUTH_KEY,
    CONF_CONNECTION_TIMEOUT,
    CONF_DEVICE_NAME,
    CONF_PERSISTENT_CONNECTION,
    CONF_RETRIES,
    CONF_SCAN_TIMEOUT,
    CONF_WAIT_TIME,
    DEFAULT_AUTH_KEY,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PERSISTENT_CONNECTION,
    DEFAULT_RETRIES,
    DEFAULT_SCAN_TIMEOUT,
    DEFAULT_WAIT_TIME,
    DOMAIN,
)
from .cooker_connection import CookerConnection
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)

# Автоматически обнаруженные устройства
STEP_DEVICE_SCHEMA = vol.Schema({})

# Шаг с выбором устройства
STEP_SELECT_DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_ADDRESS): vol.In({}),
})

# Шаг с предустановленными данными
STEP_CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_FRIENDLY_NAME, default="SkyCooker"): str,
    vol.Required(CONF_AUTH_KEY, default=DEFAULT_AUTH_KEY): str,
    vol.Required(CONF_PERSISTENT_CONNECTION, default=DEFAULT_PERSISTENT_CONNECTION): bool,
})

# Шаг настройки параметров подключения
STEP_OPTIONS_SCHEMA = vol.Schema({
    vol.Optional(
        CONF_CONNECTION_TIMEOUT, default=DEFAULT_CONNECTION_TIMEOUT
    ): int,
    vol.Optional(CONF_SCAN_TIMEOUT, default=DEFAULT_SCAN_TIMEOUT): int,
    vol.Optional(CONF_WAIT_TIME, default=DEFAULT_WAIT_TIME): int,
    vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): int,
})


class SkyCookerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SkyCooker."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        self.selected_device: str | None = None
        self.device_info: dict[str, Any] = {}
        _LOGGER.debug("Init SkyCookerConfigFlow")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - device discovery."""
        _LOGGER.debug("Starting device discovery")
        
        # Сканируем Bluetooth устройства
        devices = await self._discover_devices()
        
        if not devices:
            _LOGGER.warning("No SkyCooker devices found")
            return self.async_abort(reason="cooker_not_found")

        if len(devices) == 1:
            # Автоматически выбираем единственное устройство
            device_address = list(devices.keys())[0]
            device_info = devices[device_address]
            _LOGGER.info(f"Auto-selected device: {device_address}")
            return await self.async_step_configure(
                {CONF_ADDRESS: device_address, **device_info}
            )

        # Несколько устройств - предлагаем выбор
        device_options = {
            addr: f"{info.name or 'Unknown'} ({addr})"
            for addr, info in devices.items()
        }
        
        if user_input is not None:
            self.selected_device = user_input[CONF_ADDRESS]
            device_info = devices[self.selected_device]
            _LOGGER.info(f"User selected device: {self.selected_device}")
            return await self.async_step_configure(
                {CONF_ADDRESS: self.selected_device, **device_info}
            )

        # Показываем форму выбора устройства
        schema = vol.Schema({
            vol.Required(CONF_ADDRESS): vol.In(device_options),
        })
        
        return self.async_show_form(
            step_id="select_device",
            data_schema=schema,
            description_placeholders={
                "count": len(devices),
                "devices": "\n".join([f"• {name}" for name in device_options.values()])
            }
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection step."""
        return await self.async_step_user(user_input)

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration step with pre-filled data."""
        _LOGGER.debug("Configure step with device: %s", user_input.get(CONF_ADDRESS))
        
        self.device_info = user_input
        device_name = user_input.get("name", "SkyCooker")
        device_address = user_input[CONF_ADDRESS]
        
        if user_input is not None:
            # Проверяем соединение с предустановленными параметрами
            try:
                cooker = CookerConnection(
                    mac=device_address,
                    key=user_input.get(CONF_AUTH_KEY, DEFAULT_AUTH_KEY),
                    persistent=user_input.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION),
                    adapter=None,
                    hass=self.hass,
                    model=DEFAULT_DEVICE_NAME
                )

                if await cooker.connect():
                    await cooker.disconnect()
                    _LOGGER.info("Successfully connected to device during configuration")
                    
                    # Сохраняем данные и переходим к опциям
                    config_data = {
                        CONF_ADDRESS: device_address,
                        CONF_FRIENDLY_NAME: user_input[CONF_FRIENDLY_NAME],
                        CONF_AUTH_KEY: user_input[CONF_AUTH_KEY],
                        CONF_PERSISTENT_CONNECTION: user_input[CONF_PERSISTENT_CONNECTION],
                        CONF_DEVICE_NAME: DEFAULT_DEVICE_NAME,
                    }
                    
                    return await self.async_step_options(config_data)
                else:
                    _LOGGER.warning("Cannot connect to device during configuration")
                    return self.async_abort(reason="cannot_connect")
                    
            except Exception as exc:
                _LOGGER.error("Error during device configuration: %s", exc)
                return self.async_abort(reason="cannot_connect")

        # Создаем схему с предустановленными значениями
        schema = vol.Schema({
            vol.Required(
                CONF_FRIENDLY_NAME,
                default=f"SkyCooker {device_address[-5:]}"
            ): str,
            vol.Required(
                CONF_AUTH_KEY,
                default=DEFAULT_AUTH_KEY
            ): str,
            vol.Required(
                CONF_PERSISTENT_CONNECTION,
                default=DEFAULT_PERSISTENT_CONNECTION
            ): bool,
        })

        return self.async_show_form(
            step_id="configure",
            data_schema=schema,
            description_placeholders={
                "device_name": device_name,
                "device_address": device_address
            }
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the options step."""
        _LOGGER.debug("Options step")
        
        if user_input is not None:
            # Добавляем параметры подключения к данным
            config_data = {
                **user_input,
                CONF_CONNECTION_TIMEOUT: DEFAULT_CONNECTION_TIMEOUT,
                CONF_SCAN_TIMEOUT: DEFAULT_SCAN_TIMEOUT,
                CONF_WAIT_TIME: DEFAULT_WAIT_TIME,
                CONF_RETRIES: DEFAULT_RETRIES,
            }
            
            # Создаем запись конфигурации
            return self.async_create_entry(
                title=config_data[CONF_FRIENDLY_NAME],
                data=config_data,
            )

        schema = vol.Schema({
            vol.Optional(
                CONF_CONNECTION_TIMEOUT, default=DEFAULT_CONNECTION_TIMEOUT
            ): int,
            vol.Optional(CONF_SCAN_TIMEOUT, default=DEFAULT_SCAN_TIMEOUT): int,
            vol.Optional(CONF_WAIT_TIME, default=DEFAULT_WAIT_TIME): int,
            vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): int,
        })

        return self.async_show_form(
            step_id="options",
            data_schema=schema,
            description_placeholders={
                "device_name": self.device_info.get("name", "SkyCooker"),
                "device_address": self.device_info.get(CONF_ADDRESS, "")
            }
        )

    async def _discover_devices(self) -> dict[str, BluetoothServiceInfoBleak]:
        """Discover SkyCooker devices via Bluetooth."""
        _LOGGER.debug("Scanning for SkyCooker devices...")
        
        discovered_devices = {}
        try:
            # Получаем список обнаруженных Bluetooth устройств
            for discovery_info in async_discovered_service_info(self.hass):
                device_name = discovery_info.name or ""
                device_address = discovery_info.address
                
                # Фильтруем устройства по имени (если есть) или по наличию нужных характеристик
                if (device_name.lower().startswith("rmc-") or
                    device_name.lower().startswith("skycooker") or
                    device_name.lower().startswith("redmond")):
                    
                    _LOGGER.debug(f"Found potential SkyCooker device: {device_name} ({device_address})")
                    discovered_devices[device_address] = discovery_info
                    
        except Exception as e:
            _LOGGER.error("Error during device discovery: %s", e)
            
        _LOGGER.info(f"Found {len(discovered_devices)} SkyCooker device(s)")
        return discovered_devices

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SkyCookerOptionsFlowHandler(config_entry)


class SkyCookerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle SkyCooker options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_options = self.config_entry.options
        schema_dict = {
            vol.Optional(
                CONF_CONNECTION_TIMEOUT,
                default=current_options.get(CONF_CONNECTION_TIMEOUT, DEFAULT_CONNECTION_TIMEOUT)
            ): int,
            vol.Optional(
                CONF_SCAN_TIMEOUT,
                default=current_options.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT)
            ): int,
            vol.Optional(
                CONF_WAIT_TIME,
                default=current_options.get(CONF_WAIT_TIME, DEFAULT_WAIT_TIME)
            ): int,
            vol.Optional(
                CONF_RETRIES,
                default=current_options.get(CONF_RETRIES, DEFAULT_RETRIES)
            ): int,
            vol.Optional(
                CONF_PERSISTENT_CONNECTION,
                default=current_options.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)
            ): bool,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
