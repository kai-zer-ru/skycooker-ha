"""Support for SkyCooker."""

import logging
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    hass.states.async_set(DOMAIN+".world", "Paulus")

    # Return boolean to indicate that initialization was successful.
    return True