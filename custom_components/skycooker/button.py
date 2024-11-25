"""SkyCooker."""
import logging

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import (CONF_FRIENDLY_NAME,
                                 UnitOfTime)
from homeassistant.helpers.dispatcher import (async_dispatcher_connect,
                                              dispatcher_send)
from homeassistant.helpers.entity import EntityCategory

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)

BUTTON_PROGRAM_1 = "program_1"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker entry."""
    model_code = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION].model_code
    if model_code in [SkyCooker.MODELS_4]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
        async_add_entities([
            SkyButton(hass, entry, BUTTON_PROGRAM_1),
        ])


class SkyButton(ButtonEntity):
    """Representation of a SkyCooker number device."""

    def __init__(self, hass, entry, button_type):
        """Initialize the number device."""
        self.hass = hass
        self.entry = entry
        self.button_type = button_type

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
        return f"{self.entry.entry_id}_{self.button_type}"

    @property
    def name(self):
        """Name of the entity."""
        if self.button_type == BUTTON_PROGRAM_1:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + " program 1"

    # todo
    @property
    def icon(self):
        return "mdi:clock-time-four"

    @property
    def device_class(self):
        return ButtonDeviceClass.IDENTIFY

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
        if self.button_type == BUTTON_PROGRAM_1:
            return self.cooker.available

    @property
    def entity_category(self):
        if self.button_type == BUTTON_PROGRAM_1:
            return EntityCategory.CONFIG

    @property
    def native_unit_of_measurement(self):
        return None

    @property
    def native_value(self):
        return None

    async def async_set_native_value(self, value):
        if self.button_type == BUTTON_PROGRAM_1:
            await self.cooker.set_cook_hours(value)
        self.hass.async_add_executor_job(dispatcher_send, self.hass, DISPATCHER_UPDATE)
