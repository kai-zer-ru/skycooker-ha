"""Утилиты для работы со временем в SkyCooker."""

import calendar
import logging
import time
from datetime import datetime
from struct import pack, unpack
from typing import Any, List, Optional, Tuple
from .const import COMMAND_SYNC_TIME, COMMAND_GET_TIME, STATUS_DELAYED_LAUNCH, \
    STATUS_WARMING, STATUS_COOKING, STATUS_AUTO_WARM, STATUS_WAIT_PRODUCT, Status
from .utils import get_localized_string

_LOGGER = logging.getLogger(__name__)


def _validate_hours(hours: int) -> int:
    """Валидация часов. Часы не могут быть больше 23."""
    return min(hours, 23)


def _validate_minutes(minutes: int) -> int:
    """Валидация минут. Минуты не могут быть больше 59."""
    return min(minutes, 59)


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
        _LOGGER.debug("Синхронизация времени: time=%s, offset=%s", now, offset)
        r = await self.command(COMMAND_SYNC_TIME, data)
        if r[0] != 0:
            _LOGGER.warning("Не удалось синхронизировать время. Код ответа: %s", r[0])
            return
        _LOGGER.debug(
            "Время синхронизировано: %s (%s), offset=%s (GMT%+.2f)",
            now, datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S'),
            offset, offset / 60 / 60
        )
    except Exception as e:
        _LOGGER.warning("Ошибка синхронизации времени: %s", e)


async def get_time(self) -> Tuple[int, int]:
    """Получение текущего времени с устройства SkyCooker.
    
    Returns:
        Кортеж, содержащий временную метку и смещение часового пояса.
    """
    r = await self.command(COMMAND_GET_TIME)
    t, offset = unpack("<ii", r)
    _LOGGER.debug(
        f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), "
        f"offset={offset} (GMT{offset / 60 / 60:+.2f})"
    )
    return t, offset


def _get_time_str(hours: int, minutes: int, hass: Any) -> str:
    """Форматирует строку времени в зависимости от языка."""
    if hours < 0:
        hours = 0
    if minutes < 0:
        minutes = 0
    return get_localized_string(hass, f"{hours} h. {minutes} m.", f"{hours} ч. {minutes} м.")


def format_time(hass: Any, hours: int, minutes: int) -> str:
    """Форматирует время в зависимости от языка."""
    return _get_time_str(hours, minutes, hass)


def get_time_options(hours: bool = True) -> List[str]:
    """Возвращает список опций для времени."""
    return [str(i) for i in range(0, 24)] if hours else [str(i) for i in range(0, 60)]


def get_time_from_status(skycooker: Any, status: Optional[Status], attr_name: str, default: int = 0) -> int:
    """Возвращает значение времени из статуса или соединения."""
    if status and isinstance(status, Status) and hasattr(status, attr_name):
        return getattr(status, attr_name)
    return getattr(skycooker, attr_name, default) if hasattr(skycooker, attr_name) else default


def _normalize_time(hours: int, minutes: int) -> tuple[int, int]:
    """Нормализует время, обеспечивая, чтобы часы не превышали 23, а минуты - 59."""
    if minutes >= 60:
        hours += minutes // 60
        minutes = minutes % 60
    if hours > 23:
        hours = 23
    return hours, minutes


def calculate_remaining_time(hass: Any, skycooker: Any, status_code: int) -> str:
    """Рассчитывает оставшееся время в зависимости от статуса."""
    if status_code == STATUS_DELAYED_LAUNCH:
        # Для отложенного старта: target_main + target_additional
        boil_hours = get_time_from_status(skycooker, skycooker.status, 'target_main_hours')
        boil_minutes = get_time_from_status(skycooker, skycooker.status, 'target_main_minutes')
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        total_hours = boil_hours + additional_hours
        total_minutes = boil_minutes + additional_minutes
        total_hours, total_minutes = _normalize_time(total_hours, total_minutes)
    elif status_code in [STATUS_WARMING, STATUS_COOKING]:
        # Для разогрева и готовки: только target_additional
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        total_hours, total_minutes = _normalize_time(additional_hours, additional_minutes)
    elif status_code == STATUS_WAIT_PRODUCT:
        # Ожидание загрузки продуктов: отсчёт ещё не начался, показываем заданное время варки
        boil_hours = get_time_from_status(skycooker, skycooker.status, 'target_main_hours')
        boil_minutes = get_time_from_status(skycooker, skycooker.status, 'target_main_minutes')
        total_hours, total_minutes = _normalize_time(boil_hours, boil_minutes)
    else:
        total_hours = 0
        total_minutes = 0

    return format_time(hass, total_hours, total_minutes)


def get_cooking_time(hass: Any, skycooker: Any, status_code: int) -> str:
    """Возвращает время приготовления."""
    if status_code in [STATUS_DELAYED_LAUNCH, STATUS_WARMING, STATUS_COOKING, STATUS_WAIT_PRODUCT]:
        boil_hours = get_time_from_status(skycooker, skycooker.status, 'target_main_hours')
        boil_minutes = get_time_from_status(skycooker, skycooker.status, 'target_main_minutes')
        return format_time(hass, boil_hours, boil_minutes)
    return format_time(hass, 0, 0)


def get_auto_warm_time(hass: Any, skycooker: Any, status_code: int) -> str:
    """Возвращает время автоподогрева."""
    if status_code == STATUS_AUTO_WARM:
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        return format_time(hass, additional_hours, additional_minutes)
    return format_time(hass, 0, 0)


def get_delayed_launch_time(hass: Any, skycooker: Any, status_code: int) -> str:
    """Возвращает время до отложенного старта."""
    if status_code == STATUS_DELAYED_LAUNCH:
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        return format_time(hass, additional_hours, additional_minutes)
    return format_time(hass, 0, 0)
