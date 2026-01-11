"""SkyCooker switches."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import *




async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker switches."""
    async_add_entities([
        SkyCookerSwitch(hass, entry, SWITCH_TYPE_AUTO_WARM),
    ])


class SkyCookerSwitch(SwitchEntity):
    """Representation of a SkyCooker switch."""

    def __init__(self, hass, entry, switch_type):
        """Initialize the switch."""
        self.hass = hass
        self.entry = entry
        self.switch_type = switch_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the switch."""
        self.schedule_update_ha_state()

    @property
    def skycooker(self):
        """Get the skycooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.switch_type}"

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
    def name(self):
        """Return the name of the switch."""
        base_name = (SKYCOOKER_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()

        # Определяем индекс языка (0 для английского, 1 для русского)
        language = self.hass.config.language
        is_russian = language == "ru"

        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            return f"{base_name} {'Автоподогрев' if is_russian else 'Auto warm'}"

        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            return "mdi:heat-wave"
        return None

    @property
    def available(self):
        """Return if switch is available."""
        return self.skycooker.available

    @property
    def is_on(self):
        """Return true if switch is on."""
        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            # Используем только значение, установленное пользователем
            return getattr(self.skycooker, '_auto_warm_enabled', False)
        return False

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            # Устанавливаем флаг автоподогрева без отправки команд на устройство
            self.skycooker._auto_warm_enabled = True
            self.update()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if self.switch_type == SWITCH_TYPE_AUTO_WARM:
            # Сбрасываем флаг автоподогрева без отправки команд на устройство
            self.skycooker._auto_warm_enabled = False
            self.update()