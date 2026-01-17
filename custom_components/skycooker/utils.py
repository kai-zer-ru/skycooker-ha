"""Утилиты для SkyCooker."""

from typing import Any
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.core import HomeAssistant

from .const import SKYCOOKER_NAME


def get_base_name(entry: Any) -> str:
    """Возвращает базовое имя устройства."""
    return (SKYCOOKER_NAME + " " + entry.data.get(CONF_FRIENDLY_NAME, "")).strip()


def get_lower_model_name(name: str) -> str:
    """Возвращает имя модели в нижнем регистре с заменой дефисов на подчеркивания."""
    return name.replace("-", "_").lower()


def get_language_index(hass: HomeAssistant) -> int:
    """Возвращает индекс языка (0 для английского, 1 для русского)."""
    return 0 if hass.config.language == "en" else 1


def is_russian(hass: HomeAssistant) -> bool:
    """Возвращает True, если текущий язык - русский."""
    return hass.config.language == "ru"


def get_localized_string(hass: HomeAssistant, english_text: str, russian_text: str) -> str:
    """Возвращает локализованную строку в зависимости от языка."""
    return russian_text if is_russian(hass) else english_text


def get_entity_name(
    hass: HomeAssistant,
    entry: Any,
    entity_type: str,
    localized_name_en: str,
    localized_name_ru: str,
) -> str:
    """Возвращает имя сущности с учетом локализации."""
    base_name = get_base_name(entry)
    localized_name = get_localized_string(hass, localized_name_en, localized_name_ru)
    return f"{base_name} {localized_name}"


def get_temperature_options() -> list[str]:
    """Возвращает список опций для температуры."""
    return [str(temp) for temp in range(40, 201, 5)]
