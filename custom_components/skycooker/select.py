"""Сущности выбора SkyCooker."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import *
from .entity_base import SkyCookerEntity
from .utils import (get_base_name, get_localized_string, get_mode_name, get_language_index,
                   get_mode_options, get_temperature_options, get_time_options, get_subprogram_options,
                   should_show_subprogram, find_mode_id, get_mode_data, get_entity_name)

_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка сущностей выбора SkyCooker."""
    entities = [
        SkyCookerSelect(hass, entry, SELECT_TYPE_MODE),
        SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_MINUTES),
    ]
    
    # Добавляем селект для подпрограммы только если модель поддерживает подпрограммы
    skycooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    if should_show_subprogram(skycooker.model_code):
        entities.append(SkyCookerSelect(hass, entry, SELECT_TYPE_SUBPROGRAM))
    
    async_add_entities(entities)


class SkyCookerSelect(SkyCookerEntity, SelectEntity):
    """Представление сущности выбора SkyCooker."""

    def __init__(self, hass, entry, select_type):
        """Инициализация сущности выбора."""
        super().__init__(hass, entry)
        self.select_type = select_type

    @property
    def unique_id(self):
        """Возвращает уникальный идентификатор."""
        return f"{self.entry.entry_id}_{self.select_type}"

    @property
    def name(self):
        """Возвращает имя сущности выбора."""
        if self.select_type == SELECT_TYPE_MODE:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Mode', 'Режим готовки')
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Subprogram', 'Подпрограмма')
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Temperature', 'Температура')
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Cooking time (hours)', 'Время приготовления (часы)')
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Cooking time (minutes)', 'Время приготовления (минуты)')
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Delayed start (hours)', 'Время отложенного старта (часы)')
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Delayed start (minutes)', 'Время отложенного старта (минуты)')
        
        return get_base_name(self.entry)

    @property
    def icon(self):
        """Возвращает иконку."""
        icons = {
            SELECT_TYPE_MODE: "mdi:chef-hat",
            SELECT_TYPE_SUBPROGRAM: "mdi:cog-outline",
            SELECT_TYPE_TEMPERATURE: "mdi:thermometer",
            SELECT_TYPE_COOKING_TIME_HOURS: "mdi:timer",
            SELECT_TYPE_COOKING_TIME_MINUTES: "mdi:timer",
            SELECT_TYPE_DELAYED_START_HOURS: "mdi:timer-sand",
            SELECT_TYPE_DELAYED_START_MINUTES: "mdi:timer-sand",
        }
        return icons.get(self.select_type)

    @property
    def current_option(self):
        """Возвращает текущий выбранный вариант."""
        if self.select_type == SELECT_TYPE_MODE:
            mode_id = self.skycooker.current_mode
            if mode_id is not None:
                return get_mode_name(self.hass, mode_id, self.skycooker.model_code)
            else:
                return None
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            if self.skycooker.status and self.skycooker.status.subprog is not None:
                return str(self.skycooker.status.subprog)
            else:
                return "0"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            if hasattr(self.skycooker, '_target_temperature') and self.skycooker._target_temperature is not None:
                return str(self.skycooker._target_temperature)
            elif self.skycooker.status and self.skycooker.status.target_temp is not None:
                return str(self.skycooker.status.target_temp)
            else:
                return None
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            if self.skycooker.target_main_hours is not None:
                return str(self.skycooker.target_main_hours)
            elif self.skycooker.status and self.skycooker.status.target_main_hours is not None:
                return str(self.skycooker.status.target_main_hours)
            else:
                return "0"
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            if self.skycooker.target_main_minutes is not None:
                return str(self.skycooker.target_main_minutes)
            elif self.skycooker.status and self.skycooker.status.target_main_minutes is not None:
                return str(self.skycooker.status.target_main_minutes)
            else:
                return "0"
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            if hasattr(self.skycooker, '_target_additional_hours'):
                return str(self.skycooker._target_additional_hours)
            elif self.skycooker.status and self.skycooker.status.target_additional_hours is not None:
                return str(self.skycooker.status.target_additional_hours)
            else:
                return "0"
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            if hasattr(self.skycooker, '_target_additional_minutes'):
                return str(self.skycooker._target_additional_minutes)
            elif self.skycooker.status and self.skycooker.status.target_additional_minutes is not None:
                return str(self.skycooker.status.target_additional_minutes)
            else:
                return "0"
        return None

    @property
    def options(self):
        """Возвращает доступные варианты."""
        if self.select_type == SELECT_TYPE_MODE:
            return get_mode_options(self.hass, self.skycooker.model_code)
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            return get_subprogram_options()
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            return get_temperature_options()
        elif self.select_type in [SELECT_TYPE_COOKING_TIME_HOURS, SELECT_TYPE_DELAYED_START_HOURS]:
            return get_time_options(hours=True)
        elif self.select_type in [SELECT_TYPE_COOKING_TIME_MINUTES, SELECT_TYPE_DELAYED_START_MINUTES]:
            return get_time_options(hours=False)
        return []

    async def async_select_option(self, option: str) -> None:
        """Изменение выбранного варианта."""
        if self.select_type == SELECT_TYPE_MODE:
            model_type = self.skycooker.model_code
            if model_type is None:
                return
            
            # Если выбрана пустая строка, не делаем ничего
            if not option or option == "":
                _LOGGER.debug("Выбран пустой режим, очистка целевого режима")
                self.skycooker._target_mode = None
                async_dispatcher_send(self.hass, DISPATCHER_UPDATE)
                self.update()
                return
            
            mode_id = find_mode_id(self.hass, option, model_type)
            if mode_id is None:
                return
            
            mode_data = get_mode_data(model_type, mode_id)
            if mode_data:
                _LOGGER.debug(f"Выбран режим {mode_id} для модели {model_type}: температура={mode_data[0]}, часы={mode_data[1]}, минуты={mode_data[2]}")
                 
                # Всегда обновляем температуру и время приготовления данными режима
                self.skycooker._target_temperature = mode_data[0]
                self.skycooker._target_main_hours = mode_data[1]
                self.skycooker._target_main_minutes = mode_data[2]
            
            self.skycooker._target_mode = mode_id
            async_dispatcher_send(self.hass, DISPATCHER_UPDATE)
            self.update()
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            self.skycooker._target_temperature = int(option)
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            self.skycooker.target_main_hours = int(option)
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            self.skycooker.target_main_minutes = int(option)
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            self.skycooker._target_additional_hours = int(option)
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            self.skycooker._target_additional_minutes = int(option)
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            self.skycooker._target_subprogram = int(option)
        
        # Устанавливаем значения по умолчанию для отложенного запуска, если они не установлены
        if self.select_type in [SELECT_TYPE_DELAYED_START_HOURS, SELECT_TYPE_DELAYED_START_MINUTES]:
            if getattr(self.skycooker, '_target_additional_hours', None) is None:
                self.skycooker._target_additional_hours = 0
            if getattr(self.skycooker, '_target_additional_minutes', None) is None:
                self.skycooker._target_additional_minutes = 0

        # Планируем обновление для обновления состояния сущности
        self.async_schedule_update_ha_state(True)

        # Логируем новые значения для отладки
        _LOGGER.debug(f"Обновлено {self.select_type}: {option}")
        if hasattr(self.skycooker, 'target_main_hours'):
            _LOGGER.debug(f"Текущие target_main_hours: {self.skycooker.target_main_hours}")
        if hasattr(self.skycooker, 'target_main_minutes'):
            _LOGGER.debug(f"Текущие target_main_minutes: {self.skycooker.target_main_minutes}")
        if hasattr(self.skycooker, '_target_additional_hours'):
            _LOGGER.debug(f"Текущие target_additional_hours: {self.skycooker._target_additional_hours}")
        if hasattr(self.skycooker, '_target_additional_minutes'):
            _LOGGER.debug(f"Текущие target_additional_minutes: {self.skycooker._target_additional_minutes}")