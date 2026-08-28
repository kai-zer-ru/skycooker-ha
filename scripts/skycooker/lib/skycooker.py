#!/usr/bin/env python3
# coding: utf-8

"""
Основной класс для работы с мультиваркой SkyCooker.
"""

import asyncio
import calendar
import time
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime
from struct import pack, unpack

from .const import (
    COMMAND_AUTH,
    COMMAND_GET_STATUS,
    COMMAND_GET_VERSION,
    COMMAND_SELECT_PROGRAM,
    COMMAND_SET_MAIN_MODE,
    COMMAND_SYNC_TIME,
    COMMAND_GET_TIME,
    COMMAND_TURN_OFF,
    COMMAND_TURN_ON,
    MODEL_3,
    MODE_DATA,
    MODELS,
    PROGRAM_DATA,
)
from .logger import skycooker_logger as _LOGGER


def is_subprogram_supported(model_id) -> bool:
    """True if model supports subprograms (same logic as integration)."""
    return model_id is not None and model_id != MODEL_3


class SkyCookerError(Exception):
    pass


class AuthError(Exception):
    pass


class DisposedError(Exception):
    pass


class SkyCooker(ABC):
    """
    Базовый класс для работы с мультиваркой SkyCooker.
    """
    
    Status = namedtuple("Status", ["mode", "subprog", "target_temp", "hours", "minutes", "remaining_hours", "remaining_minutes", "auto_warm", "status"])
    
    def __init__(self, model):
        _LOGGER.info(f"SkyCooker model: {model}")
        self.model = model
        self.model_code = self.get_model_code(model)
        if not self.model_code:
            raise SkyCookerError("Unknown SkyCooker model")
    
    @staticmethod
    def get_model_code(model):
        if model in MODELS:
            return MODELS[model]
        if model.endswith("-E"):
            return MODELS.get(model[:-2], None)
        return None
    
    @abstractmethod
    async def command(self, command, params=None):
        pass
    
    async def auth(self, key):
        # Преобразуем ключ в байты
        key_bytes = bytes.fromhex(key) if isinstance(key, str) else key
        r = await self.command(COMMAND_AUTH, key_bytes)
        ok = r[0] != 0
        _LOGGER.debug(f"Auth: ok={ok}")
        return ok
    
    async def get_version(self):
        r = await self.command(COMMAND_GET_VERSION)
        major, minor = unpack("BB", r)
        ver = f"{major}.{minor}"
        _LOGGER.debug(f"Version: {ver}")
        return major, minor
    
    async def turn_on(self):
        r = await self.command(COMMAND_TURN_ON)
        if r[0] != 1: raise SkyCookerError("can't turn on")
        _LOGGER.debug(f"Turned on")
    
    async def turn_off(self):
        r = await self.command(COMMAND_TURN_OFF)
        if r[0] != 1: raise SkyCookerError("can't turn off")
        _LOGGER.debug(f"Turned off")
    
    async def select_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0, bit_flags=0):
            program_data = PROGRAM_DATA.get(self.model_code, [])
            if mode < len(program_data) and bit_flags == 0:
                bit_flags = program_data[mode]["byte_flag"]
            if is_subprogram_supported(self.model_code):
                data = pack("BBBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes),
                            int(dhours), int(dminutes), int(heat), int(bit_flags))
            else:
                data = pack("BBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes), int(dhours), int(dminutes), int(heat))

            r = await self.command(COMMAND_SELECT_PROGRAM, list(data))
            if r[0] != 1: raise SkyCookerError("can't select mode")
            _LOGGER.debug(f"Mode selected: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}, bit_flags={bit_flags}")

    async def set_main_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0, bit_flags=0):
            program_data = PROGRAM_DATA.get(self.model_code, [])
            if mode < len(program_data) and bit_flags == 0:
                bit_flags = program_data[mode]["byte_flag"]
            if is_subprogram_supported(self.model_code):
                data = pack("BBBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes),
                            int(dhours), int(dminutes), int(heat), int(bit_flags))
            else:
                data = pack("BBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes), int(dhours), int(dminutes), int(heat))

            r = await self.command(COMMAND_SET_MAIN_MODE, list(data))
            if r[0] != 1: raise SkyCookerError("can't set mode")
            _LOGGER.debug(f"Mode set: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}, bit_flags={bit_flags}")
    
    async def get_status(self):
        r = await self.command(COMMAND_GET_STATUS)
        # Parse the status data according to the correct format
        mode = r[0]
        subprog = r[1]
        target_temp = r[2]
        hours = r[3]
        minutes = r[4]
        remaining_hours = r[5]
        remaining_minutes = r[6]
        auto_warm = r[7]
        status = r[8]
        
        status = SkyCooker.Status(mode, subprog, target_temp, hours, minutes, remaining_hours, remaining_minutes, auto_warm, status)
        _LOGGER.debug(f"Status: mode={status.mode}, subprog={status.subprog}, target_temp={status.target_temp}, hours={status.hours}, minutes={status.minutes}, remaining_hours={status.remaining_hours}, remaining_minutes={status.remaining_minutes}, auto_warm={status.auto_warm}, status={status.status}")
        return status
    
    async def sync_time(self):
        try:
            t = time.localtime()
            offset = calendar.timegm(t) - calendar.timegm(time.gmtime(time.mktime(t)))
            now = int(time.time())
            data = pack("<ii", now, offset)
            _LOGGER.debug("Синхронизация времени: time=%s, offset=%s", now, offset)
            r = await self.command(COMMAND_SYNC_TIME, data)
            if r[0] != 0:
                _LOGGER.warning("Не удалось синхронизировать время. Код ответа: %s", r[0])
                return
            _LOGGER.debug(
                "Время синхронизировано: %s (%s), offset=%s (GMT%+.2f)",
                now, datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S'), offset, offset / 60 / 60
            )
        except Exception as e:
            _LOGGER.warning("Ошибка синхронизации времени: %s", e)
    
    async def get_time(self):
        r = await self.command(COMMAND_GET_TIME)
        t, offset = unpack("<ii", r)
        _LOGGER.debug(f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
        return t, offset