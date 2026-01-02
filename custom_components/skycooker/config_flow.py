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

# Шаг 1: Поиск устройства
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
        vol.Required(CONF_ADDRESS): str,
        vol.Optional(CONF_AUTH_KEY, default=DEFAULT_AUTH_KEY): str,
        vol.Optional(CONF_FRIENDLY_NAME): str,
    }
)

# Шаг 2: Настройка параметров подключения
STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_CONNECTION_TIMEOUT, default=DEFAULT_CONNECTION_TIMEOUT
        ): int,
        vol.Optional(CONF_SCAN_TIMEOUT, default=DEFAULT_SCAN_TIMEOUT): int,
        vol.Optional(CONF_WAIT_TIME, default=DEFAULT_WAIT_TIME): int,
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): int,
        vol.Optional(
            CONF_PERSISTENT_CONNECTION, default=DEFAULT_PERSISTENT_CONNECTION
        ): bool,
    }
)


class SkyCookerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SkyCooker."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        self.device_data: dict[str, Any] = {}
        _LOGGER.debug("Init SkyCookerConfigFlow")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Init SkyCookerConfigFlow 2")
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Init SkyCookerConfigFlow 3")
            # Сохраняем данные пользователя
            self.device_data.update(user_input)

            # Проверяем, что устройство доступно
            try:
                _LOGGER.debug("Init SkyCookerConfigFlow 4")
                # Создаем временное соединение для проверки
                cooker = CookerConnection(
                    mac=user_input[CONF_ADDRESS],
                    key=user_input.get(CONF_AUTH_KEY, DEFAULT_AUTH_KEY),
                    persistent=False,  # Временно отключаем постоянное соединение
                    adapter=None,
                    hass=self.hass,
                    model=user_input.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
                )

                _LOGGER.debug("Init SkyCookerConfigFlow 5")
                # Проверяем соединение
                if await cooker.connect():
                    _LOGGER.debug("Init SkyCookerConfigFlow 6")
                    await cooker.disconnect()
                    _LOGGER.debug("Init SkyCookerConfigFlow 7")
                    # Сохраняем данные и переходим к следующему шагу
                    self.hass.data.setdefault(DOMAIN, {})
                    self.hass.data[DOMAIN]["temp_config"] = self.device_data
                    _LOGGER.debug("Init SkyCookerConfigFlow 8")
                    return await self.async_step_options()
                else:
                    _LOGGER.debug("Init SkyCookerConfigFlow 9")
                    errors["base"] = "cannot_connect"
            except Exception as exc:
                _LOGGER.debug("Init SkyCookerConfigFlow 10")
                _LOGGER.error("Error connecting to SkyCooker: %s", exc)
                errors["base"] = "cannot_connect"

        # Если это первый вызов или есть ошибки, показываем форму
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Соединяем данные из обоих шагов
            config_data = {**self.device_data, **user_input}

            try:
                # Проверяем соединение с новыми параметрами
                cooker = CookerConnection(
                    mac=config_data[CONF_ADDRESS],
                    key=config_data.get(CONF_AUTH_KEY, DEFAULT_AUTH_KEY),
                    persistent=config_data[CONF_PERSISTENT_CONNECTION],
                    adapter=None,
                    hass=self.hass,
                    model=config_data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
                )

                if await cooker.connect():
                    await cooker.disconnect()

                    # Создаем запись конфигурации
                    return self.async_create_entry(
                        title=config_data.get(
                            CONF_FRIENDLY_NAME,
                            f"SkyCooker {config_data[CONF_ADDRESS]}",
                        ),
                        data=config_data,
                    )
                else:
                    errors["base"] = "cannot_connect"
            except Exception as exc:
                _LOGGER.error("Error connecting to SkyCooker with options: %s", exc)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="options",
            data_schema=STEP_OPTIONS_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Init SkyCookerConfigFlow")
        errors: dict[str, str] = {}

        if user_input is not None:
            # Сохраняем данные пользователя
            self.device_data.update(user_input)

            # Проверяем, что устройство доступно
            try:
                # Создаем временное соединение для проверки
                cooker = CookerConnection(
                    mac=user_input[CONF_ADDRESS],
                    key=user_input.get(CONF_AUTH_KEY, DEFAULT_AUTH_KEY),
                    persistent=False,  # Временно отключаем постоянное соединение
                    adapter=None,
                    hass=self.hass,
                    model=user_input.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME)
                )

                # Проверяем соединение
                if await cooker.connect():
                    await cooker.disconnect()
                    # Сохраняем данные и переходим к следующему шагу
                    self.hass.data.setdefault(DOMAIN, {})
                    self.hass.data[DOMAIN]["temp_config"] = self.device_data
                    return await self.async_step_options()
                else:
                    errors["base"] = "cannot_connect"
            except Exception as exc:
                _LOGGER.error("Error connecting to SkyCooker: %s", exc)
                errors["base"] = "cannot_connect"

        # Если это первый вызов или есть ошибки, показываем форму
        return self.async_show_form(
            step_id="init",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

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

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CONNECTION_TIMEOUT,
                    default=self.config_entry.options.get(
                        CONF_CONNECTION_TIMEOUT, DEFAULT_CONNECTION_TIMEOUT
                    ),
                ): int,
                vol.Optional(
                    CONF_SCAN_TIMEOUT,
                    default=self.config_entry.options.get(
                        CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT
                    ),
                ): int,
                vol.Optional(
                    CONF_WAIT_TIME,
                    default=self.config_entry.options.get(
                        CONF_WAIT_TIME, DEFAULT_WAIT_TIME
                    ),
                ): int,
                vol.Optional(
                    CONF_RETRIES,
                    default=self.config_entry.options.get(
                        CONF_RETRIES, DEFAULT_RETRIES
                    ),
                ): int,
                vol.Optional(
                    CONF_PERSISTENT_CONNECTION,
                    default=self.config_entry.options.get(
                        CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION
                    ),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
