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
        SkyCookerSensor(hass, entry, SENSOR_TYPE_COOKING_TIME),
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
        elif self.sensor_type == SENSOR_TYPE_COOKING_TIME:
            return f"{base_name} {'Время приготовления' if is_russian else 'Cooking time'}"
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
        elif self.sensor_type == SENSOR_TYPE_COOKING_TIME:
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
            # Проверяем наличие статуса и времени для расчета оставшегося времени
            return (self.skycooker.status_code is not None and
                    hasattr(self.skycooker, 'target_main_hours') and
                    hasattr(self.skycooker, 'target_main_minutes') and
                    hasattr(self.skycooker, 'target_additional_hours') and
                    hasattr(self.skycooker, 'target_additional_minutes'))
        elif self.sensor_type == SENSOR_TYPE_COOKING_TIME:
            # Проверяем наличие target_main_hours и target_main_minutes
            return (hasattr(self.skycooker, 'target_main_hours') and
                    hasattr(self.skycooker, 'target_main_minutes'))
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            # Проверяем наличие статуса для автоподогрева
            return (self.skycooker.status_code is not None and
                    hasattr(self.skycooker, 'target_additional_hours') and
                    hasattr(self.skycooker, 'target_additional_minutes'))
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
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_COOKING_TIME,
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return None
        return None

    @property
    def state_class(self):
        """Return state class."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return SensorStateClass.MEASUREMENT
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return SensorStateClass.MEASUREMENT
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_COOKING_TIME,
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return None
        return None

    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        elif self.sensor_type in [SENSOR_TYPE_REMAINING_TIME, SENSOR_TYPE_COOKING_TIME,
                                  SENSOR_TYPE_AUTO_WARM_TIME, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return None
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
            status_code = self.skycooker.status_code
            if status_code == STATUS_DELAYED_LAUNCH:
                # Для отложенного запуска: target_main + target_additional
                # Используем значения из статуса устройства, если они доступны
                from .skycooker import SkyCooker
                if (self.skycooker.status and
                    isinstance(self.skycooker.status, SkyCooker.Status) and
                    hasattr(self.skycooker.status, 'target_main_hours') and
                    hasattr(self.skycooker.status, 'target_main_minutes') and
                    hasattr(self.skycooker.status, 'target_additional_hours') and
                    hasattr(self.skycooker.status, 'target_additional_minutes')):
                    boil_hours = self.skycooker.status.target_main_hours
                    boil_minutes = self.skycooker.status.target_main_minutes
                    additional_hours = self.skycooker.status.target_additional_hours
                    additional_minutes = self.skycooker.status.target_additional_minutes
                else:
                    # Если значения из статуса недоступны, используем значения из соединения
                    boil_hours = self.skycooker.target_main_hours if hasattr(self.skycooker, 'target_main_hours') and self.skycooker.target_main_hours is not None else 0
                    boil_minutes = self.skycooker.target_main_minutes if hasattr(self.skycooker, 'target_main_minutes') and self.skycooker.target_main_minutes is not None else 0
                    additional_hours = self.skycooker.target_additional_hours if hasattr(self.skycooker, 'target_additional_hours') and self.skycooker.target_additional_hours is not None else 0
                    additional_minutes = self.skycooker.target_additional_minutes if hasattr(self.skycooker, 'target_additional_minutes') and self.skycooker.target_additional_minutes is not None else 0
                total_hours = boil_hours + additional_hours
                total_minutes = boil_minutes + additional_minutes
                # Нормализуем минуты
                if total_minutes >= 60:
                    total_hours += 1
                    total_minutes -= 60
            elif status_code in [STATUS_WARMING, STATUS_COOKING]:
                # Для разогрева и готовки: только target_additional
                # Используем значения из статуса устройства, если они доступны
                from .skycooker import SkyCooker
                if (self.skycooker.status and
                    isinstance(self.skycooker.status, SkyCooker.Status) and
                    hasattr(self.skycooker.status, 'target_additional_hours') and
                    hasattr(self.skycooker.status, 'target_additional_minutes')):
                    additional_hours = self.skycooker.status.target_additional_hours
                    additional_minutes = self.skycooker.status.target_additional_minutes
                else:
                    # Если значения из статуса недоступны, используем значения из соединения
                    additional_hours = self.skycooker.target_additional_hours if hasattr(self.skycooker, 'target_additional_hours') and self.skycooker.target_additional_hours is not None else 0
                    additional_minutes = self.skycooker.target_additional_minutes if hasattr(self.skycooker, 'target_additional_minutes') and self.skycooker.target_additional_minutes is not None else 0
                total_hours = additional_hours
                total_minutes = additional_minutes
            else:
                total_hours = 0
                total_minutes = 0
                   
            if total_hours > 0 or total_minutes > 0:
                if self.hass.config.language == "ru":
                    return f"{total_hours} ч. {total_minutes} м."
                else:
                    return f"{total_hours} h. {total_minutes} m."
            else:
                if self.hass.config.language == "ru":
                    return "0 ч. 0 м."
                else:
                    return "0 h. 0 m."
        elif self.sensor_type == SENSOR_TYPE_COOKING_TIME:
            # Время приготовления: не должно меняться со временем, только при смене статуса
            status_code = self.skycooker.status_code
            if status_code in [STATUS_DELAYED_LAUNCH, STATUS_WARMING, STATUS_COOKING]:
                # Используем значения из статуса устройства, если они доступны
                # Проверяем, что status является реальным объектом Status, а не MagicMock
                from .skycooker import SkyCooker
                if (self.skycooker.status and
                    isinstance(self.skycooker.status, SkyCooker.Status) and
                    hasattr(self.skycooker.status, 'target_main_hours') and
                    hasattr(self.skycooker.status, 'target_main_minutes')):
                    boil_hours = self.skycooker.status.target_main_hours
                    boil_minutes = self.skycooker.status.target_main_minutes
                else:
                    # Если значения из статуса недоступны, используем значения из соединения
                    boil_hours = self.skycooker.target_main_hours if hasattr(self.skycooker, 'target_main_hours') and self.skycooker.target_main_hours is not None else 0
                    boil_minutes = self.skycooker.target_main_minutes if hasattr(self.skycooker, 'target_main_minutes') and self.skycooker.target_main_minutes is not None else 0
                if self.hass.config.language == "ru":
                    return f"{boil_hours} ч. {boil_minutes} м."
                else:
                    return f"{boil_hours} h. {boil_minutes} m."
            else:
                if self.hass.config.language == "ru":
                    return "0 ч. 0 м."
                else:
                    return "0 h. 0 m."
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            # Время автоподогрева: только при статусе STATUS_AUTO_WARM
            status_code = self.skycooker.status_code
            if status_code == STATUS_AUTO_WARM:
                # Используем target_additional_hours и target_additional_minutes
                # Используем значения из статуса устройства, если они доступны
                from .skycooker import SkyCooker
                if (self.skycooker.status and
                    isinstance(self.skycooker.status, SkyCooker.Status) and
                    hasattr(self.skycooker.status, 'target_additional_hours') and
                    hasattr(self.skycooker.status, 'target_additional_minutes')):
                    additional_hours = self.skycooker.status.target_additional_hours
                    additional_minutes = self.skycooker.status.target_additional_minutes
                else:
                    # Если значения из статуса недоступны, используем значения из соединения
                    additional_hours = self.skycooker.target_additional_hours if hasattr(self.skycooker, 'target_additional_hours') and self.skycooker.target_additional_hours is not None else 0
                    additional_minutes = self.skycooker.target_additional_minutes if hasattr(self.skycooker, 'target_additional_minutes') and self.skycooker.target_additional_minutes is not None else 0
                if self.hass.config.language == "ru":
                    return f"{additional_hours} ч. {additional_minutes} м."
                else:
                    return f"{additional_hours} h. {additional_minutes} m."
            else:
                if self.hass.config.language == "ru":
                    return "0 ч. 0 м."
                else:
                    return "0 h. 0 m."
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return self.skycooker.success_rate if self.skycooker.success_rate is not None else 0
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            # Время до отложенного старта: только при статусе STATUS_DELAYED_LAUNCH
            status_code = self.skycooker.status_code
            if status_code == STATUS_DELAYED_LAUNCH:
                # Используем target_additional_hours и target_additional_minutes
                # Используем значения из статуса устройства, если они доступны
                from .skycooker import SkyCooker
                if (self.skycooker.status and
                    isinstance(self.skycooker.status, SkyCooker.Status) and
                    hasattr(self.skycooker.status, 'target_additional_hours') and
                    hasattr(self.skycooker.status, 'target_additional_minutes')):
                    additional_hours = self.skycooker.status.target_additional_hours
                    additional_minutes = self.skycooker.status.target_additional_minutes
                else:
                    # Если значения из статуса недоступны, используем значения из соединения
                    additional_hours = self.skycooker.target_additional_hours if hasattr(self.skycooker, 'target_additional_hours') and self.skycooker.target_additional_hours is not None else 0
                    additional_minutes = self.skycooker.target_additional_minutes if hasattr(self.skycooker, 'target_additional_minutes') and self.skycooker.target_additional_minutes is not None else 0
                if self.hass.config.language == "ru":
                    return f"{additional_hours} ч. {additional_minutes} м."
                else:
                    return f"{additional_hours} h. {additional_minutes} m."
            else:
                if self.hass.config.language == "ru":
                    return "0 ч. 0 м."
                else:
                    return "0 h. 0 m."
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