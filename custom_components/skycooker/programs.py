"""Модуль для работы с режимами SkyCooker."""
import logging
from typing import Any, Dict, List, Optional

from .const import *
from .utils import get_localized_string

_LOGGER = logging.getLogger(__name__)


def _get_translations(hass: Any) -> dict:
    """Возвращает словарь переводов или пустой dict."""
    return hass.data.get("skycooker_translations", {}) if hass is not None else {}


def get_program_data(model_id: int, program_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает данные режима."""
    if model_id in PROGRAM_DATA and program_id < len(PROGRAM_DATA[model_id]):
        return PROGRAM_DATA[model_id][program_id]
    return None

def get_program_constants(model_id: int) -> List[str]:
    """Возвращает список констант режимов для указанной модели."""
    return PROGRAM_NAMES.get(model_id, [])


def get_program_options(hass, model_id: int, include_standby: bool = True) -> List[str]:
    """Возвращает список опций для режимов."""
    program_constants = get_program_constants(model_id)
    if not program_constants or hass is None:
        return []

    translations = _get_translations(hass)
    program_names = translations.get("program_names", {})
    if include_standby:
        programs = [program_names.get(PROGRAM_STANDBY, f"Unknown ({PROGRAM_STANDBY})")]
    else:
        programs = []

    # Добавляем режим ожидания в начало списка
    for program_constant in program_constants:
        if program_constant and program_constant != PROGRAM_NONE and program_constant != PROGRAM_STANDBY:
            programs.append(program_names.get(program_constant, f"Unknown ({program_constant})"))

    return programs

# option - текст в выбранном пункте селекта, а не число
def get_constant_by_name(hass, program_name: str, model_id: int) -> Optional[str]:
    program_id = find_program_id(hass, program_name, model_id)
    program_constants = get_program_constants(model_id)
    if not program_constants or program_id is None or program_id >= len(program_constants):
        return None
    
    return program_constants[program_id]

def get_program_name_by_const(hass, const_name: str, model_id: int) -> Optional[str]:
    program_id = find_program_id_by_const(hass, const_name, model_id)
    if program_id is None:
        return None
    return get_program_name(hass, program_id, model_id)

def get_standby_program_name(hass, model_id: int) -> Optional[str]:
    return get_program_name_by_const(hass, PROGRAM_STANDBY, model_id)

def _find_program_index(program_constants: List[str], target_constant: str) -> Optional[int]:
    """Возвращает индекс константы в списке режимов модели."""
    for idx, mc in enumerate(program_constants):
        if mc == target_constant:
            return idx
    return None


def find_program_id(hass, program_name: str, model_id: int) -> Optional[int]:
    """Ищет идентификатор режима по названию."""
    program_constants = get_program_constants(model_id)
    if not program_constants:
        return None

    translations = _get_translations(hass)
    program_names = translations.get("program_names", {})

    program_constant_by_name = {program_names.get(mc, ""): mc for mc in program_constants if mc}
    program_constant = program_constant_by_name.get(program_name)
    if program_constant is None:
        return None
    return _find_program_index(program_constants, program_constant)


def find_program_id_by_const(hass, const_name: str, model_id: int) -> Optional[int]:
    """Ищет идентификатор режима по константе."""
    program_constants = get_program_constants(model_id)
    if not program_constants:
        return None

    translations = _get_translations(hass)
    program_names = translations.get("program_names", {})

    program_constant_by_name = {program_names.get(mc, ""): mc for mc in program_constants if mc}
    for display_name, program_constant in program_constant_by_name.items():
        if program_constant == const_name:
            return _find_program_index(program_constants, program_constant)
    return None


def get_program_name(hass, program_id: int, model_id: int) -> str:
    """Возвращает название режима в зависимости от языка."""
    program_constants = get_program_constants(model_id)
    if model_id is None or not program_constants or program_id >= len(program_constants):
        return f"Unknown ({program_id})"
    program_constant = program_constants[program_id]
    if program_constant and program_constant != PROGRAM_NONE:
        translations = _get_translations(hass)
        program_names = translations.get("program_names", {})
        return program_names.get(program_constant, f"Unknown ({program_id})")

    return f"Unknown ({program_id})"


def is_subprogram_supported(model_id: int) -> bool:
    """Возвращает True, если модель поддерживает подпрограммы."""
    return model_id != MODEL_3

def get_subprogram_options() -> List[str]:
    """Возвращает список опций для подпрограмм."""
    return [str(i) for i in range(0, 16)]


def get_current_program_text(hass, skycooker, status_code: int) -> str:
    """Возвращает текст текущего режима."""
    standby_mode_text = get_localized_string(hass, "Standby Mode", "Режим ожидания")
    if status_code == STATUS_OFF:
        return standby_mode_text
    current_program_id = skycooker.current_program_id
    if current_program_id is not None:
        return get_program_name(hass, current_program_id, skycooker.model_id)
    return standby_mode_text


def get_favorite_programs(hass, entry, model_id: int) -> List[str]:
    """Возвращает список избранных режимов из настроек."""
    favorite_programs = entry.data.get(CONF_FAVORITE_PROGRAMS, [])
    if not favorite_programs:
        return []
     
    # Get translations
    translations = hass.data.get("skycooker_translations", {})
    program_names = translations.get("program_names", {})
     
    # Filter out invalid mode IDs and get their display names
    valid_favorites = [program_names.get(PROGRAM_STANDBY, f"Unknown ({PROGRAM_STANDBY})")]
    for program_name in favorite_programs:
        program_constant = get_constant_by_name(hass, program_name, model_id)
        if not program_name or not program_constant or program_constant == PROGRAM_NONE or program_constant == PROGRAM_STANDBY:
            continue
        valid_favorites.append(program_name)
 
    return valid_favorites

def is_program_supported(hass, program_name: str, model_id: int) -> bool:
    """Проверяет, поддерживается ли режим устройством."""
    program_const = get_constant_by_name(hass, program_name, model_id)
    if program_const is None: return False
    if model_id and model_id in PROGRAM_DATA:
        if program_const not in PROGRAM_NAMES[model_id]:
            _LOGGER.warning(f"⚠️  Режим {program_name} не поддерживается для модели {model_id}")
            return False
        if program_const == PROGRAM_STANDBY:
            _LOGGER.debug(f"📋 Режим 16 (ожидание) - это допустимое состояние устройства, но его нельзя устанавливать напрямую")
        elif program_const == PROGRAM_NONE:
            _LOGGER.debug(f"📋 Режим PROGRAM_NONE - зарезервированный слот, его нельзя устанавливать напрямую")
    return True
