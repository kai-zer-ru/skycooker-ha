"""Утилиты для SkyCooker."""

from homeassistant.const import CONF_FRIENDLY_NAME

from .const import (SKYCOOKER_NAME, MODE_NAMES, MODE_NONE, STATUS_CODES, MODEL_3, MODE_DATA,
                   STATUS_OFF, STATUS_DELAYED_LAUNCH, STATUS_WARMING, STATUS_COOKING, STATUS_AUTO_WARM)
from .skycooker import SkyCooker


def get_base_name(entry):
    """Возвращает базовое имя устройства."""
    return (SKYCOOKER_NAME + " " + entry.data.get(CONF_FRIENDLY_NAME, "")).strip()


def get_language_index(hass):
    """Возвращает индекс языка (0 для английского, 1 для русского)."""
    return 0 if hass.config.language == "en" else 1


def is_russian(hass):
    """Возвращает True, если текущий язык - русский."""
    return hass.config.language == "ru"


def get_localized_string(hass, english_text, russian_text):
    """Возвращает локализованную строку в зависимости от языка."""
    return russian_text if is_russian(hass) else english_text


def get_mode_name(hass, mode_id, model_type):
    """Возвращает название режима в зависимости от языка."""
    if model_type is None or not MODE_NAMES.get(model_type) or mode_id >= len(MODE_NAMES[model_type]):
        return f"Unknown ({mode_id})"
    
    lang_index = get_language_index(hass)
    mode_constant = MODE_NAMES[model_type][mode_id]
    
    if mode_constant and len(mode_constant) > lang_index and mode_constant != MODE_NONE:
        return mode_constant[lang_index]
    
    return f"Unknown ({mode_id})"


def get_status_text(hass, status_code):
    """Возвращает текст статуса в зависимости от языка."""
    lang_index = get_language_index(hass)
    return STATUS_CODES[lang_index].get(
        status_code,
        f"Unknown ({status_code})" if lang_index == 0 else f"Неизвестно ({status_code})"
    )


def format_time(hass, hours, minutes):
    """Форматирует время в зависимости от языка."""
    time_str = f"{hours} ч. {minutes} м." if is_russian(hass) else f"{hours} h. {minutes} m."
    return time_str if hours > 0 or minutes > 0 else "0 ч. 0 м." if is_russian(hass) else "0 h. 0 m."


def get_entity_name(hass, entry, entity_type, localized_name_en, localized_name_ru):
    """Возвращает имя сущности с учетом локализации."""
    base_name = get_base_name(entry)
    localized_name = get_localized_string(hass, localized_name_en, localized_name_ru)
    return f"{base_name} {localized_name}"


def get_mode_options(hass, model_type):
    """Возвращает список опций для режимов."""
    if model_type is None or not MODE_NAMES.get(model_type):
        return []
    
    lang_index = get_language_index(hass)
    mode_constants = MODE_NAMES[model_type]
    
    # Добавляем пустую строку в начало списка
    options = [""] + [mode_constant[lang_index] for mode_constant in mode_constants
                if mode_constant and len(mode_constant) > lang_index and mode_constant != MODE_NONE]
    
    return options


def get_temperature_options():
    """Возвращает список опций для температуры."""
    return [str(temp) for temp in range(40, 201, 5)]


def get_time_options(hours=True):
    """Возвращает список опций для времени."""
    return [str(i) for i in range(0, 24)] if hours else [str(i) for i in range(0, 60)]


def get_subprogram_options():
    """Возвращает список опций для подпрограмм."""
    return [str(i) for i in range(0, 16)]


def should_show_subprogram(model_code):
    """Возвращает True, если модель поддерживает подпрограммы."""
    return model_code != MODEL_3


def find_mode_id(hass, option, model_type):
    """Ищет идентификатор режима по названию."""
    if model_type is None or not MODE_NAMES.get(model_type):
        return None
    
    lang_index = get_language_index(hass)
    mode_constants = MODE_NAMES[model_type]
    
    for idx, mode_constant in enumerate(mode_constants):
        if (mode_constant and len(mode_constant) > lang_index and
            mode_constant[lang_index] == option and mode_constant != MODE_NONE):
            return idx
    
    return None


def get_mode_data(model_type, mode_id):
    """Возвращает данные режима."""
    if model_type and model_type in MODE_DATA and mode_id < len(MODE_DATA[model_type]):
        return MODE_DATA[model_type][mode_id]
    return None


def get_time_from_status(skycooker, status, attr_name, default=0):
    """Возвращает значение времени из статуса или соединения."""
    if (status and isinstance(status, SkyCooker.Status) and
        hasattr(status, attr_name)):
        return getattr(status, attr_name)
    return getattr(skycooker, attr_name, default) if hasattr(skycooker, attr_name) else default


def calculate_remaining_time(hass, skycooker, status_code):
    """Рассчитывает оставшееся время в зависимости от статуса."""
    if status_code == STATUS_DELAYED_LAUNCH:
        # Для отложенного запуска: target_main + target_additional
        boil_hours = get_time_from_status(skycooker, skycooker.status, 'target_main_hours')
        boil_minutes = get_time_from_status(skycooker, skycooker.status, 'target_main_minutes')
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        total_hours = boil_hours + additional_hours
        total_minutes = boil_minutes + additional_minutes
        # Нормализуем минуты
        if total_minutes >= 60:
            total_hours += 1
            total_minutes -= 60
    elif status_code in [STATUS_WARMING, STATUS_COOKING]:
        # Для разогрева и готовки: только target_additional
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        total_hours = additional_hours
        total_minutes = additional_minutes
    else:
        total_hours = 0
        total_minutes = 0
    
    return format_time(hass, total_hours, total_minutes)


def get_cooking_time(hass, skycooker, status_code):
    """Возвращает время приготовления."""
    if status_code in [STATUS_DELAYED_LAUNCH, STATUS_WARMING, STATUS_COOKING]:
        boil_hours = get_time_from_status(skycooker, skycooker.status, 'target_main_hours')
        boil_minutes = get_time_from_status(skycooker, skycooker.status, 'target_main_minutes')
        return format_time(hass, boil_hours, boil_minutes)
    return format_time(hass, 0, 0)


def get_auto_warm_time(hass, skycooker, status_code):
    """Возвращает время автоподогрева."""
    if status_code == STATUS_AUTO_WARM:
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        return format_time(hass, additional_hours, additional_minutes)
    return format_time(hass, 0, 0)


def get_delayed_launch_time(hass, skycooker, status_code):
    """Возвращает время до отложенного запуска."""
    if status_code == STATUS_DELAYED_LAUNCH:
        additional_hours = get_time_from_status(skycooker, skycooker.status, 'target_additional_hours')
        additional_minutes = get_time_from_status(skycooker, skycooker.status, 'target_additional_minutes')
        return format_time(hass, additional_hours, additional_minutes)
    return format_time(hass, 0, 0)


def get_current_mode_text(hass, skycooker, status_code):
    """Возвращает текст текущего режима."""
    if status_code == STATUS_OFF:
        return "Режим ожидания" if hass.config.language == "ru" else "Standby Mode"
    current_mode = skycooker.current_mode
    if current_mode is not None:
        return get_mode_name(hass, current_mode, skycooker.model_code)
    return "Режим ожидания" if hass.config.language == "ru" else "Standby Mode"