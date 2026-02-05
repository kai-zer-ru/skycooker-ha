#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import traceback
from time import monotonic
from typing import Any, Optional, Tuple

from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import *
from .programs import get_program_constants, find_program_id, \
    find_program_id_by_const, get_standby_program_name, get_program_name, is_program_supported, get_constant_by_name
from .status import get_status


def is_mode_supported(hass, program_name: str, model_id: int) -> bool:
    """Проверяет, поддерживается ли режим устройством (устаревшее название для совместимости)."""
    return is_program_supported(hass, program_name, model_id)

_LOGGER = logging.getLogger(__name__)


class SkyCookerCookingController:
    """Класс для управления логикой приготовления."""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        # self._target_program_name - название программы на языке, который установлен в системе, не число и не константа!!!!
        self._target_program_name = self._get_standby_program_name()
        self._auto_warm_enabled = True
        self._target_subprogram_id = None
        self._target_temperature = 100
        self._target_main_hours = 0
        self._target_main_minutes = 0
        self._target_additional_hours = 0
        self._target_additional_minutes = 0
        self._status = None
        self._last_set_target = 0

    async def select_program(self, program_id: int, subprog: int=0):
        """Выбор программы приготовления."""
        program_name = get_program_name(self.connection_manager.hass, program_id, self.connection_manager.model_id)
        standby_program_name = self._get_standby_program_name()
        if program_name != standby_program_name and not self.is_program_supported(program_name):
            _LOGGER.error(f"❌ Попытка установить неподдерживаемый режим {program_name}")
            raise ValueError(f"Режим {program_name} не поддерживается устройством")
        
        model_id = self.connection_manager.model_id
        program_constants = get_program_constants(model_id)
        if model_id and program_id < len(program_constants):
            program_constant = program_constants[program_id]
            if program_constant == PROGRAM_NONE:
                _LOGGER.error(f"❌ Попытка установить режим PROGRAM_NONE (индекс {program_id})")
                raise ValueError(f"Режим {program_name} не поддерживается устройством (PROGRAM_NONE)")
            elif program_constant == PROGRAM_STANDBY:
                self._target_temperature = 100
                self._target_main_hours = 0
                self._target_main_minutes = 0
                self._target_additional_hours = 0
                self._target_additional_minutes = 0
                return
        
        _LOGGER.debug(f"📤 Отправка команды SELECT_PROGRAM для режима {program_name}")
        await self.connection_manager.select_program(program_id, subprog)
        
        model_id = self.connection_manager.model_id
        if model_id and model_id in PROGRAM_DATA and program_id < len(PROGRAM_DATA[model_id]):
            program_data = PROGRAM_DATA[model_id][program_id]
            
            target_temperature_from_program = program_data["temperature"]
            if target_temperature_from_program != 0:
                if not hasattr(self, '_target_temperature') or self._target_temperature is None:
                    self._target_temperature = target_temperature_from_program
            
            if (not hasattr(self, '_target_main_hours') or self._target_main_hours is None or
                not hasattr(self, '_target_main_minutes') or self._target_main_minutes is None):
                self._target_main_hours = program_data["hours"]
                self._target_main_minutes = program_data["minutes"]
            
            if getattr(self, '_target_additional_hours', None) is None and getattr(self, '_target_additional_minutes', None) is None:
                self._target_additional_hours = 0
                self._target_additional_minutes = 0
    
    def is_program_supported(self, program_name: str):
        """Публичный метод для проверки поддержки программы устройством."""
        return is_mode_supported(self.connection_manager.hass, program_name, self.connection_manager.model_id)

    async def execute_cooking_sequence(self, target_program_id, target_subprogram_id, target_temperature,
                                       target_main_hours, target_main_minutes,
                                       target_additional_hours, target_additional_minutes,
                                       auto_warm_flag):
        """Публичный метод для выполнения последовательности приготовления."""
        await self._execute_cooking_sequence(target_program_id, target_subprogram_id, target_temperature,
                                             target_main_hours, target_main_minutes,
                                             target_additional_hours, target_additional_minutes,
                                             auto_warm_flag)

    def get_delayed_start_parameters(self):
        """Публичный метод для получения параметров отложенного старта."""
        return self._get_delayed_start_parameters()

    def get_program_parameters(self, operation_mode):
        """Публичный метод для получения параметров программы."""
        return self._get_program_parameters(operation_mode)

    @property
    def auto_warm_enabled(self):
        """Публичное свойство для доступа к состоянию автоподогрева."""
        return self._auto_warm_enabled

    @auto_warm_enabled.setter
    def auto_warm_enabled(self, value):
        """Установка состояния автоподогрева."""
        self._auto_warm_enabled = value

    def _get_cooking_parameters(self, target_program_name: str) -> list[Any]:
        """Получение параметров приготовления на основе целевой программы."""
        model_id = self.connection_manager.model_id
        target_program_id = find_program_id(self.connection_manager.hass, target_program_name, model_id)
        target_temperature = self._target_temperature if hasattr(self, '_target_temperature') else 100
        target_main_hours = self._target_main_hours if self._target_main_hours is not None else 0
        target_main_minutes = self._target_main_minutes if self._target_main_minutes is not None else 0
        
        target_subprogram_id = getattr(self, '_target_subprogram_id', 0)
        _LOGGER.debug(f"🎯 Используется подпрограмма {target_subprogram_id}")
        
        if target_temperature is None:
            if model_id and model_id in PROGRAM_DATA and target_program_id < len(PROGRAM_DATA[model_id]):
                target_temperature = PROGRAM_DATA[model_id][target_program_id]["temperature"]
        
        if target_main_hours == 0 and target_main_minutes == 0:
            if model_id and model_id in PROGRAM_DATA and target_program_id < len(PROGRAM_DATA[model_id]):
                target_main_hours = PROGRAM_DATA[model_id][target_program_id]["hours"]
                target_main_minutes = PROGRAM_DATA[model_id][target_program_id]["minutes"]
        
        target_main_hours = target_main_hours or 0
        target_main_minutes = target_main_minutes or 0
        
        return [target_program_id, target_subprogram_id, target_temperature, target_main_hours, target_main_minutes]
    
    async def _execute_cooking_sequence(self, target_program_id: int, target_subprogram_id: int, target_temperature: int,
                                        target_main_hours: int, target_main_minutes: int,
                                        target_additional_hours: int, target_additional_minutes: int,
                                        auto_warm_flag: int):
        """Выполнение последовательности приготовления."""
        # is_in_standby = self._status and self._get_constant_by_name(self._status.program_name) == PROGRAM_STANDBY
        is_in_standby = self._get_constant_by_name(self.target_program_name) == PROGRAM_STANDBY
        current_program_id = self._status.program_id if self._status else None
        device_is_on = self._status.is_on if self._status else False
        
        if is_in_standby:
            _LOGGER.debug("🔄 Устройство находится в режиме ожидания (MODE_STANDBY статус)")
            _LOGGER.debug("📤 Отправка команды 09 с выбранным режимом и подпрограммой")
            await self.select_program(target_program_id, target_subprogram_id)
            await asyncio.sleep(0.5)
               
            _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
            await self.connection_manager.set_main_program(target_program_id, target_subprogram_id, target_temperature, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes, auto_warm_flag)
            await asyncio.sleep(0.3)
             
            _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
            await self.connection_manager.turn_on()
        elif current_program_id == target_program_id and device_is_on:
            _LOGGER.debug(f"🔄 На мультиварке уже выбран режим {target_program_id}, и он совпадает с выбранным в интерфейсе")
            _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
            await self.connection_manager.set_main_program(target_program_id, target_subprogram_id, target_temperature, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes, auto_warm_flag)
            await asyncio.sleep(0.3)
               
            _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
            await self.connection_manager.turn_on()
        elif current_program_id != target_program_id:
            _LOGGER.debug(f"🔄 На мультиварке уже выбран режим {current_program_id}, и он НЕ совпадает с выбранным в интерфейсе ({target_program_id})")
            _LOGGER.debug("📤 Отправка команды 09 с выбранным режимом и подпрограммой")
            await self.select_program(target_program_id, target_subprogram_id)
            await asyncio.sleep(0.5)
               
            _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
            await self.connection_manager.set_main_program(target_program_id, target_subprogram_id, target_temperature, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes, auto_warm_flag)
            await asyncio.sleep(0.3)
                  
            _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
            await self.connection_manager.turn_on()
        else:
            _LOGGER.warning("🔄 Неизвестное состояние устройства, отправляем все команды")
            await self.select_program(target_program_id, target_subprogram_id)
            await asyncio.sleep(0.3)
               
            await self.connection_manager.set_main_program(target_program_id, target_subprogram_id, target_temperature, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes, auto_warm_flag)
            await asyncio.sleep(0.3)
               
            await self.connection_manager.turn_on()
    
    async def start(self):
        """Запуск приготовления с текущими настройками."""

        if not self.connection_manager.connected:
            _LOGGER.error("❌ Устройство не подключено. Пожалуйста, проверьте соединение и повторите попытку.")
            raise SkyCookerError("Устройство не подключено")
        if self._target_program_name == self._get_standby_program_name():
            return
        auto_warm_flag = self._get_auto_warm_flag()
        [target_program_id, target_subprogram_id, target_temp, target_main_hours, target_main_minutes] = self._get_cooking_parameters(self._target_program_name) # Строка с НАЗВАНИЕМ!!!!)
        try:
            await self.connection_manager.connect_if_need()
            await self._execute_cooking_sequence(target_program_id, target_subprogram_id, target_temp,
                                                 target_main_hours, target_main_minutes,
                                                 0, 0, auto_warm_flag)
            # self._status = await get_status(self.connection_manager)
            if self.connection_manager.hass:
                async_dispatcher_send(self.connection_manager.hass, DISPATCHER_UPDATE)
        except Exception as ex:
            _LOGGER.error(f"❌ Ошибка при запуске приготовления: {str(ex)}")
            if "Некорректный размер данных статуса" in str(ex):
                _LOGGER.error("💡 Проверьте соединение с устройством и повторите попытку")
            raise
        finally:
            await self.connection_manager.disconnect_if_need()
    
    async def enable_auto_warm(self) -> None:
        """Включение режима автоподогрева."""
        self._auto_warm_enabled = True

    async def disable_auto_warm(self) -> None:
        """Выключение режима автоподогрева."""
        self._auto_warm_enabled = False
    
    async def stop_cooking(self) -> None:
        """Остановка приготовления."""
        await self.connection_manager.turn_off()
        
        # Сбрасываем все целевые значения к значениям по умолчанию
        await self.set_target_program(self._get_standby_program_name())
        _LOGGER.debug(f"target_program_name: {self._target_program_name}, target_temperature: {self._target_temperature}, target_main_hours: {self._target_main_hours}, "
                      f"target_main_minutes: {self._target_main_minutes}, target_additional_hours: {self._target_additional_hours}, target_additional_minutes: {self._target_additional_minutes}"
                      f"auto_warm: {self._auto_warm_enabled}, target_program_name: {self._target_program_name}")
        if self.connection_manager.hass:
            async_dispatcher_send(self.connection_manager.hass, DISPATCHER_UPDATE)

        # self._status = await get_status(self.connection_manager)
    
    def _get_delayed_start_parameters(self) -> Tuple[int, int]:
        """Получение параметров отложенного старта."""
        target_additional_hours = 0
        target_additional_minutes = 0
        
        if hasattr(self, '_target_additional_hours') and self._target_additional_hours is not None:
            target_additional_hours = self._target_additional_hours
        if hasattr(self, '_target_additional_minutes') and self._target_additional_minutes is not None:
            target_additional_minutes = self._target_additional_minutes
        
        target_additional_hours = target_additional_hours or 0
        target_additional_minutes = target_additional_minutes or 0
        
        return target_additional_hours, target_additional_minutes
    
    async def start_delayed(self) -> None:
        """Запуск приготовления с отложенным стартом."""
        _LOGGER.debug("Starting cooking with delayed start")

        if not self.connection_manager.connected:
            _LOGGER.error("❌ Устройство не подключено. Пожалуйста, проверьте соединение и повторите попытку.")
            raise SkyCookerError("Устройство не подключено")

        if self._target_program_name == self._get_standby_program_name():
            return
        target_program_id, target_subprogram_id, target_temp, target_main_hours, target_main_minutes = self._get_cooking_parameters(self._target_program_name)
        target_additional_hours, target_additional_minutes = self._get_delayed_start_parameters()
        auto_warm_flag = self._get_auto_warm_flag()
        try:
            await self.connection_manager.connect_if_need()

            await self._execute_cooking_sequence(target_program_id, target_subprogram_id, target_temp,
                                                 target_main_hours, target_main_minutes,
                                                 target_additional_hours, target_additional_minutes,
                                                 auto_warm_flag)
            # self._status = await get_status(self.connection_manager)
            if self.connection_manager.hass:
                async_dispatcher_send(self.connection_manager.hass, DISPATCHER_UPDATE)
        except Exception as ex:
            _LOGGER.error(f"❌ Ошибка при настройке отложенного старта: {str(ex)}")
            raise
        finally:
            await self.connection_manager.disconnect_if_need()

    async def set_target_temp(self, target_temp: int) -> None:
        """Установка целевой температуры."""
        if target_temp == self.target_temperature:
            return
        self._target_temperature = target_temp
        self._last_set_target = monotonic()

    def _get_auto_warm_flag(self) -> int:
        return 1 if getattr(self, '_auto_warm_enabled', False) else 0

    def _get_standby_program_name(self):
        return get_standby_program_name(self.connection_manager.hass, self.connection_manager.model_id)

    def _get_constant_by_name(self, program_name: str) -> Optional[str]:
        return get_constant_by_name(self.connection_manager.hass, program_name, self.connection_manager.model_id)

    def _get_program_parameters(self, program_name: str) -> Tuple[int, int, int]:
        """Получение параметров режима."""
        model_id = self.connection_manager.model_id
        program_const = self._get_constant_by_name(program_name)
        target_temperature = 90
        target_main_hours = 0
        target_main_minutes = 0
        if program_const == PROGRAM_STANDBY: # Режим ожидания
            target_temperature = 100
            target_main_hours = 0
            target_main_minutes = 0

            return target_temperature, target_main_hours, target_main_minutes
        program_id = find_program_id_by_const(self.connection_manager.hass, program_name, self.connection_manager.model_id)
        if model_id and model_id in PROGRAM_DATA and program_id == PROGRAM_NAMES[model_id].index(program_const):
            program_data = PROGRAM_DATA[model_id][program_id]
            target_temperature = program_data["temperature"]
            target_main_hours = program_data["hours"]
            target_main_minutes = program_data["minutes"]

        return target_temperature, target_main_hours, target_main_minutes
    
    async def set_target_program(self, program_name: str) -> None:
        """Установка целевой программы."""
        if program_name == self._target_program_name: return
        program_const = self._get_constant_by_name(program_name)
        if program_const == PROGRAM_STANDBY:
            self._target_program_name = self._get_standby_program_name()
            self._target_temperature = 100
            self._target_main_hours = 0
            self._target_main_minutes = 0
            self._target_additional_hours = 0
            self._target_additional_minutes = 0
            self._auto_warm_enabled = True
            return
        if not self.is_program_supported(program_name):
            _LOGGER.error(f"❌ Программа {program_name} не поддерживается устройством")
            return

        target_temperature, target_main_hours, target_main_minutes = self._get_program_parameters(program_name)

        if getattr(self, '_target_additional_hours', None) is None:
            self._target_additional_hours = 0
        if getattr(self, '_target_additional_minutes', None) is None:
            self._target_additional_minutes = 0

        self._target_program_name = program_name
        self._target_temperature = target_temperature
        self._last_set_target = monotonic()

        self._target_main_hours = target_main_hours
        self._target_main_minutes = target_main_minutes

    
    async def set_boil_time(self, target_main_hours: int, target_main_minutes: int) -> None:
        """Установка времени приготовления."""
        self._target_main_hours = int(target_main_hours)
        self._target_main_minutes = int(target_main_minutes)

    async def set_temperature(self, value: int) -> None:
        """Установка температуры."""
        value = int(value)
        self._target_temperature = value

    async def set_delayed_start(self, target_additional_hours: int, target_additional_minutes: int) -> None:
        """Установка отложенного старта."""
        self._target_additional_hours = int(target_additional_hours)
        self._target_additional_minutes = int(target_additional_minutes)
    
    @property
    def target_temperature(self):
        """Целевая температура."""
        if hasattr(self, '_target_temperature') and self._target_temperature is not None:
            return self._target_temperature
        if self._status:
            if self._status.is_on:
                return self._status.target_temperature
            else:
                return 25
        return None
    
    @property
    def target_program_name(self):
        """Целевая программа."""
        if hasattr(self, '_target_program_name') and self._target_program_name is not None:
            return self._target_program_name
        else:
            if self._status and self._status.is_on:
                return self._status.program_name
        return None

    @target_program_name.setter
    def target_program_name(self, value):
        """Установка целевой программы."""
        self._target_program_name = value
    
    @property
    def target_main_hours(self):
        """Целевые часы приготовления."""
        return getattr(self, '_target_main_hours', None)

    @target_main_hours.setter
    def target_main_hours(self, value):
        """Установка целевых часов приготовления."""
        self._target_main_hours = value

    @target_main_hours.deleter
    def target_main_hours(self):
        """Удаление целевых часов приготовления."""
        delattr(self, '_target_main_hours')
    
    @property
    def target_main_minutes(self):
        """Целевые минуты приготовления."""
        return getattr(self, '_target_main_minutes', None)

    @target_main_minutes.setter
    def target_main_minutes(self, value):
        """Установка целевых минут приготовления."""
        self._target_main_minutes = value

    @target_main_minutes.deleter
    def target_main_minutes(self):
        """Удаление целевых минут приготовления."""
        delattr(self, '_target_main_minutes')
    
    @property
    def target_additional_hours(self):
        """Целевые часы отложенного старта."""
        return getattr(self, '_target_additional_hours', None)

    @target_additional_hours.setter
    def target_additional_hours(self, value):
        """Установка целевых часов отложенного старта."""
        self._target_additional_hours = value

    @target_additional_hours.deleter
    def target_additional_hours(self):
        """Удаление целевых часов отложенного старта."""
        delattr(self, '_target_additional_hours')
    
    @property
    def target_additional_minutes(self):
        """Целевые минуты отложенного старта."""
        return getattr(self, '_target_additional_minutes', None)

    @target_additional_minutes.setter
    def target_additional_minutes(self, value):
        """Установка целевых минут отложенного старта."""
        self._target_additional_minutes = value

    @target_additional_minutes.deleter
    def target_additional_minutes(self):
        """Удаление целевых минут отложенного старта."""
        delattr(self, '_target_additional_minutes')
    
    @property
    def target_subprogram_id(self):
        return self._target_subprogram_id

    @target_subprogram_id.setter
    def target_subprogram_id(self, value):
        """Установка целевой подпрограммы."""
        self._target_subprogram_id = value

    @target_temperature.setter
    def target_temperature(self, value):
        """Установка целевой температуры."""
        self._target_temperature = value
    
    @property
    def status(self):
        """Текущий статус."""
        return self._status

    @status.setter
    def status(self, value):
        """Установка текущего статуса."""
        self._status = value

    @property
    def current_program_id(self):
        """Текущая программ (ID)."""
        if self._status and self._status.is_on:
            return self._status.program_id
        return None

    @property
    def last_set_target(self):
        """Время последней установки цели."""
        return self._last_set_target

class SkyCookerError(Exception):
    pass