#!/usr/bin/env python3
# coding: utf-8

"""
Основной класс для работы с мультиваркой SkyCooker.
"""

import asyncio

from .skycooker_connection import SkyCookerConnection
from .const import PROGRAM_DATA, TARGET_TEMP_STEP
from .logger import skycooker_logger as _LOGGER


class SkyCookerLibrary:
    """
    Основной класс для работы с мультиваркой SkyCooker.
    """
    
    def __init__(self, mac="DA:D8:9F:9E:0B:4C", key="0000000000000000", model="RMC-M40S"):
        """
        Инициализация библиотеки.
        
        Args:
            mac (str): MAC-адрес мультиварки (по умолчанию "DA:D8:9F:9E:0B:4C").
            key (str): Ключ аутентификации для мультиварки (по умолчанию "0000000000000000").
            model (str): Модель мультиварки (по умолчанию "RMC-M40S").
        """
        self.mac = mac
        self.key = key
        self.model = model
        self.connection = None
        
    async def connect(self):
        """
        Установка соединения с мультиваркой.
        """
        try:
            self.connection = SkyCookerConnection(mac=self.mac, key=self.key, model=self.model)
            await self.connection._connect_if_need()
            _LOGGER.info("Соединение с мультиваркой установлено")
            return True
        except Exception as e:
            _LOGGER.error("Ошибка подключения: %s", e)
            return False

    async def disconnect(self):
        """Разрыв соединения с мультиваркой."""
        if self.connection:
            await self.connection.disconnect()
            _LOGGER.info("Соединение с мультиваркой разорвано")

    async def check_connection(self):
        """Проверка подключения к мультиварке."""
        try:
            if not self.connection:
                await self.connect()
            return self.connection._client and self.connection._client.is_connected and self.connection._auth_ok
        except Exception as e:
            _LOGGER.error("Ошибка проверки подключения: %s", e)
            return False

    async def sync_time(self):
        """Синхронизация времени с мультиваркой."""
        try:
            if not await self.check_connection():
                return False
            await self.connection.sync_time()
            _LOGGER.info("Время синхронизировано")
            return True
        except Exception as e:
            _LOGGER.error("Ошибка синхронизации времени: %s", e)
            return False

    async def get_time(self):
        """Получение времени от мультиварки."""
        try:
            if not await self.check_connection():
                return None
            t, offset = await self.connection.get_time()
            _LOGGER.info("Время мультиварки: %s, смещение: %s", t, offset)
            return t, offset
        except Exception as e:
            _LOGGER.error("Ошибка получения времени: %s", e)
            return None

    async def get_version(self):
        """Получение версии от мультиварки."""
        try:
            if not await self.check_connection():
                return None
            version = await self.connection.get_version()
            _LOGGER.info("Версия мультиварки: %s", version)
            return version
        except Exception as e:
            _LOGGER.error("Ошибка получения версии: %s", e)
            return None

    async def get_status(self):
        """Получение статуса от мультиварки."""
        try:
            if not await self.check_connection():
                return None
            status = await self.connection.get_status()
            _LOGGER.info(
                "Статус мультиварки: mode=%s, target_temp=%s, hours=%s, minutes=%s, "
                "remaining_hours=%s, remaining_minutes=%s, auto_warm=%s, status=%s",
                status.mode, status.target_temp, status.hours, status.minutes,
                status.remaining_hours, status.remaining_minutes, status.auto_warm, status.status
            )
            return status
        except Exception as e:
            _LOGGER.error("Ошибка получения статуса: %s", e)
            return None

    async def turn_on(self):
        """Включение мультиварки."""
        try:
            if not await self.check_connection():
                return False
            await self.connection.turn_on()
            _LOGGER.info("Мультиварка включена")
            return True
        except Exception as e:
            _LOGGER.error("Ошибка включения мультиварки: %s", e)
            return False

    async def turn_off(self):
        """Выключение мультиварки."""
        try:
            if not await self.check_connection():
                return False
            await self.connection.turn_off()
            _LOGGER.info("Мультиварка выключена")
            return True
        except Exception as e:
            _LOGGER.error("Ошибка выключения мультиварки: %s", e)
            return False

    async def set_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0):
        """Выбор и запуск режима."""
        try:
            if not await self.check_connection():
                return False
            if target_temp == 0 or target_temp is None:
                model_type = self.connection.model_id
                if model_type and model_type in PROGRAM_DATA and mode < len(PROGRAM_DATA[model_type]):
                    target_temp = PROGRAM_DATA[model_type][mode]["temperature"]
            if target_temp != 0:
                target_temp = round(target_temp / TARGET_TEMP_STEP) * TARGET_TEMP_STEP
            await self.connection.select_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            await self.connection.set_main_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            _LOGGER.info(
                "Режим установлен: mode=%s, subprog=%s, target_temp=%s, hours=%s, minutes=%s, dhours=%s, dminutes=%s, heat=%s",
                mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat
            )
            return True
        except Exception as e:
            _LOGGER.error("Ошибка установки режима: %s", e)
            return False

    async def set_mode_default(self, mode):
        """Выбор и запуск режима с параметрами по умолчанию."""
        try:
            if not await self.check_connection():
                return False
            model_type = self.connection.model_id
            if model_type and model_type in PROGRAM_DATA and mode < len(PROGRAM_DATA[model_type]):
                mode_data = PROGRAM_DATA[model_type][mode]
                target_temp = mode_data["temperature"]
                hours = mode_data["hours"]
                minutes = mode_data["minutes"]
            else:
                target_temp = 0
                hours = 0
                minutes = 0
            if hours == 0 and minutes == 0:
                minutes = 1
            if target_temp != 0:
                target_temp = round(target_temp / TARGET_TEMP_STEP) * TARGET_TEMP_STEP
            await self.connection.select_program(mode, 0, target_temp, hours, minutes)
            await self.connection.set_main_program(mode, 0, target_temp, hours, minutes)
            _LOGGER.info(
                "Режим установлен с параметрами по умолчанию: mode=%s, target_temp=%s, hours=%s, minutes=%s",
                mode, target_temp, hours, minutes
            )
            return True
        except Exception as e:
            _LOGGER.error("Ошибка установки режима с параметрами по умолчанию: %s", e)
            return False

    async def set_delayed_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0):
        """Выбор и запуск режима с отложенным временем."""
        try:
            if not await self.check_connection():
                return False
            if target_temp == 0 or target_temp is None:
                model_type = self.connection.model_id
                if model_type and model_type in PROGRAM_DATA and mode < len(PROGRAM_DATA[model_type]):
                    target_temp = PROGRAM_DATA[model_type][mode]["temperature"]
            if target_temp != 0:
                target_temp = round(target_temp / TARGET_TEMP_STEP) * TARGET_TEMP_STEP
            await self.connection.select_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            await self.connection.set_main_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            _LOGGER.info(
                "Режим с отложенным временем установлен: mode=%s, subprog=%s, target_temp=%s, hours=%s, minutes=%s, dhours=%s, dminutes=%s, heat=%s",
                mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat
            )
            return True
        except Exception as e:
            _LOGGER.error("Ошибка установки режима с отложенным временем: %s", e)
            return False