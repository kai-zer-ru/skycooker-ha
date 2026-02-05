"""Сущности выбора SkyCooker."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import *
from .entity_base import SkyCookerEntity
from .utils import (get_base_name, get_temperature_options, get_entity_name)
from .time import get_time_options, _validate_hours, _validate_minutes
from .programs import (get_favorite_programs, get_program_options,
                       is_subprogram_supported, find_program_id, get_subprogram_options, get_program_data,
                       get_constant_by_name, get_standby_program_name)

_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Настройка сущностей выбора SkyCooker."""
    entities: list[SkyCookerSelect] = [
        SkyCookerSelect(hass, entry, SELECT_TYPE_PROGRAM),
        SkyCookerSelect(hass, entry, SELECT_TYPE_TEMPERATURE),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_COOKING_TIME_MINUTES),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_HOURS),
        SkyCookerSelect(hass, entry, SELECT_TYPE_DELAYED_START_MINUTES),
    ]
    
    # Добавляем селект для подпрограммы только если модель поддерживает подпрограммы
    skycooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    if is_subprogram_supported(skycooker.model_id):
        entities.append(SkyCookerSelect(hass, entry, SELECT_TYPE_SUBPROGRAM))

    # Добавляем селект для избранных программ только если они настроены
    favorite_programs = get_favorite_programs(hass, entry, skycooker.model_id)
    if favorite_programs:
        entities.append(SkyCookerSelect(hass, entry, SELECT_TYPE_FAVORITES))

    async_add_entities(entities)


