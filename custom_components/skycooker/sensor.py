"""SkyCooker sensors."""
from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                              SensorStateClass)
from homeassistant.const import (CONF_FRIENDLY_NAME, PERCENTAGE, UnitOfTemperature,
                                   UnitOfTime)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory

from .const import *




async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker sensors."""
    entities = [
        SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_REMAINING_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_TOTAL_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_AUTO_WARM_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_SUCCESS_RATE),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_DELAYED_LAUNCH_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_CURRENT_MODE),
    ]
    
    # Добавляем сенсор для подпрограммы только если модель не MODEL_3
    skycooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    if skycooker.model_code != MODEL_3:
        entities.append(SkyCookerSensor(hass, entry, SENSOR_TYPE_SUBPROGRAM))
    
    async_add_entities(entities)


class SkyCookerSensor(SensorEntity):
    """Representation of a SkyCooker sensor."""

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
    def skycooker(self):
        """Get the skycooker connection."""
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
        base_name = (SKYCOOKER_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()

        # Определяем индекс языка (0 для английского, 1 для русского)
        language = self.hass.config.language
        is_russian = language == "ru"

        if self.sensor_type == SENSOR_TYPE_STATUS:
            return f"{base_name} {'Статус' if is_russian else 'Status'}"
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return f"{base_name} {'Температура' if is_russian else 'Temperature'}"
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return f"{base_name} {'Оставшееся время' if is_russian else 'Remaining time'}"
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return f"{base_name} {'Общее время' if is_russian else 'Total time'}"
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return f"{base_name} {'Время автоподогрева' if is_russian else 'Auto warm time'}"
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return f"{base_name} {'Процент успеха' if is_russian else 'Success rate'}"
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            return f"{base_name} {'Время до отложенного запуска' if is_russian else 'Delayed launch time'}"
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            return f"{base_name} {'Текущий режим' if is_russian else 'Current mode'}"
        elif self.sensor_type == SENSOR_TYPE_SUBPROGRAM:
            return f"{base_name} {'Текущая подпрограмма' if is_russian else 'Current subprogram'}"

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
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            return "mdi:chef-hat"
        elif self.sensor_type == SENSOR_TYPE_SUBPROGRAM:
            return "mdi:cog-outline"
        return None

    @property
    def available(self):
        """Return if sensor is available."""
        # Если skycooker недоступен, возвращаем False
        if not self.skycooker.available:
            return False

        # Для датчиков успеха, времени отложенного запуска и версии ПО всегда возвращаем True, если skycooker доступен
        if self.sensor_type in [SENSOR_TYPE_SUCCESS_RATE, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return True
           
        # Для датчика подпрограммы проверяем, есть ли данные о подпрограмме
        if self.sensor_type == SENSOR_TYPE_SUBPROGRAM:
            return self.skycooker.status and self.skycooker.status.subprog is not None
           
        # Для других датчиков проверяем, есть ли данные из статуса устройства
        # Датчики должны использовать только данные из статуса устройства, а не из пользовательских настроек
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return self.skycooker.status_code is not None
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return self.skycooker.target_temp is not None
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return self.skycooker.remaining_time is not None
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return self.skycooker.total_time is not None
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return self.skycooker.auto_warm_enabled is not None
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            # For current mode, we should return True if we have a status code
            # even if current_mode is None, as we can show "Standby Mode" or "Режим ожидания"
            return self.skycooker.status_code is not None

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
            # Получаем статус из self._status.status
            status = self.skycooker.status
            if status and hasattr(status, 'status'):
                status_code = status.status
                # Определяем индекс языка (0 для английского, 1 для русского)
                language = self.hass.config.language
                lang_index = 0 if language == "en" else 1
                return STATUS_CODES[lang_index].get(status_code, f"Unknown ({status_code})" if lang_index == 0 else f"Неизвестно ({status_code})")
            return "Unknown" if self.hass.config.language == "en" else "Неизвестно"
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            status_code = self.skycooker.status_code
            if status_code == STATUS_OFF:
                return 0
            return self.skycooker.target_temp if self.skycooker.target_temp is not None else 0
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return self.skycooker.remaining_time if self.skycooker.remaining_time is not None else 0
        elif self.sensor_type == SENSOR_TYPE_TOTAL_TIME:
            return self.skycooker.total_time if self.skycooker.total_time is not None else 0
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            status_code = self.skycooker.status_code
            if status_code is not None:
                return self.skycooker.remaining_time if status_code == STATUS_AUTO_WARM else 0
            return 0
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return self.skycooker.success_rate if self.skycooker.success_rate is not None else 0
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            # Возвращаем время отложенного запуска, если оно установлено, независимо от текущего статуса
            if self.skycooker.status_code is not None:
                # Проверяем, есть ли установленное время отложенного запуска
                delayed_time = self.skycooker.delayed_start_time
                # Если delayed_time не является callable (mock-объект) и не равен None, возвращаем его
                if delayed_time is not None and not callable(delayed_time):
                    return delayed_time
            return 0
        elif self.sensor_type == SENSOR_TYPE_CURRENT_MODE:
            status_code = self.skycooker.status_code
            if status_code == STATUS_OFF:
                return "Режим ожидания" if self.hass.config.language == "ru" else "Standby Mode"
            current_mode = self.skycooker.current_mode
            if current_mode is not None:
                # Получаем тип модели из соединения
                model_type = self.skycooker.model_code
                if model_type is None:
                    return f"Unknown ({current_mode})"

                # Получаем названия режимов для текущей модели
                mode_constants = MODE_NAMES.get(model_type, [])
                if not mode_constants or current_mode >= len(mode_constants):
                    return f"Unknown ({current_mode})"

                # Определяем индекс языка (0 для английского, 1 для русского)
                language = self.hass.config.language
                lang_index = 0 if language == "en" else 1

                # Получаем название режима из константы
                mode_constant = mode_constants[current_mode]
                if mode_constant and len(mode_constant) > lang_index:
                    # Проверяем, является ли режим MODE_NONE
                    if mode_constant == MODE_NONE:
                        return f"Unknown ({current_mode})"
                    return mode_constant[lang_index]
                return f"Unknown ({current_mode})"
            return "Режим ожидания" if self.hass.config.language == "ru" else "Standby Mode"
        elif self.sensor_type == SENSOR_TYPE_SUBPROGRAM:
            # Возвращаем текущую подпрограмму из статуса устройства
            if self.skycooker.status and self.skycooker.status.subprog is not None:
                return str(self.skycooker.status.subprog)
            return "0"
          
        return None