"""Support for SkyCooker."""
import asyncio
import json
import logging
import os
from datetime import timedelta

import aiofiles
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.event as ev
from packaging import version

from homeassistant.const import __version__ as HA_VERSION
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE,
    CONF_FRIENDLY_NAME,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.dispatcher import async_dispatcher_send, dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_PERSISTENT_CONNECTION,
    DATA_CANCEL,
    DATA_CONNECTION,
    DATA_DEVICE_INFO,
    DATA_WORKING,
    DISPATCHER_UPDATE,
    DOMAIN,
    LANGS,
    MODELS,
    MANUFACTURER,
    SKYCOOKER_NAME,
)
from .skycooker_connection import SkyCookerConnection

_LOGGER = logging.getLogger(__name__)


def _resolve_entry_id_from_call(hass: HomeAssistant, call: ServiceCall) -> str | None:
    """Возвращает entry_id для сервиса.

    Приоритет:
    1. Явно переданный config_entry_id
    2. Явно переданный entry_id (для обратной совместимости и тестов)
    3. entity_id любой сущности SkyCooker (через entity_registry)
    """
    entry_id = call.data.get("config_entry_id") or call.data.get("entry_id")
    if entry_id:
        return entry_id

    entity_id = call.data.get("entity_id")
    if entity_id:
        ent_reg = er.async_get(hass)
        ent_entry = ent_reg.async_get(entity_id)
        if ent_entry and ent_entry.config_entry_id:
            return ent_entry.config_entry_id

    _LOGGER.error(
        "Сервис %s: требуется config_entry_id или entity_id SkyCooker-сущности",
        call.service,
    )
    return None


def _get_connection_from_call(hass: HomeAssistant, call: ServiceCall) -> SkyCookerConnection | None:
    """Извлекает SkyCookerConnection из hass.data по данным сервиса."""
    entry_id = _resolve_entry_id_from_call(hass, call)
    if not entry_id:
        _LOGGER.error("Сервис %s: требуется config_entry_id, entry_id или entity_id", call.service)
        return None

    domain_data = hass.data.get(DOMAIN, {})
    entry_data = domain_data.get(entry_id)
    if not entry_data:
        _LOGGER.error("Сервис %s: не найдено подключение SkyCooker для entry_id=%s", call.service, entry_id)
        return None
    conn = entry_data.get(DATA_CONNECTION)
    if not conn:
        _LOGGER.error("Сервис %s: DATA_CONNECTION отсутствует для entry_id=%s", call.service, entry_id)
        return None
    return conn


