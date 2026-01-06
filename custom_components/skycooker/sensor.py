"""SkyCoocker sensors."""
import logging

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                              SensorStateClass)
from homeassistant.const import (CONF_FRIENDLY_NAME, PERCENTAGE, UnitOfTemperature,
                                  UnitOfTime)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory

from .const import *

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPE_STATUS = "status"
SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_REMAINING_TIME = "remaining_time"
SENSOR_TYPE_TOTAL_TIME = "total_time"
SENSOR_TYPE_AUTO_WARM_TIME = "auto_warm_time"
SENSOR_TYPE_SUCCESS_RATE = "success_rate"
SENSOR_TYPE_DELAYED_LAUNCH_TIME = "delayed_launch_time"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCoocker sensors."""
    async_add_entities([
        SkyCoockerSensor(hass, entry, SENSOR_TYPE_STATUS),
        SkyCoockerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE),
        SkyCoockerSensor(hass, entry, SENSOR_TYPE_REMAINING_TIME),
        SkyCoockerSensor(hass, entry, SENSOR_TYPE_TOTAL_TIME),
        SkyCoockerSensor(hass, entry, SENSOR_TYPE_AUTO_WARM_TIME),
        SkyCoockerSensor(hass, entry, SENSOR_TYPE_SUCCESS_RATE),
        SkyCoockerSensor(hass, entry, SENSOR_TYPE_DELAYED_LAUNCH_TIME),
    ])


class SkyCoockerSensor(SensorEntity):
    """Representation of a SkyCoocker sensor."""

    def __init__(self, hass, entry, sensor_type):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self.sensor_type = sensor_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the sensor."""
        self.schedule_update_ha_state()

    @property
    def multicooker(self):
        """Get the multicooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.sensor_type}"

    @property
    def device_info(self):
        """Return device info."""
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def assumed_state(self):
        """Return true if unable to access real state of the entity."""
        return False

    @property
    def last_reset(self):
        """Return last reset."""
        return None

    @property
    def name(self):
        """Return the name of the sensor."""
        base_name = (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()
        
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return f"{base_name} статус"
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return f"{base_name} температура"
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return f"{base_name} оставшееся время"
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return f"{base_name} общее время"
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return f"{base_name} время автоподогрева"
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return f"{base_name} процент успеха"
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            return f"{base_name} время до отложенного запуска"
        
        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return "mdi:information"
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return "mdi:thermometer"
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return "mdi:timer"
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return "mdi:clock"
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return "mdi:clock-start"
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return "mdi:bluetooth-connect"
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            return "mdi:timer-sand"
        return None

    @property
    def available(self):
        """Return if sensor is available."""
        if not self.multicooker.available:
            return False
         
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return self.multicooker.status_code is not None
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return self.multicooker.current_temperature is not None
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return self.multicooker.remaining_time is not None
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return self.multicooker.total_time is not None
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return self.multicooker.auto_warm_enabled is not None
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return True
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            # Always available, returns 0 when not in delayed launch mode
            return True
         
        return False

    @property
    def entity_category(self):
        """Return entity category."""
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def device_class(self):
        """Return device class."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return SensorDeviceClass.TEMPERATURE
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_TOTAL_TIME, 
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return SensorDeviceClass.DURATION
        return None

    @property
    def state_class(self):
        """Return state class."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return SensorStateClass.MEASUREMENT
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_TOTAL_TIME, 
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return SensorStateClass.MEASUREMENT
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return SensorStateClass.MEASUREMENT
        return None

    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_TOTAL_TIME, 
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return UnitOfTime.MINUTES
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return PERCENTAGE
        return None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.sensor_type == SENSOR_TYPE_STATUS:
            status_code = self.multicooker.status_code
            # Get status text from model-specific constants
            if self.multicooker.model and self.multicooker.model in SUPPORTED_MODELS:
                status_text = SUPPORTED_MODELS[self.multicooker.model]["status_codes"].get(status_code)
                if status_text:
                    return status_text
            return STATUS_CODES.get(status_code, f"Неизвестно ({status_code})")
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return self.multicooker.current_temperature
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return self.multicooker.remaining_time
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return self.multicooker.total_time
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            status_code = self.multicooker.status_code
            # Use model-specific status code for auto warm
            auto_warm_code = None
            if self.multicooker.model and self.multicooker.model in SUPPORTED_MODELS:
                # Find the auto warm status code for this model
                for code, text in SUPPORTED_MODELS[self.multicooker.model]["status_codes"].items():
                    if "авто" in text.lower() or "warm" in text.lower():
                        auto_warm_code = code
                        break
            return self.multicooker.remaining_time if status_code == (auto_warm_code or STATUS_AUTO_WARM) else 0
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return self.multicooker.success_rate
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            status_code = self.multicooker.status_code
            # Use model-specific status code for delayed launch
            delayed_launch_code = None
            if self.multicooker.model and self.multicooker.model in SUPPORTED_MODELS:
                # Find the delayed launch status code for this model
                for code, text in SUPPORTED_MODELS[self.multicooker.model]["status_codes"].items():
                    if "отложен" in text.lower() or "delayed" in text.lower():
                        delayed_launch_code = code
                        break
            return self.multicooker.remaining_time if status_code == (delayed_launch_code or STATUS_DELAYED_LAUNCH) else 0
        
        return None