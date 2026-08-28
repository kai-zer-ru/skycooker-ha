#!/usr/bin/env python3
# coding: utf-8

"""
Основной класс для работы с мультиваркой SkyCooker.
"""

import asyncio
import math

from .skycooker_connection import SkyCookerConnection
from .const import MODE_DATA, TARGET_TEMP_STEP
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
            _LOGGER.info("✅ Соединение с мультиваркой установлено")
            return True
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка подключения: {e}")
            return False
    
    async def disconnect(self):
        """
        Разрыв соединения с мультиваркой.
        """
        if self.connection:
            await self.connection.disconnect()
            _LOGGER.info("🔌 Соединение с мультиваркой разорвано")
    
    async def check_connection(self):
        """
        Проверка подключения к мультиварке.
        """
        try:
            if not self.connection:
                await self.connect()
            return self.connection._client and self.connection._client.is_connected and self.connection._auth_ok
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка проверки подключения: {e}")
            return False
    
    async def sync_time(self):
        """
        Синхронизация времени с мультиваркой.
        """
        try:
            if not await self.check_connection():
                return False
            await self.connection.sync_time()
            _LOGGER.info("✅ Время синхронизировано")
            return True
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка синхронизации времени: {e}")
            return False
    
    async def get_time(self):
        """
        Получение времени от мультиварки.
        """
        try:
            if not await self.check_connection():
                return None
            t, offset = await self.connection.get_time()
            _LOGGER.info(f"⏰ Время мультиварки: {t}, смещение: {offset}")
            return t, offset
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка получения времени: {e}")
            return None
    
    async def get_version(self):
        """
        Получение версии от мультиварки.
        """
        try:
            if not await self.check_connection():
                return None
            version = await self.connection.get_version()
            _LOGGER.info(f"📋 Версия мультиварки: {version}")
            return version
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка получения версии: {e}")
            return None
    
    async def get_status(self):
        """
        Получение статуса от мультиварки.
        """
        try:
            if not await self.check_connection():
                return None
            status = await self.connection.get_status()
            _LOGGER.info(f"📊 Статус мультиварки: mode={status.mode}, target_temp={status.target_temperature}, hours={status.hours}, minutes={status.minutes}, remaining_hours={status.remaining_hours}, remaining_minutes={status.remaining_minutes}, auto_warm={status.auto_warm}, status={status.status}")
            return status
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка получения статуса: {e}")
            return None
    
    async def turn_on(self):
        """
        Включение мультиварки.
        """
        try:
            if not await self.check_connection():
                return False
            await self.connection.turn_on()
            _LOGGER.info("✅ Мультиварка включена")
            return True
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка включения мультиварки: {e}")
            return False
    
    async def turn_off(self):
        """
        Выключение мультиварки.
        """
        try:
            if not await self.check_connection():
                return False
            await self.connection.turn_off()
            _LOGGER.info("✅ Мультиварка выключена")
            return True
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка выключения мультиварки: {e}")
            return False
    
    async def set_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0):
        """
        Выбор и запуск режима.
        
        Args:
            mode (int): Режим работы мультиварки.
            subprog (int): Подрежим.
            target_temp (int): Целевая температура.
            hours (int): Часы.
            minutes (int): Минуты.
            dhours (int): Часы задержки.
            dminutes (int): Минуты задержки.
            heat (int): Нагрев.
        """
        try:
            if not await self.check_connection():
                return False
            # Если температура не указана (0 или None), берем значение из констант
            if target_temp == 0 or target_temp is None:
                model_type = self.connection.model_id
                if model_type and model_type in MODE_DATA and mode < len(MODE_DATA[model_type]):
                    target_temp = MODE_DATA[model_type][mode][0]
            # Округляем целевую температуру до ближайшего значения, кратного TARGET_TEMP_STEP
            if target_temp != 0:
                target_temp = round(target_temp / TARGET_TEMP_STEP) * TARGET_TEMP_STEP
            # Отправляем команду "Выбор режима" перед установкой режима
            await self.connection.select_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            await self.connection.set_main_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            _LOGGER.info(f"✅ Режим установлен: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}")
            return True
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка установки режима: {e}")
            return False

    async def set_mode_default(self, mode):
        """
        Выбор и запуск режима с параметрами по умолчанию.
        
        Args:
            mode (int): Режим работы мультиварки.
        """
        try:
            if not await self.check_connection():
                return False
            # Получаем параметры по умолчанию для указанного режима
            model_type = self.connection.model_id
            if model_type and model_type in MODE_DATA and mode < len(MODE_DATA[model_type]):
                mode_data = MODE_DATA[model_type][mode]
                target_temp = mode_data[0]
                hours = mode_data[1]
                minutes = mode_data[2]
            else:
                target_temp = 0
                hours = 0
                minutes = 0
            # Проверяем, что если часы равны 0, то минуты должны быть больше 0
            if hours == 0 and minutes == 0:
                minutes = 1
            # Округляем целевую температуру до ближайшего значения, кратного TARGET_TEMP_STEP
            if target_temp != 0:
                target_temp = round(target_temp / TARGET_TEMP_STEP) * TARGET_TEMP_STEP
            # Отправляем команду "Выбор режима" перед установкой режима
            await self.connection.select_program(mode, 0, target_temp, hours, minutes)
            await self.connection.set_main_program(mode, 0, target_temp, hours, minutes)
            _LOGGER.info(f"✅ Режим установлен с параметрами по умолчанию: mode={mode}, subprog=0, target_temp={target_temp}, hours={hours}, minutes={minutes}")
            return True
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка установки режима с параметрами по умолчанию: {e}")
            return False
    
    async def set_delayed_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0):
        """
        Выбор и запуск режима с отложенным временем.
        
        Args:
            mode (int): Режим работы мультиварки.
            subprog (int): Подрежим.
            target_temp (int): Целевая температура.
            hours (int): Часы.
            minutes (int): Минуты.
            dhours (int): Часы задержки.
            dminutes (int): Минуты задержки.
            heat (int): Нагрев.
        """
        try:
            if not await self.check_connection():
                return False
            # Если температура не указана (0 или None), берем значение из констант
            if target_temp == 0 or target_temp is None:
                model_type = self.connection.model_id
                if model_type and model_type in MODE_DATA and mode < len(MODE_DATA[model_type]):
                    target_temp = MODE_DATA[model_type][mode][0]
            # Округляем целевую температуру до ближайшего значения, кратного TARGET_TEMP_STEP
            if target_temp != 0:
                target_temp = round(target_temp / TARGET_TEMP_STEP) * TARGET_TEMP_STEP
            # Отправляем команду "Выбор режима" перед установкой режима
            await self.connection.select_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            # Установка режима
            await self.connection.set_main_program(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
            # В этой версии библиотеки отложенный запуск не реализован,
            # так как требует BLE-соединения.
            _LOGGER.info(f"✅ Режим с отложенным временем установлен: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}")
            return True
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка установки режима с отложенным временем: {e}")
            return False