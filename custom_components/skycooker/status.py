"""Модуль для работы со статусом SkyCooker."""

from typing import Optional, Any
import logging

from .const import COMMAND_GET_STATUS, STATUS_CODE_TO_TRANSLATION_KEY, Status
from .programs import get_program_name
from .skycooker import SkyCookerError
from .utils import get_localized_string

_LOGGER = logging.getLogger(__name__)

def get_status_text(hass: Any, status_code: Optional[int]) -> str:
    """Возвращает текст статуса в зависимости от языка."""
    if status_code is None:
        return get_localized_string(hass, "Unknown", "Неизвестно")
    
    # Получение ключа перевода для кода статуса
    translation_key = STATUS_CODE_TO_TRANSLATION_KEY.get(status_code)
    
    if translation_key:
        # Получение переводов из данных hass
        translations = hass.data.get("skycooker_translations", {})
        status_codes = translations.get("status_codes", {})
        
        # Если переводы доступны, используем их
        if status_codes:
            return status_codes.get(translation_key, translation_key)
        else:
            # Резервные значения для тестирования или резервного копирования
            fallback_translations = {
                "off": get_localized_string(hass, "Off", "Выключена"),
                "wait": get_localized_string(hass, "Waiting", "Ожидание"),
                "delayed_launch": get_localized_string(hass, "Delayed Launch", "Отложенный старт"),
                "warming": get_localized_string(hass, "Warming", "Разогрев"),
                "cooking": get_localized_string(hass, "Cooking", "Готовка"),
                "auto_warm": get_localized_string(hass, "Auto Warm", "Подогрев"),
                "full_off": get_localized_string(hass, "Fully off", "Полностью выключена"),
            }
            return fallback_translations.get(translation_key, translation_key)
    else:
        # Резервное значение для неизвестных кодов статусов
        return get_localized_string(hass, f"Unknown ({status_code})", f"Неизвестно ({status_code})")


async def get_status(connection_manager) -> Status:
    """Получение текущего статуса устройства SkyCooker.

    Returns:
        Текущий статус в виде именованного кортежа Status.

    Raises:
        SkyCookerError: Если данные статуса некорректны или не могут быть разобраны.
    """
    r = await connection_manager.command(COMMAND_GET_STATUS)
    _LOGGER.debug(f"Raw status data: {r.hex().upper()}, length: {len(r)}")
    if len(r) < 16:
        _LOGGER.error(f"❌ Ошибка: получено {len(r)} байт вместо ожидаемых 16")
        raise SkyCookerError(f"Некорректный размер данных статуса: {len(r)} байт")
    try:
        # Parse the 16-byte status response according to the new format
        # Format: program_id(1), subprogram_id(1), target_temperature(1), target_main_hours(1), target_main_minutes(1),
        #         target_additional_hours(1), target_additional_minutes(1), auto_warm(1), status(1), ...
        program_id = r[0]
        subprogram_id = r[1]
        target_temperature = r[2]
        target_main_hours = r[3]
        target_main_minutes = r[4]
        target_additional_hours = r[5]
        target_additional_minutes = r[6]
        auto_warm = r[7]
        status = r[8]
        is_on = r[8] != 0
        sound_enabled = r[9] != 0
        program_name = get_program_name(connection_manager.hass, program_id, connection_manager.model_id)
        status_data = Status(
            program_id=program_id,
            subprogram_id=subprogram_id,
            target_temperature=target_temperature,
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
            program_name=program_name
        )
    except Exception as e:
        _LOGGER.error(f"❌ Ошибка распаковки статуса: {e}")
        raise SkyCookerError(f"Ошибка распаковки статуса: {e}")

    _LOGGER.debug(
        f"Status: program_id={status_data.program_id}, subprogram_id={status_data.subprogram_id}, is_on={status_data.is_on}, "
        f"target_temperature={status_data.target_temperature}, "
        f"auto_warm={status_data.auto_warm}, sound_enabled={status_data.sound_enabled}, "
        f"target_main_hours={status_data.target_main_hours}, target_main_minutes={status_data.target_main_minutes}, "
        f"target_additional_hours={status_data.target_additional_hours}, target_additional_minutes={status_data.target_additional_minutes}, "
        f"current_status={status_data.status}, program_name={status_data.program_name}, "
    )
    return status_data
