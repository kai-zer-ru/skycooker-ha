"""Утилиты для SkyCooker."""

from typing import Any

from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id

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


def build_entity_id(domain: str, hass: HomeAssistant, entry: Any, suffix: str) -> str:
    """Строит стабильный английский entity_id независимо от языка интерфейса.

    Формат: <domain>.skycooker_<model>_<suffix>, например:
    sensor.skycooker_rmc_m40s_success_rate
    """
    # В тестах или при некорректной инициализации entry/hass могут быть None.
    friendly = ""
    if entry is not None and getattr(entry, "data", None) is not None:
        friendly = entry.data.get(CONF_FRIENDLY_NAME, "") or ""
    model = get_lower_model_name(friendly) if friendly else "unknown"
    base_object_id = f"{SKYCOOKER_NAME.lower()}_{model}_{suffix}".lower()
    # В юнит‑тестах hass может быть None — в этом случае не используем generate_entity_id,
    # а просто собираем entity_id напрямую.
    if hass is None:
        return f"{domain}.{base_object_id}"
    return generate_entity_id(f"{domain}.{{}}", base_object_id, hass=hass)
