"""Support for SkyCooker."""
import logging
from datetime import timedelta

import homeassistant.helpers.event as ev
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_DEVICE,
                                  CONF_FRIENDLY_NAME, CONF_MAC, CONF_PASSWORD,
                                  CONF_SCAN_INTERVAL, Platform)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import DeviceInfo

from .const import *
from .skycooker_connection import SkyCookerConnection

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BUTTON
]

async def async_setup(hass, config):
    """Настройка компонента SkyCooker."""
    # Проверка минимальной версии HomeAssistant
    from homeassistant.const import __version__ as HA_VERSION
    from packaging import version
    
    min_ha_version = "2025.12.5"
    if version.parse(HA_VERSION) < version.parse(min_ha_version):
        _LOGGER.error("❌ Требуется HomeAssistant версии %s или выше. У вас установлена версия %s",
                     min_ha_version, HA_VERSION)
        return False
    
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("✅ Интеграция SkyCooker загружена. Версия HA: %s", HA_VERSION)
    return True

async def load_translations(hass):
    """Load translations from JSON files."""
    import json
    import os
    import aiofiles

    translations = {}

    # Determine the language to load
    language = getattr(hass.config, 'language', 'ru')

    # Check if the language is supported
    if language not in LANGS:
        _LOGGER.warning(f"⚠️  Язык {language} не поддерживается. Используется английский")
        language = 'en'

    # Load the appropriate translation file
    translation_file = os.path.join(os.path.dirname(__file__), 'translations', f'{language}.json')

    try:
        async with aiofiles.open(translation_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            translations = json.loads(content)
        _LOGGER.debug(f"✅ Загружены переводы для языка: {language}")
    except FileNotFoundError:
        _LOGGER.warning(f"⚠️  Файл переводов для языка {language} не найден, используется английский")
        # Fallback to English
        translation_file = os.path.join(os.path.dirname(__file__), 'translations', 'en.json')
        try:
            async with aiofiles.open(translation_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                translations = json.loads(content)
            _LOGGER.debug("✅ Загружены английские переводы как резервные")
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка загрузки английских переводов: {e}")
            translations = {}
    except Exception as e:
        _LOGGER.error(f"❌ Ошибка загрузки переводов: {e}")
        translations = {}

    hass.data["skycooker_translations"] = translations

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Настройка интеграции SkyCooker из конфигурационного входа."""
    entry.async_on_unload(entry.add_update_listener(entry_update_listener))

    if DOMAIN not in hass.data: hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data: hass.data[DOMAIN][entry.entry_id] = {}

    # Load translations if not already loaded
    if "skycooker_translations" not in hass.data:
        await load_translations(hass)

    # Проверка поддержки модели
    model_name = entry.data.get(CONF_FRIENDLY_NAME, "")
    if model_name not in MODELS:
        _LOGGER.error(f"🚨 Модель {model_name} не поддерживается. Поддерживаемые модели: {list(MODELS.keys())}")
        return False


    try:
        skycooker = SkyCookerConnection(
            mac=entry.data[CONF_MAC],
            key=entry.data[CONF_PASSWORD],
            persistent=entry.data[CONF_PERSISTENT_CONNECTION],
            adapter=entry.data.get(CONF_DEVICE, None),
            hass=hass,
            model_name=model_name
        )
        hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION] = skycooker
        
        # Подключение и получение версии ПО во время начальной настройки
        await skycooker.update()
        _LOGGER.debug(f"📋 Версия ПО устройства: {skycooker.sw_version}")
    except Exception as e:
        if "не найдено" in str(e).lower() or "not found" in str(e).lower():
            _LOGGER.error(f"🚨 Устройство {entry.data[CONF_MAC]} не найдено. Проверьте, что устройство включено и находится в зоне действия Bluetooth.")
            return False
        else:
            _LOGGER.error(f"🚨 Ошибка при настройке соединения: {e}")
            return False

    async def poll(now, **kwargs) -> None:
        await skycooker.update()
        await hass.async_add_executor_job(dispatcher_send, hass, DISPATCHER_UPDATE)
        if hass.data[DOMAIN][DATA_WORKING]:
            schedule_poll(timedelta(seconds=entry.data[CONF_SCAN_INTERVAL]))
        else:
            _LOGGER.debug("🔴 Не работает больше, остановка")

    def schedule_poll(td):
        hass.data[DOMAIN][DATA_CANCEL] = ev.async_call_later(hass, td, poll)

    hass.data[DOMAIN][DATA_WORKING] = True
    hass.data[DOMAIN][DATA_DEVICE_INFO] = lambda: device_info(entry, hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    schedule_poll(timedelta(seconds=3))

    return True


def device_info(entry, hass):
    # Получение соединения SkyCooker для доступа к версии ПО
    skycooker = None
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        skycooker = hass.data[DOMAIN][entry.entry_id].get(DATA_CONNECTION)
    
    # Получение версии ПО из соединения, если доступно
    sw_version = None
    if skycooker and skycooker.sw_version:
        sw_version = skycooker.sw_version
    
    return DeviceInfo(
        name=(SKYCOOKER_NAME + " " + entry.data.get(CONF_FRIENDLY_NAME, "")).strip(),
        manufacturer=MANUFACTORER,
        model=entry.data.get(CONF_FRIENDLY_NAME, None),
        sw_version=sw_version,
        identifiers={
            (DOMAIN, entry.data[CONF_MAC])
        },
        connections={
            ("mac", entry.data[CONF_MAC])
        }
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Выгрузка конфигурационного входа."""
    _LOGGER.debug("🔄 Выгрузка")
    hass.data[DOMAIN][DATA_WORKING] = False
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_unload(entry, component)
        )
    hass.data[DOMAIN][DATA_CANCEL]()
    await hass.async_add_executor_job(hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION].stop)
    hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION] = None
    _LOGGER.debug("✅ Вход выгружен")
    return True


async def entry_update_listener(hass, entry):
    """Обработка обновления опций."""
    skycooker = hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION]
    skycooker.persistent = entry.data.get(CONF_PERSISTENT_CONNECTION)
    
    
    _LOGGER.debug("⚙️  Опции обновлены")