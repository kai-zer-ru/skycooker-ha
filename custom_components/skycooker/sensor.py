"""Сенсоры SkyCooker."""

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                                SensorStateClass)
from homeassistant.const import (PERCENTAGE, UnitOfTemperature)
from homeassistant.helpers.entity import EntityCategory

from .const import *
from .entity_base import SkyCookerEntity
from .utils import (get_base_name, get_entity_name)
from .programs import get_current_program_text
from .time import (calculate_remaining_time, get_cooking_time, get_auto_warm_time,
                   get_delayed_launch_time)
from .programs import is_subprogram_supported
from .status import get_status_text


async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка сенсоров SkyCooker."""
    entities = [
        SkyCookerSensor(hass, entry, SENSOR_TYPE_STATUS),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_TEMPERATURE),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_REMAINING_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_COOKING_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_AUTO_WARM_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_SUCCESS_RATE),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_DELAYED_LAUNCH_TIME),
        SkyCookerSensor(hass, entry, SENSOR_TYPE_CURRENT_PROGRAM),
    ]
    
    # Добавляем сенсор для подпрограммы только если модель поддерживает подпрограммы
    skycooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    if is_subprogram_supported(skycooker.model_id):
        entities.append(SkyCookerSensor(hass, entry, SENSOR_TYPE_SUBPROGRAM))
    
    async_add_entities(entities)


class SkyCookerSensor(SkyCookerEntity, SensorEntity):
    """Представление сенсора SkyCooker."""

    def __init__(self, hass, entry, sensor_type):
        """Инициализация сенсора."""
        super().__init__(hass, entry)
        self.sensor_type = sensor_type

    @property
    def unique_id(self):
        """Возвращает уникальный идентификатор."""
        return f"{self.entry.entry_id}_{self.sensor_type}"

    @property
    def last_reset(self):
        """Возвращает последний сброс."""
        return None

    @property
    def name(self):
        """Возвращает имя сенсора."""
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Status', 'Статус')
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Temperature', 'Температура')
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Remaining time', 'Оставшееся время')
        elif self.sensor_type == SENSOR_TYPE_COOKING_TIME:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Cooking time', 'Время приготовления')
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Auto warm time', 'Время автоподогрева')
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Success rate', 'Процент успеха')
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Delayed launch time', 'Время до отложенного запуска')
        elif self.sensor_type == SENSOR_TYPE_CURRENT_PROGRAM:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Current mode', 'Текущий режим')
        elif self.sensor_type == SENSOR_TYPE_SUBPROGRAM:
            return get_entity_name(self.hass, self.entry, self.sensor_type, 'Current subprogram', 'Текущая подпрограмма')

        return get_base_name(self.entry)

    @property
    def icon(self):
        """Возвращает иконку."""
        icons = {
            SENSOR_TYPE_STATUS: "mdi:information",
            SENSOR_TYPE_TEMPERATURE: "mdi:thermometer",
            SENSOR_TYPE_REMAINING_TIME: "mdi:timer",
            SENSOR_TYPE_COOKING_TIME: "mdi:clock",
            SENSOR_TYPE_AUTO_WARM_TIME: "mdi:clock-start",
            SENSOR_TYPE_SUCCESS_RATE: "mdi:bluetooth-connect",
            SENSOR_TYPE_DELAYED_LAUNCH_TIME: "mdi:timer-sand",
            SENSOR_TYPE_CURRENT_PROGRAM: "mdi:chef-hat",
            SENSOR_TYPE_SUBPROGRAM: "mdi:cog-outline",
        }
        return icons.get(self.sensor_type)

    @property
    def entity_category(self):
        """Возвращает категорию сущности."""
        if self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def device_class(self):
        """Возвращает класс устройства."""
        return SensorDeviceClass.TEMPERATURE if self.sensor_type == SENSOR_TYPE_TEMPERATURE else None

    @property
    def state_class(self):
        """Возвращает класс состояния."""
        if self.sensor_type in [SENSOR_TYPE_TEMPERATURE, SENSOR_TYPE_SUCCESS_RATE]:
            return SensorStateClass.MEASUREMENT
        return None

    @property
    def native_unit_of_measurement(self):
        """Возвращает единицу измерения."""
        if self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return PERCENTAGE
        return None

    @property
    def available(self):
        """Возвращает доступность сенсора."""
        if not self.skycooker.available:
            return False

        # Для датчиков успеха и времени отложенного запуска всегда возвращаем True
        if self.sensor_type in [SENSOR_TYPE_SUCCESS_RATE, SENSOR_TYPE_DELAYED_LAUNCH_TIME]:
            return True
        
        # Для датчика подпрограммы проверяем, есть ли данные о подпрограмме
        if self.sensor_type == SENSOR_TYPE_SUBPROGRAM:
            return self.skycooker.status and self.skycooker.status.subprogram_id is not None
        
        # Для других датчиков проверяем, есть ли данные из статуса устройства
        if self.sensor_type == SENSOR_TYPE_STATUS:
            return self.skycooker.status_code is not None
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            # Сенсор температуры всегда доступен, даже если target_temp is None
            return True
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return (self.skycooker.status_code is not None and
                    hasattr(self.skycooker, 'target_main_hours') and
                    hasattr(self.skycooker, 'target_main_minutes') and
                    hasattr(self.skycooker, 'target_additional_hours') and
                    hasattr(self.skycooker, 'target_additional_minutes'))
        elif self.sensor_type == SENSOR_TYPE_COOKING_TIME:
            return hasattr(self.skycooker, 'target_main_hours') and hasattr(self.skycooker, 'target_main_minutes')
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return self.skycooker.status_code is not None and hasattr(self.skycooker, 'target_additional_hours') and hasattr(self.skycooker, 'target_additional_minutes')
        elif self.sensor_type == SENSOR_TYPE_CURRENT_PROGRAM:
            return self.skycooker.status_code is not None

        return False

    @property
    def native_value(self):
        """Возвращает состояние сенсора."""
        if self.sensor_type == SENSOR_TYPE_STATUS:
            status = self.skycooker.status
            if status and hasattr(status, 'status'):
                return get_status_text(self.hass, status.status)
            return get_status_text(self.hass, None)
        elif self.sensor_type == SENSOR_TYPE_TEMPERATURE:
            return 0 if self.skycooker.status_code == STATUS_OFF else (self.skycooker.target_temperature if self.skycooker.target_temperature is not None else 0)
        elif self.sensor_type == SENSOR_TYPE_REMAINING_TIME:
            return calculate_remaining_time(self.hass, self.skycooker, self.skycooker.status_code)
        elif self.sensor_type == SENSOR_TYPE_COOKING_TIME:
            return get_cooking_time(self.hass, self.skycooker, self.skycooker.status_code)
        elif self.sensor_type == SENSOR_TYPE_AUTO_WARM_TIME:
            return get_auto_warm_time(self.hass, self.skycooker, self.skycooker.status_code)
        elif self.sensor_type == SENSOR_TYPE_SUCCESS_RATE:
            return self.skycooker.success_rate if self.skycooker.success_rate is not None else 0
        elif self.sensor_type == SENSOR_TYPE_DELAYED_LAUNCH_TIME:
            return get_delayed_launch_time(self.hass, self.skycooker, self.skycooker.status_code)
        elif self.sensor_type == SENSOR_TYPE_CURRENT_PROGRAM:
            return get_current_program_text(self.hass, self.skycooker, self.skycooker.status_code)
        elif self.sensor_type == SENSOR_TYPE_SUBPROGRAM:
            return str(self.skycooker.status.subprogram_id) if self.skycooker.status and self.skycooker.status.subprogram_id is not None else "0"
        
        return None