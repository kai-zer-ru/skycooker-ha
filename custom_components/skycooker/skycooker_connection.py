#!/usr/local/bin/python3
# coding: utf-8

import logging
from typing import Optional, Any, Dict

from .const import *
from .programs import find_program_id
from .skycooker import SkyCooker
from .skycooker_connection_manager import SkyCookerConnectionManager
from .skycooker_cooking_controller import SkyCookerCookingController
from .skycooker_state_manager import SkyCookerStateManager

_LOGGER = logging.getLogger(__name__)


class SkyCookerConnection(SkyCooker):

    def __init__(
        self,
        mac: str,
        key: bytes,
        persistent: bool = True,
        adapter: Optional[Any] = None,
        hass: Optional[Any] = None,
        model_name: Optional[str] = None,
    ) -> None:
        super().__init__(hass, model_name)
        # Инициализация компонентов
        self.connection_manager = SkyCookerConnectionManager(mac, key, persistent, adapter, hass, model_name)
        self.cooking_controller = SkyCookerCookingController(self.connection_manager)
        self.state_manager = SkyCookerStateManager(self.connection_manager, self.cooking_controller)
     
    # Делегирование методов к соответствующим компонентам
    
    async def command(self, command: int, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self.connection_manager.command(command, params)
    
    def _rx_callback(self, sender: Any, data: Any) -> None:
        # Заменим вызов защищенного метода на публичный
        self.connection_manager.rx_callback(sender, data)
    
    async def _connect(self):
        # Заменим вызов защищенного метода на публичный
        await self.connection_manager.connect()
    
    auth = lambda self: self.connection_manager.auth()
    
    async def select_program(self, program_name: str, subprog_id: int = 0) -> None:
        program_id = find_program_id(self.connection_manager.hass, program_name, self.model_id)
        await self.cooking_controller.select_program(program_id, subprog_id)
    
    async def _cleanup_previous_connections(self):
        # Заменим вызов защищенного метода на публичный
        await self.connection_manager.cleanup_previous_connections()
    
    async def _disconnect(self):
        # Заменим вызов защищенного метода на публичный
        await self.connection_manager.disconnect()
    
    async def disconnect(self):
        await self.connection_manager.disconnect()
    
    async def _connect_if_need(self):
        # Заменим вызов защищенного метода на публичный
        await self.connection_manager.connect_if_need()
    
    async def _disconnect_if_need(self):
        # Заменим вызов защищенного метода на публичный
        await self.connection_manager.disconnect_if_need()
    
    async def update(
        self,
        tries: int = MAX_TRIES,
        force_stats: bool = False,
        extra_action: Optional[Any] = None,
        commit: bool = False,
    ) -> Any:
        return await self.state_manager.update(tries, force_stats, extra_action, commit)
    
    def add_stat(self, value):
        self.connection_manager.add_stat(value)
    
    @property
    def success_rate(self):
        return self.state_manager.success_rate
    
    async def commit(self):
        await self.state_manager.commit()
    
    def _is_program_supported(self, mode: str) -> bool:
        # Заменим вызов защищенного метода на публичный
        return self.cooking_controller.is_program_supported(mode)
    
    async def stop(self):
        await self.connection_manager.stop()
    
    @property
    def available(self):
        return self.connection_manager.available
    
    @property
    def last_connect_ok(self):
        return self.connection_manager.last_connect_ok
    
    @property
    def last_auth_ok(self):
        return self.connection_manager.last_auth_ok
    
    @property
    def auto_warm(self):
        return self.state_manager.auto_warm
    
    @property
    def subprog(self):
        return self.state_manager.subprog
    
    @property
    def current_program_id(self):
        return self.cooking_controller.current_program_id
    
    @property
    def target_temperature(self):
        return self.cooking_controller.target_temperature
    
    @property
    def target_program_name(self):
        return self.cooking_controller.target_program_name

    @target_program_name.setter
    def target_program_name(self, value):
        self.cooking_controller.target_program_name = value

    @property
    def target_main_hours(self):
        return self.cooking_controller.target_main_hours
    
    @target_main_hours.setter
    def target_main_hours(self, value):
        self.cooking_controller.target_main_hours = value
    
    @property
    def target_main_minutes(self):
        return self.cooking_controller.target_main_minutes
    
    @target_main_minutes.setter
    def target_main_minutes(self, value):
        self.cooking_controller.target_main_minutes = value
    
    @property
    def target_additional_hours(self):
        return self.cooking_controller.target_additional_hours
    
    @target_additional_hours.setter
    def target_additional_hours(self, value):
        self.cooking_controller.target_additional_hours = value
    
    @property
    def target_additional_minutes(self):
        return self.cooking_controller.target_additional_minutes
    
    @target_additional_minutes.setter
    def target_additional_minutes(self, value):
        self.cooking_controller.target_additional_minutes = value
    
    @property
    def target_subprogram_id(self):
        return self.cooking_controller.target_subprogram_id

    @target_subprogram_id.setter
    def target_subprogram_id(self, value):
        self.cooking_controller.target_subprogram_id = value

    @target_temperature.setter
    def target_temperature(self, value):
        self.cooking_controller.target_temperature = value
    
    @property
    def status(self):
        return self.cooking_controller.status
    
    @property
    def connected(self):
        return self.connection_manager.connected
    
    @property
    def auth_ok(self):
        return self.connection_manager.auth_ok
    
    @property
    def sw_version(self):
        return self.connection_manager.sw_version
    
    @property
    def status_code(self):
        return self.state_manager.status_code

    @property
    def auto_warm_enabled(self) -> bool:
        """Возвращает состояние автоподогрева из cooking_controller."""
        return self.cooking_controller.auto_warm_enabled

    @auto_warm_enabled.setter
    def auto_warm_enabled(self, value: bool) -> None:
        """Устанавливает состояние автоподогрева через cooking_controller."""
        self.cooking_controller.auto_warm_enabled = value

    @property
    def _successes(self):
        """Возвращает список успешных операций из connection_manager."""
        # Заменим вызов защищенного свойства на публичное
        return self.connection_manager.successes

    @property
    def _disposed(self):
        """Возвращает состояние disposed из connection_manager."""
        # Заменим вызов защищенного свойства на публичное
        return self.connection_manager.disposed

    @property
    def _mac(self):
        """Возвращает MAC адрес из connection_manager."""
        # Заменим вызов защищенного свойства на публичное
        return self.connection_manager.mac_address
    
    async def set_boil_time(self, target_main_hours: int, target_main_minutes: int) -> None:
        # Ограничиваем значения часов и минут
        target_main_hours = min(target_main_hours, 23)
        target_main_minutes = min(target_main_minutes, 59)
        await self.cooking_controller.set_boil_time(target_main_hours, target_main_minutes)
    
    async def set_temperature(self, value: int) -> None:
        await self.cooking_controller.set_temperature(value)
    
    async def set_delayed_start(self, target_additional_hours: int, target_additional_minutes: int) -> None:
        # Ограничиваем значения часов и минут
        target_additional_hours = min(target_additional_hours, 23)
        target_additional_minutes = min(target_additional_minutes, 59)
        await self.cooking_controller.set_delayed_start(target_additional_hours, target_additional_minutes)
    
    async def _execute_cooking_sequence(
        self,
        target_program_id: int,
        target_subprogram_id: int,
        target_temp: int,
        target_main_hours: int,
        target_main_minutes: int,
        target_additional_hours: int,
        target_additional_minutes: int,
        auto_warm_flag: bool,
    ) -> None:
        _LOGGER.debug("Инициализация последовательности приготовления 1111111")
        # Ограничиваем значения часов и минут
        target_main_hours = min(target_main_hours, 23)
        target_main_minutes = min(target_main_minutes, 59)
        target_additional_hours = min(target_additional_hours, 23)
        target_additional_minutes = min(target_additional_minutes, 59)
        # Заменим вызов защищенного метода на публичный
        await self.cooking_controller.execute_cooking_sequence(
            target_program_id,
            target_subprogram_id,
            target_temp,
            target_main_hours,
            target_main_minutes,
            target_additional_hours,
            target_additional_minutes,
            auto_warm_flag,
        )
    
    async def start(self):
        await self.cooking_controller.start()
    
    async def enable_auto_warm(self):
        await self.cooking_controller.enable_auto_warm()
    
    async def disable_auto_warm(self):
        await self.cooking_controller.disable_auto_warm()
    
    async def stop_cooking(self):
        await self.cooking_controller.stop_cooking()
    
    def _get_delayed_start_parameters(self) -> Any:
        # Заменим вызов защищенного метода на публичный
        return self.cooking_controller.get_delayed_start_parameters()
    
    async def start_delayed(self):
        await self.cooking_controller.start_delayed()

    async def set_target_temp(self, target_temp: int) -> None:
        await self.cooking_controller.set_target_temp(target_temp)
    
    def _get_program_parameters(self, program_name: str) -> Any:
        # Заменим вызов защищенного метода на публичный
        return self.cooking_controller.get_program_parameters(program_name)
    
    async def set_target_program(self, program_name: str) -> None:
        await self.cooking_controller.set_target_program(program_name)


class DisposedError(Exception):
    pass