class SkyCookerSelect(SkyCookerEntity, SelectEntity):
    """Представление сущности выбора SkyCooker."""

    def __init__(self, hass, entry, select_type: str) -> None:
        """Инициализация сущности выбора."""
        super().__init__(hass, entry)
        self.select_type = select_type

    async def async_added_to_hass(self) -> None:
        """Вызывается при добавлении сущности в Home Assistant."""
        await super().async_added_to_hass()
        # Устанавливаем значения по умолчанию для селектов времени
        if self.select_type in [SELECT_TYPE_COOKING_TIME_HOURS, SELECT_TYPE_COOKING_TIME_MINUTES,
                                SELECT_TYPE_DELAYED_START_HOURS, SELECT_TYPE_DELAYED_START_MINUTES, SELECT_TYPE_TEMPERATURE]:
            await self._set_default_time_values()
        # Устанавливаем программу "Режим ожидания" по умолчанию для селекта программ приготовления
        elif self.select_type == SELECT_TYPE_PROGRAM or self.select_type == SELECT_TYPE_FAVORITES:
            await self._set_default_mode()

    async def _set_default_time_values(self) -> None:
        """Установка значений по умолчанию для селектов времени."""
        if self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            if getattr(self.skycooker, 'target_main_hours', None) is None:
                self.skycooker.target_main_hours = 0
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            if getattr(self.skycooker, 'target_main_minutes', None) is None:
                self.skycooker.target_main_minutes = 0
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            if getattr(self.skycooker, 'target_additional_hours', None) is None:
                self.skycooker.target_additional_hours = 0
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            if getattr(self.skycooker, 'target_additional_minutes', None) is None:
                self.skycooker.target_additional_minutes = 0
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            if getattr(self.skycooker, 'target_temperature', None) is None:
                self.skycooker.target_temperature = 100

    async def _set_default_mode(self) -> None:
        """Установка программы ожидания по умолчанию для селекта программ приготовления."""
        # Находим программ ожидания для текущей модели.
        self.skycooker.target_program_name = self._get_standby_program_name()
        _LOGGER.debug(f"Установлена программа ожидания по умолчанию: mode_name={self.skycooker.target_program_name}")

    @property
    def unique_id(self) -> str:
        """Возвращает уникальный идентификатор."""
        return f"{self.entry.entry_id}_{self.select_type}"

    @property
    def name(self) -> str:
        """Возвращает имя сущности выбора."""
        if self.select_type == SELECT_TYPE_PROGRAM:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Mode', 'Программа приготовления')
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
        elif self.select_type == SELECT_TYPE_FAVORITES:
            return get_entity_name(self.hass, self.entry, self.select_type, 'Favorites', 'Избранное')

        return get_base_name(self.entry)

    @property
    def icon(self) -> str | None:
        """Возвращает иконку."""
        icons = {
            SELECT_TYPE_PROGRAM: "mdi:chef-hat",
            SELECT_TYPE_SUBPROGRAM: "mdi:cog-outline",
            SELECT_TYPE_TEMPERATURE: "mdi:thermometer",
            SELECT_TYPE_COOKING_TIME_HOURS: "mdi:timer",
            SELECT_TYPE_COOKING_TIME_MINUTES: "mdi:timer",
            SELECT_TYPE_DELAYED_START_HOURS: "mdi:timer-sand",
            SELECT_TYPE_DELAYED_START_MINUTES: "mdi:timer-sand",
            SELECT_TYPE_FAVORITES: "mdi:star",
        }
        return icons.get(self.select_type)

    @property
    def current_option(self) -> str | None:
        """Возвращает текущий выбранный вариант."""
        if self.select_type == SELECT_TYPE_PROGRAM or self.select_type == SELECT_TYPE_FAVORITES:
            program_name = self.skycooker.target_program_name
            if self.select_type == SELECT_TYPE_FAVORITES:
                if program_name not in get_favorite_programs(self.hass, self.entry, self.skycooker.model_id):
                    return None
            return program_name
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            if hasattr(self.skycooker, 'target_subprogram_id') and self.skycooker.target_subprogram_id is not None:
                return str(self.skycooker.target_subprogram_id)
            return "0"
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            if hasattr(self.skycooker, 'target_temperature') and self.skycooker.target_temperature is not None:
                return str(self.skycooker.target_temperature)
            else:
                return "0"  # Return "0" when temperature is None for proper display
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            if self.skycooker.target_main_hours is not None:
                return str(self.skycooker.target_main_hours)
            else:
                return "0"
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            if self.skycooker.target_main_minutes is not None:
                return str(self.skycooker.target_main_minutes)
            else:
                return "0"
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            if hasattr(self.skycooker, 'target_additional_hours'):
                return str(self.skycooker.target_additional_hours)
            else:
                return "0"
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            if hasattr(self.skycooker, 'target_additional_minutes'):
                return str(self.skycooker.target_additional_minutes)
            else:
                return "0"
        return None

    @property
    def options(self) -> list[str]:
        """Возвращает доступные варианты."""
        if self.select_type == SELECT_TYPE_PROGRAM:
            return get_program_options(self.hass, self.skycooker.model_id)
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            return get_subprogram_options()
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            return get_temperature_options()
        elif self.select_type in [SELECT_TYPE_COOKING_TIME_HOURS, SELECT_TYPE_DELAYED_START_HOURS]:
            return get_time_options(hours=True)
        elif self.select_type in [SELECT_TYPE_COOKING_TIME_MINUTES, SELECT_TYPE_DELAYED_START_MINUTES]:
            return get_time_options(hours=False)
        elif self.select_type == SELECT_TYPE_FAVORITES:
            return get_favorite_programs(self.hass, self.entry, self.skycooker.model_id)
        return []

    async def async_select_option(self, option: str) -> None:
        """Изменение выбранного варианта."""
        if self.select_type == SELECT_TYPE_PROGRAM or self.select_type == SELECT_TYPE_FAVORITES:
            await self._handle_program_selection(option)
        elif self.select_type == SELECT_TYPE_TEMPERATURE:
            self.skycooker.target_temperature = int(option)
        elif self.select_type == SELECT_TYPE_COOKING_TIME_HOURS:
            self.skycooker.target_main_hours = _validate_hours(int(option))
        elif self.select_type == SELECT_TYPE_COOKING_TIME_MINUTES:
            self.skycooker.target_main_minutes = _validate_minutes(int(option))
        elif self.select_type == SELECT_TYPE_DELAYED_START_HOURS:
            self.skycooker.target_additional_hours = _validate_hours(int(option))
        elif self.select_type == SELECT_TYPE_DELAYED_START_MINUTES:
            self.skycooker.target_additional_minutes = _validate_minutes(int(option))
        elif self.select_type == SELECT_TYPE_SUBPROGRAM:
            self.skycooker.target_subprogram_id = int(option)
        else:
            return None
            
        # Устанавливаем значения по умолчанию для отложенного запуска, если они не установлены
        if self.select_type in [SELECT_TYPE_DELAYED_START_HOURS, SELECT_TYPE_DELAYED_START_MINUTES]:
            if getattr(self.skycooker, 'target_additional_hours', None) is None:
                self.skycooker.target_additional_hours = 0
            if getattr(self.skycooker, 'target_additional_minutes', None) is None:
                self.skycooker.target_additional_minutes = 0
         
        self.async_schedule_update_ha_state(True)
          
        # Если это изменение программ, отправляем событие обновления для всех сущностей
        # чтобы обновить связанные селекты (время приготовления, температура и т.д.)
        if self.select_type == SELECT_TYPE_PROGRAM or self.select_type == SELECT_TYPE_FAVORITES:
            async_dispatcher_send(self.hass, DISPATCHER_UPDATE)
         
        return None

    async def _handle_program_selection(self, selected_program_name: str) -> None:
        """Обработка выбора программ."""
        model_id = self.skycooker.model_id
        if model_id is None:
            _LOGGER.warning("⚠️  model_id is None, возвращаем None")
            return None
        # Если выбрана пустая строка, не делаем ничего
        if not selected_program_name or selected_program_name == "":
            # Устанавливаем режим ожидания вместо пустого значения
            self.skycooker.target_program_name = self._get_standby_program_name()
            # Вызываем обновление состояния сущности
            self.async_schedule_update_ha_state(True)
            return None

        program_constant = get_constant_by_name(self.hass, selected_program_name, model_id)
        if program_constant == PROGRAM_NONE:
            return None
        program_id = find_program_id(self.hass, selected_program_name, model_id)
        if program_id is None:
            return None

        program_data = get_program_data(model_id, program_id)
        if program_data:
            if self.select_type == SELECT_TYPE_PROGRAM:
                _LOGGER.debug(f"Выбран режим {program_id} ({selected_program_name}) для модели {model_id}: температура={program_data['temperature']}, часы={program_data['hours']}, минуты={program_data['minutes']}")
            else:
                _LOGGER.debug(
                    f"Выбран режим из избранного {program_id} ({selected_program_name}) для модели {model_id}: температура={program_data['temperature']}, часы={program_data['hours']}, минуты={program_data['minutes']}")
            self.skycooker.target_temperature = program_data['temperature']
            self.skycooker.target_main_hours = _validate_hours(program_data['hours'])
            self.skycooker.target_main_minutes = _validate_minutes(program_data['minutes'])
        # target_program_name - всегда "Название программы", не число и не константа!
        self.skycooker.target_program_name = selected_program_name
        # Вызываем обновление для всех сущностей, чтобы немедленно обновить связанные селекты
        async_dispatcher_send(self.hass, DISPATCHER_UPDATE)
        return None

    def _get_standby_program_name(self):
        return get_standby_program_name(self.hass, self.skycooker.model_id)