def _ensure_services_registered(hass: HomeAssistant) -> None:
    """Регистрирует сервисы интеграции (однократно)."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("services_registered"):
        return

    # Схемы сервисов для UI и валидации
    base_target_schema = {
        vol.Optional("config_entry_id"): cv.string,
        vol.Optional("entity_id"): cv.entity_id,
    }

    set_program_schema = vol.Schema(
        {
            **base_target_schema,
            vol.Optional("program_name"): cv.string,
            vol.Optional("subprogram_id"): vol.Coerce(int),
            vol.Optional("temperature"): vol.Coerce(int),
            vol.Optional("main_hours"): vol.Coerce(int),
            vol.Optional("main_minutes"): vol.Coerce(int),
            vol.Optional("additional_hours"): vol.Coerce(int),
            vol.Optional("additional_minutes"): vol.Coerce(int),
            vol.Optional("auto_warm"): cv.boolean,
        }
    )

    set_temperature_schema = vol.Schema(
        {
            **base_target_schema,
            vol.Required("temperature"): vol.Coerce(int),
        }
    )

    set_cook_time_schema = vol.Schema(
        {
            **base_target_schema,
            vol.Optional("main_hours"): vol.Coerce(int),
            vol.Optional("main_minutes"): vol.Coerce(int),
        }
    )

    set_delayed_start_schema = vol.Schema(
        {
            **base_target_schema,
            vol.Optional("delayed_start_hours"): vol.Coerce(int),
            vol.Optional("delayed_start_minutes"): vol.Coerce(int),
        }
    )

    simple_target_schema = vol.Schema(base_target_schema)

    start_cooking_schema = vol.Schema(
        {
            **base_target_schema,
            vol.Optional("auto_warm"): cv.boolean,
        }
    )

    async def _apply_settings_without_start(conn: SkyCookerConnection, service_name: str) -> None:
        """Применяет текущие настройки на устройстве без запуска приготовления."""
        try:
            await conn.apply_current_settings_without_start()
        except Exception as e:
            _LOGGER.debug("Применение настроек без запуска после %s: %s", service_name, e)

    async def handle_set_program(call: ServiceCall) -> None:
        _LOGGER.debug("Сервис set_program вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        data = call.data

        program_name = data.get("program_name")
        subprogram_id = data.get("subprogram_id")
        temperature = data.get("temperature")
        main_hours = data.get("main_hours")
        main_minutes = data.get("main_minutes")
        additional_hours = data.get("additional_hours")
        additional_minutes = data.get("additional_minutes")
        auto_warm = data.get("auto_warm")
        should_apply = any(
            [
                bool(program_name),
                subprogram_id is not None,
                temperature is not None,
                main_hours is not None,
                main_minutes is not None,
                additional_hours is not None,
                additional_minutes is not None,
                auto_warm is not None,
            ]
        )

        if program_name:
            await conn.set_target_program(program_name)
        if subprogram_id is not None:
            conn.target_subprogram_id = int(subprogram_id)
        if temperature is not None:
            await conn.set_temperature(int(temperature))
        if main_hours is not None or main_minutes is not None:
            mh = int(main_hours) if main_hours is not None else 0
            mm = int(main_minutes) if main_minutes is not None else 0
            await conn.set_boil_time(mh, mm)
        if additional_hours is not None or additional_minutes is not None:
            ah = int(additional_hours) if additional_hours is not None else 0
            am = int(additional_minutes) if additional_minutes is not None else 0
            await conn.set_delayed_start(ah, am)
        if auto_warm is not None:
            if bool(auto_warm):
                await conn.enable_auto_warm()
            else:
                await conn.disable_auto_warm()
        if should_apply:
            await _apply_settings_without_start(conn, "set_program")

    async def handle_set_temperature(call: ServiceCall) -> None:
        """Устанавливает целевую температуру."""
        _LOGGER.debug("Сервис set_temperature вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        temperature = call.data.get("temperature")
        if temperature is None:
            return
        await conn.set_temperature(int(temperature))
        await _apply_settings_without_start(conn, "set_temperature")

    async def handle_set_cook_time(call: ServiceCall) -> None:
        """Устанавливает основное время приготовления."""
        _LOGGER.debug("Сервис set_cook_time вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        main_hours = call.data.get("main_hours")
        main_minutes = call.data.get("main_minutes")
        if main_hours is None and main_minutes is None:
            return
        mh = int(main_hours) if main_hours is not None else 0
        mm = int(main_minutes) if main_minutes is not None else 0
        await conn.set_boil_time(mh, mm)
        await _apply_settings_without_start(conn, "set_cook_time")

    async def handle_set_delayed_start(call: ServiceCall) -> None:
        """Устанавливает время отложенного старта."""
        _LOGGER.debug("Сервис set_delayed_start вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        delayed_hours = call.data.get("delayed_start_hours")
        delayed_minutes = call.data.get("delayed_start_minutes")
        if delayed_hours is None and delayed_minutes is None:
            return
        dh = int(delayed_hours) if delayed_hours is not None else 0
        dm = int(delayed_minutes) if delayed_minutes is not None else 0
        await conn.set_delayed_start(dh, dm)
        await _apply_settings_without_start(conn, "set_delayed_start")

    async def handle_enable_auto_warm(call: ServiceCall) -> None:
        _LOGGER.debug("Сервис enable_auto_warm вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        await conn.enable_auto_warm()

    async def handle_disable_auto_warm(call: ServiceCall) -> None:
        _LOGGER.debug("Сервис disable_auto_warm вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        await conn.disable_auto_warm()

    async def handle_sync_time(call: ServiceCall) -> None:
        _LOGGER.debug("Сервис sync_time вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        # sync_time реализован в SkyCookerConnectionManager
        await conn.connection_manager.sync_time()

    async def handle_start_cooking(call: ServiceCall) -> None:
        """Запускает приготовление с уже настроенной программой и параметрами."""
        _LOGGER.debug("Сервис start_cooking вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        auto_warm = call.data.get("auto_warm")
        if auto_warm is not None:
            if bool(auto_warm):
                await conn.enable_auto_warm()
            else:
                await conn.disable_auto_warm()
        # Если задано ненулевое отложенное время — используем отложенный старт
        try:
            delayed_hours = getattr(conn, "target_additional_hours", 0) or 0
            delayed_minutes = getattr(conn, "target_additional_minutes", 0) or 0
        except Exception:  # на всякий случай, если свойств нет
            delayed_hours = delayed_minutes = 0

        if delayed_hours or delayed_minutes:
            await conn.start_delayed()
        else:
            await conn.start()
        # Сразу запрашиваем актуальный статус с устройства, не ждём опроса по таймауту
        try:
            await conn.update()
        except Exception as e:
            _LOGGER.debug("Обновление статуса после start_cooking: %s", e)
        async_dispatcher_send(hass, DISPATCHER_UPDATE)

    async def handle_stop_cooking(call: ServiceCall) -> None:
        """Останавливает текущее приготовление и переводит устройство в режим ожидания."""
        _LOGGER.debug("Сервис stop_cooking вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return
        await conn.stop_cooking()
        # Сразу запрашиваем актуальный статус с устройства, не ждём опроса по таймауту
        try:
            await conn.update()
        except Exception as e:
            _LOGGER.debug("Обновление статуса после stop_cooking: %s", e)
        async_dispatcher_send(hass, DISPATCHER_UPDATE)

    # Регистрация сервисов; в тестах MockServices может не принимать аргумент schema,
    # поэтому пробуем с schema и при TypeError регистрируем без него.

    def _register(name: str, handler: callable, schema: vol.Schema | None = None) -> None:
        try:
            if schema is not None:
                hass.services.async_register(DOMAIN, name, handler, schema=schema)
            else:
                hass.services.async_register(DOMAIN, name, handler)
        except TypeError:
            hass.services.async_register(DOMAIN, name, handler)

    # Современные сервисы
    _register("set_program", handle_set_program, set_program_schema)
    _register("set_temperature", handle_set_temperature, set_temperature_schema)
    _register("set_cook_time", handle_set_cook_time, set_cook_time_schema)
    _register("set_delayed_start", handle_set_delayed_start, set_delayed_start_schema)
    _register("enable_auto_warm", handle_enable_auto_warm, simple_target_schema)
    _register("disable_auto_warm", handle_disable_auto_warm, simple_target_schema)
    _register("sync_time", handle_sync_time, simple_target_schema)
    _register("start_cooking", handle_start_cooking, start_cooking_schema)
    _register("stop_cooking", handle_stop_cooking, simple_target_schema)

    # Backward‑compat: оставляем сервис run_recipe для тестов и старых автоматизаций.
    async def handle_run_recipe(call: ServiceCall) -> None:
        """Совместимость: старый сервис run_recipe (настраивает и сразу запускает)."""
        _LOGGER.debug("Сервис run_recipe вызван с данными: %s", dict(call.data))
        conn = _get_connection_from_call(hass, call)
        if not conn:
            return

        data = call.data
        program_name = data.get("program_name")
        temperature = data.get("temperature")
        main_hours = data.get("main_hours")
        main_minutes = data.get("main_minutes")
        delayed_hours = data.get("delayed_start_hours")
        delayed_minutes = data.get("delayed_start_minutes")
        auto_warm = data.get("auto_warm")

        if program_name:
            await conn.set_target_program(program_name)
        if temperature is not None:
            await conn.set_temperature(int(temperature))
        if main_hours is not None or main_minutes is not None:
            mh = int(main_hours) if main_hours is not None else 0
            mm = int(main_minutes) if main_minutes is not None else 0
            await conn.set_boil_time(mh, mm)
        if delayed_hours is not None or delayed_minutes is not None:
            dh = int(delayed_hours) if delayed_hours is not None else 0
            dm = int(delayed_minutes) if delayed_minutes is not None else 0
            await conn.set_delayed_start(dh, dm)

        if auto_warm is not None:
            if bool(auto_warm):
                await conn.enable_auto_warm()
            else:
                await conn.disable_auto_warm()

        # Если есть отложенный старт — запускаем отложенно, иначе обычный старт.
        if (delayed_hours or 0) or (delayed_minutes or 0):
            await conn.start_delayed()
        else:
            await conn.start()

    _register("run_recipe", handle_run_recipe)

    domain_data["services_registered"] = True


def _key_to_bytes(key):  # noqa: D401
    """Convert key from config (list of int, bytes or hex str) to bytes."""
    if isinstance(key, bytes):
        return key
    if isinstance(key, str):
        return bytes.fromhex(key) if key else bytes(16)
    return bytes(key) if key else bytes(16)


PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BUTTON
]


async def async_setup(hass, config):
    """Настройка компонента SkyCooker."""
    # Проверка минимальной версии HomeAssistant
    min_ha_version = "2025.12.5"
    if version.parse(HA_VERSION) < version.parse(min_ha_version):
        _LOGGER.error(
            "Требуется Home Assistant версии %s или выше. У вас установлена версия %s",
            min_ha_version, HA_VERSION
        )
        return False

    hass.data.setdefault(DOMAIN, {})
    if "skycooker_translations" not in hass.data:
        await load_translations(hass)
    _LOGGER.debug("Интеграция SkyCooker загружена. Версия HA: %s", HA_VERSION)
    return True


async def load_translations(hass):
    """Load translations from JSON files."""
    translations = {}

    # Determine the language to load
    language = getattr(hass.config, 'language', 'ru')

    # Check if the language is supported
    if language not in LANGS:
        _LOGGER.warning("Язык %s не поддерживается. Используется английский", language)
        language = 'en'

    # Load the appropriate translation file
    translation_file = os.path.join(os.path.dirname(__file__), 'translations', f'{language}.json')

    try:
        async with aiofiles.open(translation_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            translations = json.loads(content)
        _LOGGER.debug("Загружены переводы для языка: %s", language)
    except FileNotFoundError:
        _LOGGER.warning(
            "Файл переводов для языка %s не найден, используется английский", language
        )
        # Fallback to English
        translation_file = os.path.join(os.path.dirname(__file__), 'translations', 'en.json')
        try:
            async with aiofiles.open(translation_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                translations = json.loads(content)
            _LOGGER.debug("Загружены английские переводы как резервные")
        except Exception as e:
            _LOGGER.error("Ошибка загрузки английских переводов: %s", e)
            translations = {}
    except Exception as e:
        _LOGGER.error("Ошибка загрузки переводов: %s", e)
        translations = {}

    hass.data["skycooker_translations"] = translations


def _create_poll_scheduler(hass, entry, skycooker):
    """Создаёт poll и schedule_poll для периодического обновления статуса."""

    def schedule_poll(td):
        hass.data[DOMAIN][DATA_CANCEL] = ev.async_call_later(hass, td, poll)

    async def poll(now, **kwargs) -> None:
        await skycooker.update()
        await hass.async_add_executor_job(dispatcher_send, hass, DISPATCHER_UPDATE)
        if hass.data[DOMAIN][DATA_WORKING]:
            schedule_poll(timedelta(seconds=entry.data[CONF_SCAN_INTERVAL]))

    return poll, schedule_poll


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Настройка интеграции SkyCooker из конфигурационного входа."""
    entry.async_on_unload(entry.add_update_listener(entry_update_listener))

    if DOMAIN not in hass.data: hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data: hass.data[DOMAIN][entry.entry_id] = {}

    # Регистрируем доменные сервисы (однократно на все entry)
    _ensure_services_registered(hass)

    # Load translations if not already loaded
    if "skycooker_translations" not in hass.data:
        await load_translations(hass)

    # Проверка поддержки модели
    model_name = entry.data.get(CONF_FRIENDLY_NAME, "")
    if model_name not in MODELS:
        _LOGGER.error(
            "Модель %s не поддерживается. Поддерживаемые модели: %s",
            model_name, list(MODELS.keys())
        )
        return False

    try:
        skycooker = SkyCookerConnection(
            mac=entry.data[CONF_MAC],
            key=_key_to_bytes(entry.data.get(CONF_PASSWORD)),
            persistent=entry.data[CONF_PERSISTENT_CONNECTION],
            adapter=entry.data.get(CONF_DEVICE, None),
            hass=hass,
            model_name=model_name
        )
        hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION] = skycooker

        # Подключение и получение версии ПО во время начальной настройки
        await skycooker.update()
        _LOGGER.debug("Версия ПО устройства: %s", skycooker.sw_version)
    except Exception as e:
        if "не найдено" in str(e).lower() or "not found" in str(e).lower():
            _LOGGER.error(
                "Устройство %s не найдено. Проверьте, что устройство включено и в зоне действия Bluetooth.",
                entry.data[CONF_MAC]
            )
            return False
        _LOGGER.error("Ошибка при настройке соединения: %s", e)
        return False

    poll, schedule_poll = _create_poll_scheduler(hass, entry, skycooker)

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
        manufacturer=MANUFACTURER,
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
    _LOGGER.debug("Выгрузка интеграции")
    hass.data[DOMAIN][DATA_WORKING] = False
    hass.data[DOMAIN][DATA_CANCEL]()
    await asyncio.gather(*[
        hass.config_entries.async_forward_entry_unload(entry, component)
        for component in PLATFORMS
    ])
    conn = hass.data[DOMAIN][entry.entry_id].get(DATA_CONNECTION)
    if conn:
        await hass.async_add_executor_job(conn.stop)
    hass.data[DOMAIN][entry.entry_id][DATA_CONNECTION] = None
    _LOGGER.debug("Вход выгружен")
    return True


async def entry_update_listener(hass, entry):
    """Обработка обновления опций."""
    skycooker = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get(DATA_CONNECTION)
    if skycooker:
        skycooker.persistent = entry.data.get(CONF_PERSISTENT_CONNECTION)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Return diagnostics for the config entry."""
    data = {
        "config": {
            "model": entry.data.get(CONF_FRIENDLY_NAME),
            "mac": entry.data.get(CONF_MAC),
            "scan_interval": entry.data.get(CONF_SCAN_INTERVAL),
            "persistent_connection": entry.data.get(CONF_PERSISTENT_CONNECTION),
        },
    }
    conn = None
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        conn = hass.data[DOMAIN][entry.entry_id].get(DATA_CONNECTION)
    if conn:
        data["connection"] = {
            "available": getattr(conn, "available", False),
            "sw_version": getattr(conn, "sw_version", None),
            "success_rate": getattr(conn, "success_rate", None),
        }
    return data
