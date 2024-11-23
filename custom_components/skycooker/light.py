"""SkyCooker."""
import logging

from homeassistant.components.light import (ATTR_BRIGHTNESS, ATTR_RGB_COLOR,
                                            ColorMode, LightEntity, LightEntityFeature)
from homeassistant.const import CONF_FRIENDLY_NAME, STATE_OFF
from homeassistant.helpers.dispatcher import (async_dispatcher_connect,
                                              dispatcher_send)
from homeassistant.helpers.entity import EntityCategory

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


LIGHT_GAME = "light"


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the SkyCooker entry."""
    model_code = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION].model_code
    if model_code in [SkyCooker.MODELS_4]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
        async_add_entities([
            CookerLight(hass, entry, LIGHT_GAME),
            CookerLight(hass, entry, SkyCooker.LIGHT_BOIL, 0),
            CookerLight(hass, entry, SkyCooker.LIGHT_BOIL, 1),
            CookerLight(hass, entry, SkyCooker.LIGHT_BOIL, 2),
            CookerLight(hass, entry, SkyCooker.LIGHT_LAMP, 0),
            CookerLight(hass, entry, SkyCooker.LIGHT_LAMP, 1),
            CookerLight(hass, entry, SkyCooker.LIGHT_LAMP, 2),
        ])


class CookerLight(LightEntity):
    """Representation of a SkyCooker light device."""

    def __init__(self, hass, entry, light_type, n = 0):
        """Initialize the light device."""
        self.hass = hass
        self.entry = entry
        self.light_type = light_type
        self.n = n
        self.on = False
        self.current = (0xFF, 0xFF, 0xFF, 0xFF)

    async def async_added_to_hass(self):
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        self.schedule_update_ha_state()
        if self.light_type == LIGHT_GAME:
            if (self.cooker.target_mode == SkyCooker.MODE_GAME and
                self.cooker.current_mode == SkyCooker.MODE_GAME):
                if not self.on:
                    self.hass.create_task(self.async_turn_on())
            else:
                self.on = False

    @property
    def cooker(self):
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        if self.light_type == LIGHT_GAME:
            return f"{self.entry.entry_id}_{self.light_type}"
        else:
            return f"{self.entry.entry_id}_{self.light_type}_{self.n+1}"

    @property
    def name(self):
        """Name of the entity."""
        if self.light_type == LIGHT_GAME:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + " light"
        if self.light_type == SkyCooker.LIGHT_BOIL:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + f" temperature #{self.n+1} color"
        if self.light_type == SkyCooker.LIGHT_LAMP:
            return (FRIENDLY_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip() + f" lamp #{self.n+1} color"

    @property
    def icon(self):
        if self.light_type == LIGHT_GAME:
            return None
        if self.light_type == SkyCooker.LIGHT_LAMP:
            return None
        if self.light_type == SkyCooker.LIGHT_BOIL:
            if self.n == 0:
                return "mdi:thermometer-low"
            if self.n == 1:        
                return "mdi:thermometer"        
            if self.n == 2:
                return "mdi:thermometer-high"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][DATA_DEVICE_INFO]()

    @property
    def entity_category(self):
        return None

    @property
    def should_poll(self):
        return False

    @property
    def assumed_state(self):
        return False

    @property
    def available(self):
        if self.light_type == LIGHT_GAME:
            return self.cooker.available
        else:
            return self.cooker.available and self.cooker.get_color(self.light_type, self.n) != None

    @property
    def entity_category(self):
        if self.light_type == LIGHT_GAME:
            return None
        else:
            return EntityCategory.CONFIG

    @property
    def rgb_color(self):
        """Return the rgb color value."""
        if self.light_type == LIGHT_GAME:
            r, g, b, brightness = self.current
            return r, g, b
        else:
            return self.cooker.get_color(self.light_type, self.n)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        if self.light_type == LIGHT_GAME:
            r, g, b, brightness = self.current
            return brightness
        else:
            return self.cooker.get_brightness(self.light_type)

    @property
    def is_on(self):
        """Return true if light is on."""
        if self.light_type == LIGHT_GAME:
            return self.on and self.cooker.target_mode == SkyCooker.MODE_GAME
        else:
            return True # Always on for other modes

    @property
    def supported_features(self):
        """Flag supported features."""
        return LightEntityFeature(0)

    @property
    def color_mode(self):
        """Return the color mode of the light."""
        return ColorMode.RGB

    @property
    def supported_color_modes(self):
        """Flag supported color modes."""
        return {ColorMode.RGB}

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        _LOGGER.warning(f"Turn on ({self.light_type}): {kwargs}")
        if self.light_type == LIGHT_GAME:
            r, g, b, brightness = self.current
            if ATTR_RGB_COLOR in kwargs:
                r, g, b = kwargs[ATTR_RGB_COLOR]
            if ATTR_BRIGHTNESS in kwargs:
                brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.warning(f"Setting {self.light_type} color of the Cooker: r={r}, g={g}, b={b}, brightness={brightness}")
            await self.cooker.set_target_mode(SkyCooker.MODE_NAMES[SkyCooker.MODE_GAME])
            await self.cooker.impulse_color(r, g, b, brightness)
            self.on = True
            self.current = r, g, b, brightness
        else:
            if ATTR_RGB_COLOR in kwargs:
                await self.cooker.set_color(self.light_type, self.n, kwargs[ATTR_RGB_COLOR])
            if ATTR_BRIGHTNESS in kwargs:
                await self.cooker.set_brightness(self.light_type, kwargs[ATTR_BRIGHTNESS])
        self.hass.async_add_executor_job(dispatcher_send, self.hass, DISPATCHER_UPDATE)

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        _LOGGER.warning(f"Turn off ({self.light_type}): {kwargs}")
        if self.light_type == LIGHT_GAME:
            await self.cooker.set_target_mode(STATE_OFF)
            self.on = False
        self.hass.async_add_executor_job(dispatcher_send, self.hass, DISPATCHER_UPDATE)
