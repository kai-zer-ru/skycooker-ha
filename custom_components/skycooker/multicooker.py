"""SkyCooker Multicooker."""
import logging
from datetime import timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.const import (ATTR_SW_VERSION, CONF_FRIENDLY_NAME, CONF_SCAN_INTERVAL)
from homeassistant.helpers.dispatcher import (async_dispatcher_connect)
from homeassistant.helpers.entity import DeviceInfo

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the SkyCooker multicooker entry."""
    cooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    
    # Check if this is a multicooker (RMC-M40S or similar)
    if cooker.model_code in [SkyCooker.MODELS_3, SkyCooker.MODELS_4, SkyCooker.MODELS_5, SkyCooker.MODELS_6, SkyCooker.MODELS_7]:
        entities = [
            SkyMulticooker(hass, entry),
            SkyMulticookerModeSelect(hass, entry),
            SkyMulticookerTemperatureNumber(hass, entry),
            SkyMulticookerCookHoursNumber(hass, entry),
            SkyMulticookerCookMinutesNumber(hass, entry),
            SkyMulticookerStartButton(hass, entry),
            SkyMulticookerStopButton(hass, entry),
        ]
        async_add_entities(entities)


class SkyMulticooker(ButtonEntity):
    """Representation of a SkyCooker multicooker device."""

    def __init__(self, hass, entry):
        """Initialize the multicooker device."""
        self.hass = hass
        self.entry = entry

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return self.entry.entry_id + "_multicooker"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()

    @property
    def icon(self):
        return "mdi:rice-cooker"

    @property
    def device_class(self):
        return None

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def assumed_state(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    @property
    def entity_category(self):
        return None

    @property
    def extra_state_attributes(self):
        sw_version = self.cooker.sw_version
        if sw_version:
            major, minor = sw_version
            sw_version = f"{major}.{minor}"
            updates = {ATTR_SW_VERSION: sw_version}
            self.hass.config_entries.async_update_entry(
                self.entry, data={**self.entry.data, **updates}
            )
        
        status = self.cooker.status
        if status:
            current_mode_name = SkyCooker.MODE_NAMES.get(status.mode, "Unknown")
        else:
            current_mode_name = "Unknown"
            
        data = {
            "connected": self.cooker.connected,
            "current_mode": current_mode_name,
            "current_mode_code": status.mode if status else None,
            "is_on": status.is_on if status else False,
            "current_temperature": status.current_temp if status else 0,
            "target_temperature": status.target_temp if status else 0,
            "cook_hours": status.cook_hours if status else 0,
            "cook_minutes": status.cook_minutes if status else 0,
            "wait_hours": status.wait_hours if status else 0,
            "wait_minutes": status.wait_minutes if status else 0,
            "error_code": status.error_code if status else None,
            "auth_ok": self.cooker.auth_ok,
            "sw_version": sw_version,
            "success_rate": self.cooker.success_rate,
            "persistent_connection": self.cooker.persistent,
            "poll_interval": self.entry.data.get(CONF_SCAN_INTERVAL, 0),
        }
        return data

    @property
    def is_on(self):
        """If the multicooker is currently running."""
        status = self.cooker.status
        return status.is_on if status else False

    async def async_press(self, **kwargs):
        """Start the multicooker with current settings."""
        await self.cooker.start_cooking()

    async def async_turn_on(self, **kwargs):
        """Turn the multicooker on."""
        await self.async_press(**kwargs)

    async def async_turn_off(self, **kwargs):
        """Turn the multicooker off."""
        await self.cooker.stop_cooking()


class SkyMulticookerModeSelect(SelectEntity):
    """Representation of a SkyCooker multicooker mode selector."""

    def __init__(self, hass, entry):
        """Initialize the mode selector."""
        self.hass = hass
        self.entry = entry
        self._attr_options = list(SkyCooker.MODE_NAMES.values())

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return self.entry.entry_id + "_multicooker_mode"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "") + " Mode").strip()

    @property
    def icon(self):
        return "mdi:stove"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    @property
    def current_option(self):
        """Return the current selected mode."""
        status = self.cooker.status
        if status:
            return SkyCooker.MODE_NAMES.get(status.mode, "Standby")
        return "Standby"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Find the mode code for the selected option
        mode_code = None
        for code, name in SkyCooker.MODE_NAMES.items():
            if name == option:
                mode_code = code
                break
        
        if mode_code is not None:
            await self.cooker.set_target_program(mode_code)
            self.async_write_ha_state()


class SkyMulticookerTemperatureNumber(NumberEntity):
    """Representation of a SkyCooker multicooker temperature setting."""

    def __init__(self, hass, entry):
        """Initialize the temperature number."""
        self.hass = hass
        self.entry = entry
        self._attr_native_min_value = SkyCooker.MIN_TEMP
        self._attr_native_max_value = SkyCooker.MAX_TEMP
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "°C"

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return self.entry.entry_id + "_multicooker_temperature"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "") + " Temperature").strip()

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    @property
    def native_value(self):
        """Return the current temperature setting."""
        status = self.cooker.status
        return status.target_temp if status else 0

    async def async_set_native_value(self, value: float) -> None:
        """Set the temperature."""
        await self.cooker.set_target_temperature(int(value))
        self.async_write_ha_state()


class SkyMulticookerCookHoursNumber(NumberEntity):
    """Representation of a SkyCooker multicooker cook hours setting."""

    def __init__(self, hass, entry):
        """Initialize the cook hours number."""
        self.hass = hass
        self.entry = entry
        self._attr_native_min_value = 0
        self._attr_native_max_value = 23
        self._attr_native_step = 1

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return self.entry.entry_id + "_multicooker_cook_hours"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "") + " Cook Hours").strip()

    @property
    def icon(self):
        return "mdi:clock-outline"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    @property
    def native_value(self):
        """Return the current cook hours."""
        status = self.cooker.status
        return status.cook_hours if status else 0

    async def async_set_native_value(self, value: float) -> None:
        """Set the cook hours."""
        await self.cooker.set_cook_hours(int(value))
        self.async_write_ha_state()


class SkyMulticookerCookMinutesNumber(NumberEntity):
    """Representation of a SkyCooker multicooker cook minutes setting."""

    def __init__(self, hass, entry):
        """Initialize the cook minutes number."""
        self.hass = hass
        self.entry = entry
        self._attr_native_min_value = 0
        self._attr_native_max_value = 59
        self._attr_native_step = 1

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return self.entry.entry_id + "_multicooker_cook_minutes"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "") + " Cook Minutes").strip()

    @property
    def icon(self):
        return "mdi:clock-outline"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    @property
    def native_value(self):
        """Return the current cook minutes."""
        status = self.cooker.status
        return status.cook_minutes if status else 0

    async def async_set_native_value(self, value: float) -> None:
        """Set the cook minutes."""
        await self.cooker.set_cook_minutes(int(value))
        self.async_write_ha_state()


class SkyMulticookerStartButton(ButtonEntity):
    """Representation of a SkyCooker multicooker start button."""

    def __init__(self, hass, entry):
        """Initialize the start button."""
        self.hass = hass
        self.entry = entry

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return self.entry.entry_id + "_multicooker_start"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "") + " Start").strip()

    @property
    def icon(self):
        return "mdi:play"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    async def async_press(self, **kwargs):
        """Start the multicooker."""
        await self.cooker.start_cooking()


class SkyMulticookerStopButton(ButtonEntity):
    """Representation of a SkyCooker multicooker stop button."""

    def __init__(self, hass, entry):
        """Initialize the stop button."""
        self.hass = hass
        self.entry = entry

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        return self.entry.entry_id + "_multicooker_stop"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "") + " Stop").strip()

    @property
    def icon(self):
        return "mdi:stop"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.cooker.available

    async def async_press(self, **kwargs):
        """Stop the multicooker."""
        await self.cooker.stop_cooking()