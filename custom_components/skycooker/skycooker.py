#!/usr/local/bin/python3
# coding: utf-8

import calendar
import logging
import time
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime
from struct import pack, unpack
from typing import Optional, Tuple, Union, List

from .const import *

_LOGGER = logging.getLogger(__name__)


class SkyCookerError(Exception):
    """Пользовательское исключение для ошибок SkyCooker."""
    pass


class SkyCooker(ABC):
    """Абстрактный базовый класс для устройств SkyCooker."""
    
    Status = namedtuple(
        "Status", [
            "mode", "subprog", "target_temp", "auto_warm", "is_on",
            "sound_enabled", "parental_control", "error_code",
            "target_main_hours", "target_main_minutes",
            "target_additional_hours", "target_additional_minutes", "status"
        ]
    )

    def __init__(self, model: str):
        """Инициализация SkyCooker с заданной моделью.
        
        Args:
            model: Название модели устройства SkyCooker.
            
        Raises:
            SkyCookerError: Если модель неизвестна.
        """
        _LOGGER.debug(f"SkyCooker model: {model}")
        self.model = model
        self.model_code = self.get_model_code(model)
        if not self.model_code:
            raise SkyCookerError("Unknown SkyCooker model")

    @staticmethod
    def get_model_code(model: str) -> Optional[int]:
        """Получение кода модели для заданного названия модели.
        
        Args:
            model: Название модели.
            
        Returns:
            Код модели, если найден, иначе None.
        """
        if model in MODELS:
            return MODELS[model]
        if model.endswith("-E"):
            return MODELS.get(model[:-2], None)
        return None

    @abstractmethod
    async def command(self, command: int, params: Optional[Union[List[int], bytes]] = None) -> bytes:
        """Отправка команды устройству SkyCooker.
        
        Args:
            command: Код команды.
            params: Необязательные параметры для команды.
            
        Returns:
            Ответ от устройства.
        """
        pass

    async def auth(self, key: bytes) -> bool:
        """Аутентификация с устройством SkyCooker.
        
        Args:
            key: Ключ аутентификации.
            
        Returns:
            True, если аутентификация прошла успешно, False в противном случае.
        """
        r = await self.command(COMMAND_AUTH, key)
        ok = r[0] != 0
        _LOGGER.debug(f"Auth: ok={ok}")
        return ok

    async def get_version(self) -> str:
        """Получение версии устройства SkyCooker.
        
        Returns:
            Строка версии в формате "major.minor".
        """
        r = await self.command(COMMAND_GET_VERSION)
        major, minor = unpack("BB", r)
        ver = f"{major}.{minor}"
        _LOGGER.debug(f"Version: {ver}")
        return ver

    async def turn_on(self) -> None:
        """Включение устройства SkyCooker.
        
        Raises:
            SkyCookerError: Если устройство не может быть включено.
        """
        r = await self.command(COMMAND_TURN_ON)
        if r[0] != 1:
            raise SkyCookerError("can't turn on")
        _LOGGER.debug("Turned on")

    async def turn_off(self) -> None:
        """Выключение устройства SkyCooker.
        
        Raises:
            SkyCookerError: Если устройство не может быть выключено.
        """
        r = await self.command(COMMAND_TURN_OFF)
        if r[0] != 1:
            raise SkyCookerError("can't turn off")
        _LOGGER.debug("Turned off")

    async def select_mode(self, mode: int, subprog: int = 0) -> None:
        """Выбор режима и подпрограммы для устройства SkyCooker.
        
        Args:
            mode: Режим для выбора.
            subprog: Подпрограмма для выбора (по умолчанию 0).
            
        Raises:
            SkyCookerError: Если выбор режима не удался.
        """
        # Для MODEL_3 отправляем только mode (1 байт), для остальных - mode и subprog (2 байта)
        if self.model_code == MODEL_3:
            data = pack("B", int(mode))
            _LOGGER.debug(f"📤 Отправка команды SELECT_MODE (0x09) для MODEL_3 с данными: {data.hex().upper()}")
            _LOGGER.debug(f"   Параметры: mode={mode}")
        else:
            data = pack("BB", int(mode), int(subprog))
            _LOGGER.debug(f"📤 Отправка команды SELECT_MODE (0x09) с данными: {data.hex().upper()}")
            _LOGGER.debug(f"   Параметры: mode={mode}, subprog={subprog}")

        try:
            r = await self.command(COMMAND_SELECT_MODE, list(data))
            _LOGGER.debug(f"📥 Получен ответ на SELECT_MODE: {r.hex().upper() if r else 'None'}")
            if r and len(r) > 0:
                _LOGGER.debug(f"   Первый байт ответа: {r[0]} (ожидалось 1 для успеха)")
            # Accept both success code (0x01) and status updates as success
            if r and r[0] != 1 and len(r) != 1:
                _LOGGER.error(f"❌ Ошибка выбора режима: устройство вернуло код ошибки {r[0]}")
                raise SkyCookerError(f"Ошибка выбора режима: код {r[0]}")
            _LOGGER.debug(f"✅ Режим успешно выбран: mode={mode}")
        except Exception as e:
            _LOGGER.error(f"❌ Исключение при выборе режима: {e}")
            raise SkyCookerError(f"Исключение при выборе режима: {e}")

    async def set_main_mode(
        self,
        mode: int,
        subprog: int = 0,
        target_temp: int = 0,
        target_main_hours: int = 0,
        target_main_minutes: int = 0,
        target_additional_hours: int = 0,
        target_additional_minutes: int = 0,
        auto_warm: int = 0,
        bit_flags: int = 0
    ) -> None:
        """Установка основного режима и параметров для устройства SkyCooker.
        
        Args:
            mode: Режим для установки.
            subprog: Подпрограмма для установки (по умолчанию 0).
            target_temp: Целевая температура (по умолчанию 0).
            target_main_hours: Целевые часы (по умолчанию 0).
            target_main_minutes: Целевые минуты (по умолчанию 0).
            target_additional_hours: Целевые дополнительные часы (по умолчанию 0).
            target_additional_minutes: Целевые дополнительные минуты (по умолчанию 0).
            auto_warm: Настройка автоподогрева (по умолчанию 0).
            bit_flags: Битовые флаги для настроек режима (по умолчанию 0).
            
        Raises:
            SkyCookerError: Если установка режима не удалась.
        """
        # В текущей реализации битовые флаги берутся из MODE_DATA
        # Для MODEL_3 битовые флаги не добавляются
        # В будущем, когда будет понятно, как использовать битовые флаги, этот код будет обновлен
        # Параметр auto_warm используется для передачи флага автоподогрева
        if self.model_code == MODEL_3:
            # Для MODEL_3 используем auto_warm как флаг автоподогрева
            data = pack(
                "BBBBBBBB",
                int(mode), int(subprog), int(target_temp), int(target_main_hours),
                int(target_main_minutes), int(target_additional_hours),
                int(target_additional_minutes), int(auto_warm)
            )
        else:
            mode_data = MODE_DATA.get(self.model_code, [])
            if mode < len(mode_data) and bit_flags == 0:
                bit_flags = mode_data[mode][3]
            data = pack(
                "BBBBBBBBB",
                int(mode), int(subprog), int(target_temp), int(target_main_hours),
                int(target_main_minutes), int(target_additional_hours),
                int(target_additional_minutes), int(auto_warm), int(bit_flags)
            )

        _LOGGER.debug(f"📤 Отправка команды SET_MAIN_MODE (0x05) с данными: {data.hex().upper()}")
        _LOGGER.debug(
            f"   Параметры: mode={mode}, subprog={subprog}, target_temp={target_temp}, "
            f"target_main_hours={target_main_hours}, target_main_minutes={target_main_minutes}, "
            f"target_additional_hours={target_additional_hours}, target_additional_minutes={target_additional_minutes}, "
            f"auto_warm={auto_warm}, bit_flags={bit_flags}"
        )

        try:
            r = await self.command(COMMAND_SET_MAIN_MODE, list(data))
            _LOGGER.debug(f"📥 Получен ответ на SET_MAIN_MODE: {r.hex().upper() if r else 'None'}")
            if r and len(r) > 0:
                _LOGGER.debug(f"   Первый байт ответа: {r[0]} (ожидалось 1 для успеха)")
            # Accept both success code (0x01) and status updates as success
            if r and r[0] != 1 and len(r) != 1:
                _LOGGER.error(f"❌ Ошибка установки режима: устройство вернуло код ошибки {r[0]}")
                raise SkyCookerError(f"Ошибка установки режима: код {r[0]}")
            _LOGGER.debug(f"✅ Режим успешно установлен: mode={mode}")
        except Exception as e:
            _LOGGER.error(f"❌ Исключение при установке режима: {e}")
            raise SkyCookerError(f"Исключение при установке режима: {e}")

    async def get_status(self) -> Status:
        """Получение текущего статуса устройства SkyCooker.
        
        Returns:
            Текущий статус в виде именованного кортежа Status.
            
        Raises:
            SkyCookerError: Если данные статуса некорректны или не могут быть разобраны.
        """
        r = await self.command(COMMAND_GET_STATUS)
        _LOGGER.debug(f"Raw status data: {r.hex().upper()}, length: {len(r)}")
        if len(r) < 16:
            _LOGGER.error(f"❌ Ошибка: получено {len(r)} байт вместо ожидаемых 16")
            raise SkyCookerError(f"Некорректный размер данных статуса: {len(r)} байт")
        try:
            # Parse the 16-byte status response according to the new format
            # Format: mode(1), subprog(1), target_temp(1), target_main_hours(1), target_main_minutes(1),
            #         target_additional_hours(1), target_additional_minutes(1), auto_warm(1), status(1), ...
            mode = r[0]
            subprog = r[1]
            target_temp = r[2]
            target_main_hours = r[3]
            target_main_minutes = r[4]
            target_additional_hours = r[5]
            target_additional_minutes = r[6]
            auto_warm = r[7]
            status = r[8]
            is_on = r[8] != 0
            sound_enabled = r[9] != 0
            
            status = SkyCooker.Status(
                mode=mode,
                subprog=subprog,
                target_temp=target_temp,
                auto_warm=auto_warm,
                is_on=is_on,
                sound_enabled=sound_enabled,
                parental_control=False,
                error_code=0,
                target_main_hours=target_main_hours,
                target_main_minutes=target_main_minutes,
                target_additional_hours=target_additional_hours,
                target_additional_minutes=target_additional_minutes,
                status=status,
            )
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка распаковки статуса: {e}")
            raise SkyCookerError(f"Ошибка распаковки статуса: {e}")
          
        _LOGGER.debug(
            f"Status: mode={status.mode}, subprog={status.subprog}, is_on={status.is_on}, "
            f"target_temp={status.target_temp}, "
            f"auto_warm={status.auto_warm}, sound_enabled={status.sound_enabled}, "
            f"target_main_hours={status.target_main_hours}, target_main_minutes={status.target_main_minutes}, "
            f"target_additional_hours={status.target_additional_hours}, target_additional_minutes={status.target_additional_minutes}"
        )
        return status

    async def sync_time(self) -> None:
        """Синхронизация времени с устройством SkyCooker.
        
        Этот метод пытается синхронизировать время устройства с текущим системным временем.
        Если синхронизация не удается, выводится предупреждение, но исключение не выбрасывается.
        """
        try:
            t = time.localtime()
            offset = calendar.timegm(t) - calendar.timegm(time.gmtime(time.mktime(t)))
            now = int(time.time())
            data = pack("<ii", now, offset)
            _LOGGER.debug(f"🕒 Синхронизация времени: time={now}, offset={offset}")
            r = await self.command(COMMAND_SYNC_TIME, data)
            if r[0] != 0:
                _LOGGER.warning(f"⚠️  Не удалось синхронизировать время. Код ответа: {r[0]}")
                return
            _LOGGER.debug(
                f"✅ Время синхронизировано: {now} "
                f"({datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')}), "
                f"offset={offset} (GMT{offset/60/60:+.2f})"
            )
        except Exception as e:
            _LOGGER.warning(f"⚠️  Ошибка синхронизации времени: {e}")

    async def get_time(self) -> Tuple[int, int]:
        """Получение текущего времени с устройства SkyCooker.
        
        Returns:
            Кортеж, содержащий временную метку и смещение часового пояса.
        """
        r = await self.command(COMMAND_GET_TIME)
        t, offset = unpack("<ii", r)
        _LOGGER.debug(
            f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), "
            f"offset={offset} (GMT{offset/60/60:+.2f})"
        )
        return t, offset