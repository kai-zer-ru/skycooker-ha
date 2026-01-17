#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
from time import monotonic
from typing import Optional, List, Any

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components import bluetooth

from .const import *
from .skycooker import SkyCooker
from .status import get_status

_LOGGER = logging.getLogger(__name__)


class SkyCookerConnectionManager(SkyCooker):
    """Класс для управления BLE соединением с мультиваркой."""
     
    def __init__(
        self,
        mac_address: str,
        key: bytes,
        persistent: bool = True,
        adapter: Optional[Any] = None,
        hass: Optional[Any] = None,
        model_name: Optional[str] = None
    ) -> None:
        # Инициализация базового класса SkyCooker
        super().__init__(hass, model_name)
        
        self._device = None
        self._client = None
        self._mac_address = mac_address
        self._key = key
        self._persistent = persistent
        self._adapter = adapter
        self._hass = hass
        self._auth_ok = False
        self._sw_version = '0.0'
        self._iter = 0
        self._update_lock = asyncio.Lock()
        self._last_set_target = 0
        self._last_connect_ok = False
        self._last_auth_ok = False
        self._successes: List[bool] = []
        self._disposed = False
        self._last_data: Optional[bytes] = None
    
    async def command(self, command: int, params: Optional[List[int]] = None) -> bytes:
        """Отправка команды устройству через BLE."""
        if params is None:
            params = []
        if self._disposed:
            raise DisposedError()
        if not self._client or not self._client.is_connected:
            raise IOError("🔌 Не подключено")
        self._iter = (self._iter + 1) % 256
        _LOGGER.debug(f"📤 Отправка команды {command:02x}, данные: [{' '.join([f'{c:02x}' for c in params])}]")
        data = bytes([0x55, self._iter, command] + list(params) + [0xAA])
        self._last_data = None
        try:
            await self._client.write_gatt_char(UUID_TX, data)
            _LOGGER.debug(f"📋 Отправленный пакет: {data.hex().upper()}")
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка отправки команды: {e}")
            raise IOError(f"Ошибка отправки команды: {e}")
        timeout_time = monotonic() + BLE_RECV_TIMEOUT
        while True:
            await asyncio.sleep(0.05)
            if self._last_data:
                r = self._last_data
                _LOGGER.debug(f"📥 Получен сырой ответ: {r.hex().upper()}")
                if len(r) < 4 or r[0] != 0x55 or r[-1] != 0xAA:
                    _LOGGER.error(f"❌ Некорректный формат ответа: {r.hex().upper()}")
                    raise IOError("Некорректный формат ответа")
                if r[1] == self._iter:
                    _LOGGER.debug(f"✅ Правильный идентификатор запроса {self._iter} в ответе")
                    break
                else:
                    _LOGGER.warning(f"⚠️  Неправильный идентификатор запроса в ответе: ожидалось {self._iter}, получено {r[1]}")
                    _LOGGER.warning(f"💡 Это может быть ответ на предыдущий запрос или от другого устройства")
                    self._last_data = None
            if monotonic() >= timeout_time:
                _LOGGER.error(f"⏱️  Таймаут приема ответа на команду {command:02x}")
                raise IOError("Таймаут приема")
         
        # Check if the response command matches the expected command
        if r[2] != command:
            _LOGGER.warning(f"⚠️  Получена неожиданная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
            
            # For SELECT_PROGRAM and SET_MAIN_MODE commands, if we get a status update (0x06),
            # it might mean the device processed the command and sent its current status
            if command in [COMMAND_SELECT_PROGRAM, COMMAND_SET_MAIN_MODE] and r[2] == COMMAND_GET_STATUS:
                _LOGGER.debug(f"📊 Устройство отправило обновление статуса после команды {command:02x}")
                _LOGGER.debug(f"💡 Вероятно, команда была обработана успешно")
                clean = bytes([0x01])  # Success code
                _LOGGER.debug(f"📥 Очищенные данные ответа: 01 (успех)")
                return clean
            elif command == COMMAND_TURN_ON and r[2] == COMMAND_GET_STATUS:
                _LOGGER.debug(f"📊 Устройство отправило обновление статуса после команды {command:02x}")
                _LOGGER.debug(f"💡 Вероятно, команда была обработана успешно")
                clean = bytes([0x01])  # Success code
                _LOGGER.debug(f"📥 Очищенные данные ответа: 01 (успех)")
                return clean
            elif command == COMMAND_GET_STATUS and r[2] in [COMMAND_SELECT_PROGRAM, COMMAND_SET_MAIN_MODE, COMMAND_TURN_OFF]:
                _LOGGER.debug(f"📊 Получен отложенный ответ на команду {r[2]:02x} вместо статуса")
                _LOGGER.debug(f"💡 Вероятно, предыдущая команда была обработана успешно")
                clean = bytes(r[3:-1])
                _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
                return clean
            else:
                _LOGGER.error(f"❌ Некорректная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
                raise IOError("Некорректная команда ответа")
         
        clean = bytes(r[3:-1])
        _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
        return clean

    def _rx_callback(self, sender: Any, data: bytes) -> None:
        """Callback для обработки входящих данных."""
        self._last_data = data

    async def _connect(self) -> None:
        """Установка соединения с устройством."""
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected:
            _LOGGER.debug("✅ Уже подключено к мультиварке")
            return
        try:
            # Очистка предыдущих подключений
            await self._cleanup_previous_connections()
            
            self._device = bluetooth.async_ble_device_from_address(self._hass, self._mac_address)
            if not self._device:
                _LOGGER.error("❌ Устройство %s не найдено", self._mac_address)
                raise IOError(f"Устройство {self._mac_address} не найдено")
            _LOGGER.debug("🔌 Подключение к мультиварке %s (%s)...", self._mac_address, self._device.name)
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self._device.name or "Unknown Device",
                max_attempts=5,
                retry_interval=1.0
            )
            _LOGGER.debug("✅ Успешно подключено к мультиварке %s", self._mac_address)
            await self._client.start_notify(UUID_RX, self._rx_callback)
            _LOGGER.debug("📡 Подписка на уведомления от мультиварки")
        except Exception as e:
            _LOGGER.error("❌ Ошибка подключения к мультиварке: %s", e)
            _LOGGER.error("💡 Проверьте, что устройство находится в режиме сопряжения и рядом с адаптером")
            if "out of connection slots" in str(e).lower():
                _LOGGER.error("💡 Bluetooth адаптер исчерпал лимит соединений. Попробуйте:")
                _LOGGER.error("   1. Перезагрузите Bluetooth адаптер")
                _LOGGER.error("   2. Уменьшите количество активных Bluetooth устройств")
                _LOGGER.error("   3. Используйте дополнительный Bluetooth прокси")
                _LOGGER.error("   4. Проверьте, что мультиварка находится в режиме сопряжения")
            raise

    async def auth(self, key: bytes) -> bool:
        """Аутентификация на устройстве."""
        return await super().auth(key)

    async def _cleanup_previous_connections(self) -> None:
        """Очистка предыдущих соединений."""
        try:
            if self._client:
                if self._client.is_connected:
                    _LOGGER.debug("🧹 Очистка предыдущего соединения...")
                    await self._client.disconnect()
                self._client = None
            self._device = None
        except Exception as e:
            _LOGGER.warning(f"⚠️  Ошибка очистки предыдущего соединения: {e}")

    async def _disconnect(self) -> None:
        """Отключение от устройства."""
        try:
            if self._client:
                was_connected = self._client.is_connected
                await self._client.disconnect()
                if was_connected: _LOGGER.debug("Disconnected")
        finally:
            self._auth_ok = False
            self._device = None
            self._client = None

    async def disconnect(self) -> None:
        """Публичный метод отключения."""
        try:
            await self._disconnect()
        except Exception:
            pass

    def rx_callback(self, sender: Any, data: bytes) -> None:
        """Публичный метод для обработки входящих данных."""
        self._rx_callback(sender, data)

    async def connect(self) -> None:
        """Публичный метод для установки соединения с устройством."""
        await self._connect()

    async def cleanup_previous_connections(self) -> None:
        """Публичный метод для очистки предыдущих соединений."""
        await self._cleanup_previous_connections()

    @property
    def successes(self) -> List[bool]:
        """Публичное свойство для доступа к списку успешных операций."""
        return self._successes

    @property
    def disposed(self) -> bool:
        """Публичное свойство для доступа к состоянию disposed."""
        return self._disposed

    @property
    def mac_address(self) -> str:
        """Публичное свойство для доступа к MAC адресу."""
        return self._mac_address

    async def connect_if_need(self) -> None:
        """Публичный метод подключения при необходимости."""
        await self._connect_if_need()

    async def disconnect_if_need(self) -> None:
        """Публичный метод отключения при необходимости."""
        await self._disconnect_if_need()

    async def _connect_if_need(self) -> None:
        """Подключение при необходимости."""
        if self._client and not self._client.is_connected:
            _LOGGER.warning("⚠️  Подключение к мультиварке потеряно")
            await self.disconnect()
        if not self._client or not self._client.is_connected:
            try:
                await self._connect()
                self._last_connect_ok = True
            except Exception as ex:
                await self.disconnect()
                self._last_connect_ok = False
                _LOGGER.error(f"🚫 Ошибка подключения к мультиварке: {ex}")
                raise ex
        if not self._auth_ok:
            self._last_auth_ok = self._auth_ok = await self.auth(self._key)
            if not self._auth_ok:
                _LOGGER.error("🚫 Ошибка аутентификации. Необходимо включить режим сопряжения на мультиварке.")
                raise AuthError("Ошибка аутентификации")
            _LOGGER.debug("✅ Аутентификация успешна")
            self._sw_version = await self.get_version()
            _LOGGER.debug(f"📋 Версия ПО: {self._sw_version}")

    async def _disconnect_if_need(self) -> None:
        """Отключение при необходимости (если не постоянное соединение)."""
        if not self._persistent:
            await self.disconnect()

    def add_stat(self, value: bool) -> None:
        """Добавление статистики успешных операций."""
        self._successes.append(value)
        if len(self._successes) > 100:
            self._successes = self._successes[-100:]

    @property
    def success_rate(self) -> int:
        """Процент успешных операций."""
        if len(self._successes) == 0:
            return 0
        return int(100 * len([s for s in self._successes if s]) / len(self._successes))

    async def stop(self) -> None:
        """Остановка менеджера соединений."""
        if self._disposed:
            return
        await self._disconnect()
        self._disposed = True
        _LOGGER.debug("Stopped.")

    @property
    def available(self) -> bool:
        """Доступность устройства."""
        return self._last_connect_ok and self._last_auth_ok

    @property
    def last_connect_ok(self) -> bool:
        """Статус последнего подключения."""
        return self._last_connect_ok

    @property
    def last_auth_ok(self) -> bool:
        """Статус последней аутентификации."""
        return self._last_auth_ok

    @property
    def connected(self) -> bool:
        """Статус текущего соединения."""
        return True if self._client and self._client.is_connected else False

    @property
    def auth_ok(self) -> bool:
        """Статус аутентификации."""
        return self._auth_ok

    @property
    def sw_version(self) -> str:
        """Версия программного обеспечения устройства."""
        return self._sw_version if self._sw_version else "0.0"

    @property
    def update_lock(self) -> asyncio.Lock:
        """Публичное свойство для доступа к блокировке обновления."""
        return self._update_lock

    @property
    def hass(self) -> asyncio.Lock:
        """Публичное свойство для доступа к блокировке обновления."""
        return self._hass

    @hass.setter
    def hass(self, value):
        """Публичное свойство для доступа к блокировке обновления."""
        self._hass = value

    async def get_version(self) -> str:
        """Получение версии ПО устройства."""
        return await super().get_version()

    async def get_status(self) -> Status:
        """Получение статуса устройства."""
        return await get_status(self)


    async def select_program(self, program_id: int, subprogram_id: int = 0) -> None:
        """Выбор программы устройства."""
        return await super().select_program(program_id, subprogram_id)

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
        """Установка основной программы."""
        return await super().set_main_program(
            program_id,
            subprogram_id,
            target_temperature,
            target_main_hours,
            target_main_minutes,
            target_additional_hours,
            target_additional_minutes,
            auto_warm,
            bit_flags
        )

    async def turn_on(self) -> None:
        """Включение устройства."""
        return await super().turn_on()

    async def turn_off(self) -> None:
        """Выключение устройства."""
        return await super().turn_off()

    async def sync_time(self) -> None:
        """Синхронизация времени."""
        from .time import sync_time
        return await sync_time(self)


class AuthError(Exception):
    pass


class DisposedError(Exception):
    pass