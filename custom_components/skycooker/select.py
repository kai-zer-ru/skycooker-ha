"""SkyCooker select entities."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SkyCooker select entities."""
    entities = [
        SkyCookerSelect(hass, entry, SELECT_TYPE_MODE),
        SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_MINUTES),
    ]
    
    # Добавляем селект для подпрограммы только если модель не MODEL_3
    skycooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    if skycooker.model_code != MODEL_3:
        entities.append(SkyCookerSelect(hass, entry, SELECT_TYPE_SUBPROGRAM))
    
    async_add_entities(entities)


class SkyCookerSelect(SelectEntity):
    """Representation of a SkyCooker select entity."""

    def __init__(self, hass, entry, select_type):
        """Initialize the select entity."""
        self.hass = hass
        self.entry = entry
        self.select_type = select_type

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.update()
        self.async_on_remove(async_dispatcher_connect(self.hass, DISPATCHER_UPDATE, self.update))

    def update(self):
        """Update the select entity."""
        self.schedule_update_ha_state()

    @property
    def skycooker(self):
        """Get the skycooker connection."""
        return self.hass.data[DOMAIN][self.entry.entry_id][DATA_CONNECTION]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.select_type}"

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
        """Return the name of the select entity."""
        base_name = (SKYCOOKER_NAME + " " + self.entry.data.get(CONF_FRIENDLY_NAME, "")).strip()

        # Определяем индекс языка (0 для английского, 1 для русского)
        language = self.hass.config.language
        is_russian = language == "ru"

        if self.select_type == SELECT_TYPE_MODE:
            return f"{base_name} {'Режим готовки' if is_russian else 'Mode'}"
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            return f"{base_name} {'Подпрограмма' if is_russian else 'Subprogram'}"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            return f"{base_name} {'Температура' if is_russian else 'Temperature'}"
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            return f"{base_name} {'Время приготовления' if is_russian else 'Cooking time'} {'(часы)' if is_russian else '(hours)'}"
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            return f"{base_name} {'Время приготовления' if is_russian else 'Cooking time'} {'(минуты)' if is_russian else '(minutes)'}"
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            return f"{base_name} {'Время отложенного старта' if is_russian else 'Delayed start'} {'(часы)' if is_russian else '(hours)'}"
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            return f"{base_name} {'Время отложенного старта' if is_russian else 'Delayed start'} {'(минуты)' if is_russian else '(minutes)'}"

        return base_name

    @property
    def icon(self):
        """Return the icon."""
        if self.select_type == SELECT_TYPE_MODE:
            return "mdi:chef-hat"
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            return "mdi:cog-outline"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            return "mdi:thermometer"
        elif self.select_type in [SELECT_TYPE_COOKING_TIME_HOURS, SELECT_TYPE_COOKING_TIME_MINUTES]:
            return "mdi:timer"
        elif self.select_type in [SELECT_TYPE_DELAYED_START_HOURS, SELECT_TYPE_DELAYED_START_MINUTES]:
            return "mdi:timer-sand"
        return None

    @property
    def available(self):
        """Return if select entity is available."""
        return self.skycooker.available

    @property
    def current_option(self):
        """Return the current selected option."""
        if self.select_type == SELECT_TYPE_MODE:
            # Используем текущий режим устройства или установленный пользователем
            mode_id = self.skycooker.current_mode
            if mode_id is None:
                return None

            # Получаем тип модели из соединения
            model_type = self.skycooker.model_code
            if model_type is None:
                return f"Unknown ({mode_id})"

            # Получаем названия режимов для текущей модели
            mode_constants = MODE_NAMES.get(model_type, [])
            if not mode_constants or mode_id >= len(mode_constants):
                return f"Unknown ({mode_id})"

            # Определяем индекс языка (0 для английского, 1 для русского)
            language = self.hass.config.language
            lang_index = 0 if language == "en" else 1

            # Получаем название режима из константы
            mode_constant = mode_constants[mode_id]
            if mode_constant and len(mode_constant) > lang_index:
                # Проверяем, является ли режим MODE_NONE
                if mode_constant == MODE_NONE:
                    return f"Unknown ({mode_id})"
                return mode_constant[lang_index]
            return f"Unknown ({mode_id})"
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            # Возвращаем текущую подпрограмму из статуса устройства
            if self.skycooker.status and self.skycooker.status.subprog is not None:
                return str(self.skycooker.status.subprog)
            return "0"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            # Возвращаем текущую температуру из пользовательских настроек или статуса
            if hasattr(self.skycooker, '_target_temperature') and self.skycooker._target_temperature is not None:
                return str(self.skycooker._target_temperature)
            elif self.skycooker.status and self.skycooker.status.target_temp:
                return str(self.skycooker.status.target_temp)
            return None
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            # Возвращаем текущие часы из пользовательских настроек или статуса
            if self.skycooker.target_boil_hours is not None:
                return str(self.skycooker.target_boil_hours)
            elif self.skycooker.status:
                return str(self.skycooker.status.target_boil_hours)
            return None
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            # Возвращаем текущие минуты из пользовательских настроек или статуса
            if self.skycooker.target_boil_minutes is not None:
                return str(self.skycooker.target_boil_minutes)
            elif self.skycooker.status:
                return str(self.skycooker.status.target_boil_minutes)
            return None
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            # Возвращаем текущие часы отложенного запуска из пользовательских настроек или статуса
            if getattr(self.skycooker, '_target_delayed_start_hours', None) is not None:
                return str(self.skycooker._target_delayed_start_hours)
            elif self.skycooker.status:
                return str(self.skycooker.status.target_delayed_start_hours)
            return None
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            # Возвращаем текущие минуты отложенного запуска из пользовательских настроек или статуса
            if getattr(self.skycooker, '_target_delayed_start_minutes', None) is not None:
                return str(self.skycooker._target_delayed_start_minutes)
            elif self.skycooker.status:
                return str(self.skycooker.status.target_delayed_start_minutes)
            return None
        return None

    @property
    def options(self):
        """Return the available options."""
        if self.select_type == SELECT_TYPE_MODE:
            # Получаем тип модели из соединения
            model_type = self.skycooker.model_code
            if model_type is None:
                return []

            # Получаем названия режимов для текущей модели
            mode_constants = MODE_NAMES.get(model_type, [])
            if not mode_constants:
                return []

            # Определяем индекс языка (0 для английского, 1 для русского)
            language = self.hass.config.language
            lang_index = 0 if language == "en" else 1

            # Извлекаем названия режимов на нужном языке
            return [mode_constant[lang_index] for mode_constant in mode_constants if mode_constant and len(mode_constant) > lang_index]
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            # Опции подпрограмм от 0 до максимального значения
            # Для большинства моделей это 0-255, но мы ограничим до 0-15 для безопасности
            return [str(i) for i in range(0, 16)]
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            # Опции температуры от 40 до 200 с шагом 5
            return [str(temp) for temp in range(40, 201, 5)]
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            # Опции часов от 0 до 23
            return [str(hour) for hour in range(0, 24)]
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            # Опции минут от 0 до 59
            return [str(minute) for minute in range(0, 60)]
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            # Опции часов отложенного запуска от 0 до 23
            return [str(hour) for hour in range(0, 24)]
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            # Опции минут отложенного запуска от 0 до 59
            return [str(minute) for minute in range(0, 60)]
        return []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.select_type == SELECT_TYPE_MODE:
            # Получаем тип модели из соединения
            model_type = self.skycooker.model_code
            if model_type is None:
                return

            # Получаем названия режимов для текущей модели
            mode_constants = MODE_NAMES.get(model_type, [])
            if not mode_constants:
                return

            # Определяем индекс языка (0 для английского, 1 для русского)
            language = self.hass.config.language
            lang_index = 0 if language == "en" else 1

            # Ищем идентификатор режима по названию
            mode_id = None
            for idx, mode_constant in enumerate(mode_constants):
                if mode_constant and len(mode_constant) > lang_index and mode_constant[lang_index] == option:
                    # Проверяем, является ли режим MODE_NONE
                    if mode_constant == MODE_NONE:
                        _LOGGER.error(f"❌ Попытка установить режим MODE_NONE (индекс {idx})")
                        return
                    mode_id = idx
                    break
                    
            if mode_id is not None:
                # Получаем значения MODE_DATA для выбранного режима
                model_type = self.skycooker.model_code
                if model_type and model_type in MODE_DATA and mode_id < len(MODE_DATA[model_type]):
                    mode_data = MODE_DATA[model_type][mode_id]
                    _LOGGER.debug(f"Selected mode {mode_id} for model {model_type}: temperature={mode_data[0]}, hours={mode_data[1]}, minutes={mode_data[2]}")
                          
                # Обновляем температуру и время приготовления данными режима только если пользователь не установил свои значения
                if not hasattr(self.skycooker, '_target_temperature') or self.skycooker._target_temperature is None:
                    self.skycooker._target_temperature = mode_data[0]
                  
                # Update target_boil_hours и target_boil_minutes with mode data only if user hasn't set custom values
                # If user has already set custom cooking time, respect their choice
                # Check if user has explicitly set custom cooking time (not just default values)
                if (not hasattr(self.skycooker, '_target_boil_hours') or 
                    not hasattr(self.skycooker, '_target_boil_minutes')):
                    # If attributes don't exist, create them with mode data
                    self.skycooker._target_boil_hours = mode_data[1]
                    self.skycooker._target_boil_minutes = mode_data[2]
                else:
                    # If attributes exist, check if they have been explicitly set by user
                    # Default values are 0 for hours and 10 for minutes
                    # If values match defaults, update with mode data
                    if (self.skycooker._target_boil_hours == 0 and self.skycooker._target_boil_minutes == 10):
                        self.skycooker._target_boil_hours = mode_data[1]
                        self.skycooker._target_boil_minutes = mode_data[2]

            # Устанавливаем целевой режим без отправки команд на устройство
            self.skycooker._target_mode = mode_id
            # Запускаем обновление диспетчера для уведомления Number сущностей об изменении режима
            async_dispatcher_send(self.hass, DISPATCHER_UPDATE)
            self.update()
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            # Помечаем, что пользователь установил собственную температуру
            self.skycooker._target_temperature = int(option)
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            # Обновляем часы в целевом времени приготовления
            self.skycooker.target_boil_hours = int(option)
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            # Обновляем минуты в целевом времени приготовления
            self.skycooker.target_boil_minutes = int(option)
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            # Устанавливаем часы отложенного запуска
            self.skycooker._target_delayed_start_hours = int(option)
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            # Устанавливаем минуты отложенного запуска
            self.skycooker._target_delayed_start_minutes = int(option)
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            # Устанавливаем целевую подпрограмму
            self.skycooker._target_subprogram = int(option)
        if self.select_type == SELECT_TYPE_DELAYED_START_HOURS and getattr(self.skycooker, '_target_delayed_start_hours', None) is None:
            self.skycooker._target_delayed_start_hours = 0
        if self.select_type == SELECT_TYPE_DELAYED_START_MINUTES and getattr(self.skycooker, '_target_delayed_start_minutes', None) is None:
            self.skycooker._target_delayed_start_minutes = 0

        # Планируем обновление для обновления состояния сущности
        self.async_schedule_update_ha_state(True)

        # Логируем новые значения для отладки
        _LOGGER.debug(f"Updated {self.select_type}: {option}")
        _LOGGER.debug(f"Current target_boil_hours: {self.skycooker.target_boil_hours}")
        _LOGGER.debug(f"Current target_boil_minutes: {self.skycooker.target_boil_minutes}")
        _LOGGER.debug(f"Current target_delayed_start_hours: {getattr(self.skycooker, '_target_delayed_start_hours', None)}")
        _LOGGER.debug(f"Current target_delayed_start_minutes: {getattr(self.skycooker, '_target_delayed_start_minutes', None)}")