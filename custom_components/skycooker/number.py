"""SkyCooker."""
import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import (CONF_FRIENDLY_NAME,
                                 UnitOfTime)
from homeassistant.helpers.dispatcher import (async_dispatcher_connect,
                                              dispatcher_send)
from homeassistant.helpers.entity import EntityCategory

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)

NUMBER_COOK_HOURS = "cook_hours"
NUMBER_WAIT_HOURS = "wait_hours"
NUMBER_COOK_MINUTES = "cook_minutes"
NUMBER_WAIT_MINUTES = "wait_minutes"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker entry."""
    model_code = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION].model_code
    if model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
        async_add_entities([
            SkyNumber(hass, entry, NUMBER_COOK_HOURS),
            SkyNumber(hass, entry, NUMBER_COOK_MINUTES),
            SkyNumber(hass, entry, NUMBER_WAIT_HOURS),
            SkyNumber(hass, entry, NUMBER_WAIT_MINUTES),
        ])


class SkyNumber(NumberEntity):
    """Representation of a SkyCooker number device."""

    def __init__(self, hass, entry, number_type):
        """Initialize the number device."""
        self.hass = hass
        self.entry = entry
        self.number_type = number_type

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
        return f"{self.entry.entry_id}_{self.number_type}"

    @property
    def name(self):
        """Name of the entity."""
        if self.number_type == NUMBER_COOK_HOURS:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + " hours"
        if self.number_type == NUMBER_COOK_MINUTES:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + " minutes"
        if self.number_type == NUMBER_WAIT_HOURS:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + " wait hours"
        if self.number_type == NUMBER_WAIT_MINUTES:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + " wait minutes"
    # todo
    @property
    def icon(self):
        return "mdi:clock-time-four"

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
        return True

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def native_unit_of_measurement(self):
        if self.number_type == NUMBER_COOK_HOURS:
            return UnitOfTime.HOURS
        if self.number_type == NUMBER_COOK_MINUTES:
            return UnitOfTime.MINUTES
        if self.number_type == NUMBER_WAIT_HOURS:
            return UnitOfTime.HOURS
        if self.number_type == NUMBER_WAIT_MINUTES:
            return UnitOfTime.MINUTES

    @property
    def native_value(self):
        if self.number_type == NUMBER_COOK_MINUTES:
            return self.cooker.cook_minutes
        if self.number_type == NUMBER_COOK_HOURS:
            return self.cooker.cook_hours
        if self.number_type == NUMBER_WAIT_MINUTES:
            return self.cooker.wait_minutes
        if self.number_type == NUMBER_WAIT_HOURS:
            return self.cooker.wait_hours

    @property
    def native_min_value(self):
        return 0

    @property
    def native_max_value(self):
        if self.number_type == NUMBER_COOK_HOURS:
            return 23
        if self.number_type == NUMBER_COOK_MINUTES:
            return 59
        if self.number_type == NUMBER_WAIT_HOURS:
            return 23
        if self.number_type == NUMBER_WAIT_MINUTES:
            return 59

    @property
    def native_step(self):
        return 1

    @property
    def mode(self):
        return NumberMode.BOX

    async def async_set_native_value(self, value):
        if self.number_type == NUMBER_COOK_HOURS:
            await self.cooker.set_cook_hours(value)
        if self.number_type == NUMBER_COOK_MINUTES:
            await self.cooker.set_cook_minutes(value)
        if self.number_type == NUMBER_WAIT_HOURS:
            await self.cooker.set_wait_hours(value)
        if self.number_type == NUMBER_COOK_MINUTES:
            await self.cooker.set_wait_minutes(value)
        self.hass.async_add_executor_job(dispatcher_send, self.hass, DISPATCHER_UPDATE)
