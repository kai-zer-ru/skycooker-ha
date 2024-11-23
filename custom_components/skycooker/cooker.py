"""SkyCooker."""
import logging

from homeassistant.components.water_heater import (WaterHeaterEntity,
                                                   WaterHeaterEntityFeature,
                                                   ATTR_OPERATION_MODE)
from homeassistant.const import (ATTR_SW_VERSION, ATTR_TEMPERATURE,
                                 CONF_FRIENDLY_NAME, CONF_SCAN_INTERVAL,
                                 STATE_OFF, UnitOfTemperature)
from homeassistant.helpers.dispatcher import (async_dispatcher_connect,
                                              dispatcher_send)

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the SkyCooker entry."""
    async_add_entities([SkyWaterHeater(hass, entry)])


class SkyWaterHeater(WaterHeaterEntity):
    """Representation of a SkyCooker water_heater device."""

    def __init__(self, hass, entry):
        """Initialize the water_heater device."""
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
        return self.entry.entry_id + "_cooker"

    @property
    def name(self):
        """Name of the entity."""
        return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()

    @property
    def icon(self):
        return "mdi:kettle"

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
    def supported_features(self):
        return (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
            | WaterHeaterEntityFeature.ON_OFF
        )

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def min_temp(self):
        return ROOM_TEMP

    @property
    def max_temp(self):
        return BOIL_TEMP

    @property
    def operation_list(self):
        if self.cooker.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            return [
                STATE_OFF,
                SkyCooker.MODE_NAMES[SkyCooker.MODE_HEAT],
                SkyCooker.MODE_NAMES[SkyCooker.MODE_BOIL],
                SkyCooker.MODE_NAMES[SkyCooker.MODE_BOIL_HEAT],
                SkyCooker.MODE_NAMES[SkyCooker.MODE_LAMP],
                SkyCooker.MODE_NAMES[SkyCooker.MODE_GAME]
            ]
        else:
            return [
                STATE_OFF,
                SkyCooker.MODE_NAMES[SkyCooker.MODE_HEAT],
                SkyCooker.MODE_NAMES[SkyCooker.MODE_BOIL],
                SkyCooker.MODE_NAMES[SkyCooker.MODE_BOIL_HEAT]
            ]

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
        data = {
            "target_temp_step": 5,
            "connected": self.cooker.connected,
            "auth_ok": self.cooker.auth_ok,
            "sw_version": sw_version,
            "success_rate": self.cooker.success_rate,
            "persistent_connection": self.cooker.persistent,
            "poll_interval": self.entry.data.get(CONF_SCAN_INTERVAL, 0),
            "ontime_seconds": self.cooker.ontime.total_seconds() if self.cooker.ontime else None,
            "ontime_string": str(self.cooker.ontime),
            "energy_wh": self.cooker.energy_wh,
            "heater_on_count": self.cooker.heater_on_count,
            "user_on_count": self.cooker.user_on_count,
            "sound_enabled": self.cooker.sound_enabled,
            "color_interval": self.cooker.cook_hours,
            "boil_time": self.cooker.cook_minutes,
            "water_freshness_hours": self.cooker.water_freshness_hours,
            "lamp_auto_off_hours": self.cooker.wait_hours,
            "boil_light": self.cooker.light_switch_boil,
            "sync_light": self.cooker.light_switch_sync,
            "parental_control": self.cooker.parental_control,
            "error_code": self.cooker.error_code,
        }
        return data

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        _LOGGER.warning(f"TargetMode: {self.cooker.target_mode != None}")
        return self.cooker.target_mode != None

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.cooker.set_target_mode(SkyCooker.MODE_NAMES[SkyCooker.MODE_BOIL])

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.cooker.set_target_mode(None)

    @property
    def current_temperature(self):
        return self.cooker.current_temp

    @property
    def target_temperature(self):
        return self.cooker.target_temp

    @property
    def current_operation(self):
        return self.cooker.target_mode_str

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        target_temperature = kwargs.get(ATTR_TEMPERATURE)
        operation_mode = kwargs.get(ATTR_OPERATION_MODE)
        await self.cooker.set_target_temp(target_temperature, operation_mode)
        self.hass.async_add_executor_job(dispatcher_send, self.hass, DISPATCHER_UPDATE)

    async def async_set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        await self.cooker.set_target_mode(operation_mode)
        self.hass.async_add_executor_job(dispatcher_send, self.hass, DISPATCHER_UPDATE)
