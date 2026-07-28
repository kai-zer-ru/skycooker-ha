#!/usr/local/bin/python3
# coding: utf-8

import logging
from abc import ABC, abstractmethod
from struct import pack, unpack
from typing import Optional, Union, List

from .const import *
from .programs import is_subprogram_supported

_LOGGER = logging.getLogger(__name__)


class SkyCookerError(Exception):
    """Пользовательское исключение для ошибок SkyCooker."""
    pass


class SkyCooker(ABC):
    """Абстрактный базовый класс для устройств SkyCooker."""

    def __init__(self, hass, model_name: str):
        """Инициализация SkyCooker с заданной моделью.
        
        Args:
            model_name: Название модели устройства SkyCooker.
            
        Raises:
            SkyCookerError: Если модель неизвестна.
        """
        _LOGGER.debug(f"SkyCooker model: {model_name}")
        self.hass = hass
        self.model_name = model_name
        self.model_id = self.get_model_id(model_name)
        if not self.model_id:
            raise SkyCookerError("Unknown SkyCooker model")

    @staticmethod
    def get_model_id(model_name: str) -> Optional[int]:
        """Получение кода модели для заданного названия модели.
        
        Args:
            model_name: Название модели.
            
        Returns:
            Код модели, если найден, иначе None.
        """
        if model_name in MODELS:
            return MODELS[model_name]
        if model_name.endswith("-E"):
            return MODELS.get(model_name[:-2], None)
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

    async def select_program(self, program_id: int, subprog: int = 0) -> None:
        """Выбор программы и подпрограммы для устройства SkyCooker.
        
        Args:
            program_id: Программа для выбора.
            subprog: Подпрограмма для выбора (по умолчанию 0).
            
        Raises:
            SkyCookerError: Если выбор программ не удался.
        """
        # Для MODEL_3 отправляем только mode (1 байт), для остальных - mode и subprog (2 байта)
        if is_subprogram_supported(self.model_id):
            data = pack("BB", int(program_id), int(subprog))
            _LOGGER.debug("Отправка команды SELECT_MODE (0x09) с данными: %s", data.hex().upper())
            _LOGGER.debug("Параметры: mode=%s, subprog=%s", program_id, subprog)
        else:
            data = pack("B", int(program_id))
            _LOGGER.debug("Отправка команды SELECT_MODE (0x09) для MODEL_3 с данными: %s", data.hex().upper())
            _LOGGER.debug("Параметры: mode=%s", program_id)

        try:
            r = await self.command(COMMAND_SELECT_PROGRAM, list(data))
            _LOGGER.debug("Получен ответ на SELECT_MODE: %s", r.hex().upper() if r else 'None')
            if r and len(r) > 0:
                _LOGGER.debug("Первый байт ответа: %s (ожидалось 1 для успеха)", r[0])
            # Accept both success code (0x01) and status updates as success
            if r and r[0] != 1 and len(r) != 1:
                _LOGGER.error("Ошибка выбора режима: устройство вернуло код ошибки %s", r[0])
                raise SkyCookerError(f"Ошибка выбора режима: код {r[0]}")
            _LOGGER.debug("Режим успешно выбран: mode=%s", program_id)
        except Exception as e:
            _LOGGER.error("Исключение при выборе режима: %s", e)
            raise SkyCookerError(f"Исключение при выборе режима: {e}")

    async def set_main_program(
            self,
            program_id: int,
            subprogram_id: int = 0,
            target_temperature: int = 0,
            target_main_hours: int = 0,
            target_main_minutes: int = 0,
            target_additional_hours: int = 0,
            target_additional_minutes: int = 0,
            auto_warm: int = 0,
            bit_flags: int = 0
    ) -> None:
        """Установка основного программы и параметров для устройства SkyCooker.
        
        Args:
            program_id: программа для установки.
            subprogram_id: Подпрограмма для установки (по умолчанию 0).
            target_temperature: Целевая температура (по умолчанию 0).
            target_main_hours: Целевые часы (по умолчанию 0).
            target_main_minutes: Целевые минуты (по умолчанию 0).
            target_additional_hours: Целевые дополнительные часы (по умолчанию 0).
            target_additional_minutes: Целевые дополнительные минуты (по умолчанию 0).
            auto_warm: Настройка автоподогрева (по умолчанию 0).
            bit_flags: Битовые флаги для настроек программ (по умолчанию 0).
            
        Raises:
            SkyCookerError: Если установка программы не удалась.
        """
        # В текущей реализации битовые флаги берутся из MODE_DATA_NEW
        # Для MODEL_3 битовые флаги не добавляются
        # В будущем, когда будет понятно, как использовать битовые флаги, этот код будет обновлен
        # Параметр auto_warm используется для передачи флага автоподогрева
        if is_subprogram_supported(self.model_id):
            program_data = PROGRAM_DATA.get(self.model_id, [])
            if program_id < len(program_data) and bit_flags == 0:
                bit_flags = program_data[program_id]["byte_flag"]
            data = pack(
                "BBBBBBBBB",
                int(program_id), int(subprogram_id), int(target_temperature), int(target_main_hours),
                int(target_main_minutes), int(target_additional_hours),
                int(target_additional_minutes), int(auto_warm), int(bit_flags)
            )
        else:
            subprogram_id = 0
            # Для MODEL_3 используем auto_warm как флаг автоподогрева
            data = pack(
                "BBBBBBBB",
                int(program_id), int(subprogram_id), int(target_temperature), int(target_main_hours),
                int(target_main_minutes), int(target_additional_hours),
                int(target_additional_minutes), int(auto_warm)
            )
        _LOGGER.debug("Отправка команды SET_MAIN_MODE (0x05) с данными: %s", data.hex().upper())
        _LOGGER.debug(
            "Параметры: mode=%s, subprog=%s, target_temp=%s, target_main_hours=%s, target_main_minutes=%s, "
            "target_additional_hours=%s, target_additional_minutes=%s, auto_warm=%s, bit_flags=%s",
            program_id, subprogram_id, target_temperature, target_main_hours, target_main_minutes,
            target_additional_hours, target_additional_minutes, auto_warm, bit_flags
        )

        try:
            r = await self.command(COMMAND_SET_MAIN_MODE, list(data))
            _LOGGER.debug("Получен ответ на SET_MAIN_MODE: %s", r.hex().upper() if r else 'None')
            if r and len(r) > 0:
                _LOGGER.debug("Первый байт ответа: %s (ожидалось 1 для успеха)", r[0])
            # Accept both success code (0x01) and status updates as success
            if r and r[0] != 1 and len(r) != 1:
                _LOGGER.error("Ошибка установки режима: устройство вернуло код ошибки %s", r[0])
                raise SkyCookerError(f"Ошибка установки режима: код {r[0]}")
            _LOGGER.debug("Режим успешно установлен: mode=%s", program_id)
        except Exception as e:
            _LOGGER.error("Исключение при установке режима: %s", e)
            raise SkyCookerError(f"Исключение при установке режима: {e}")
