#!/usr/bin/env python3
# coding: utf-8

"""
Класс для работы с мультиваркой SkyCooker через BLE.
"""

import asyncio
import traceback
from time import monotonic

try:
    from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("Bleak library not available. Install it with: pip install bleak-retry-connector")

from .skycooker import SkyCooker
from .const import *
from .logger import skycooker_logger as _LOGGER


class SkyCookerConnection(SkyCooker):
    """
    Класс для работы с мультиваркой SkyCooker через BLE.
    """
    
    def __init__(self, mac="DA:D8:9F:9E:0B:4C", key="0000000000000000", model="RMC-M40S"):
        super().__init__(model)
        self._device = None
        self._client = None
        self._mac = mac
        self._key = key
        self._auth_ok = False
        self._sw_version = None
        self._iter = 0
        self._update_lock = asyncio.Lock()
        self._last_data = None
        self._disposed = False
    
    async def command(self, command, params=None):
        if params is None:
            params = b''
        elif isinstance(params, bytes):
            params = params
        elif isinstance(params, str):
            params = params.encode('latin-1')
        else:
            params = bytes(params)
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
        if r[2] != command:
            _LOGGER.error(f"❌ Некорректная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
            raise IOError("Некорректная команда ответа")
        clean = bytes(r[3:-1])
        _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
        return clean
    
    def _rx_callback(self, sender, data):
        self._last_data = data
    
    auth = lambda self: super().auth(self._key)
    
    async def _connect(self):
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected:
            _LOGGER.debug("✅ Уже подключено к мультиварке")
            return
        try:
            if not BLEAK_AVAILABLE:
                raise ImportError("Bleak library not available. Install it with: pip install bleak-retry-connector")
            
            # Используем bleak для сканирования и подключения к устройству
            from bleak import BleakScanner
            
            _LOGGER.info("🔍 Поиск устройства %s...", self._mac)
            devices = await BleakScanner.discover()
            
            self._device = None
            for device in devices:
                if device.address.lower() == self._mac.lower():
                    self._device = device
                    break
            
            if not self._device:
                _LOGGER.error("❌ Устройство %s не найдено", self._mac)
                raise IOError(f"Устройство {self._mac} не найдено")
            
            _LOGGER.info("🔌 Подключение к мультиварке %s (%s)...", self._mac, self._device.name)
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self._device.name or "Unknown Device",
                max_attempts=5,
                retry_interval=1.0
            )
            _LOGGER.info("✅ Успешно подключено к мультиварке %s", self._mac)
            await self._client.start_notify(UUID_RX, self._rx_callback)
            _LOGGER.info("📡 Подписка на уведомления от мультиварки")
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
    
    async def _disconnect(self):
        try:
            if self._client:
                was_connected = self._client.is_connected
                await self._client.disconnect()
                if was_connected: _LOGGER.debug("Disconnected")
        finally:
            self._auth_ok = False
            self._device = None
            self._client = None
    
    async def disconnect(self):
        try:
            await self._disconnect()
        except:
            pass
    
    async def _connect_if_need(self):
        if self._client and not self._client.is_connected:
            _LOGGER.warning("⚠️  Подключение к мультиварке потеряно")
            await self.disconnect()
        if not self._client or not self._client.is_connected:
            try:
                await self._connect()
            except Exception as ex:
                await self.disconnect()
                _LOGGER.error(f"🚫 Ошибка подключения к мультиварке: {ex}")
                raise ex
        if not self._auth_ok:
            for attempt in range(MAX_TRIES):
                try:
                    self._auth_ok = await self.auth()
                    if self._auth_ok:
                        _LOGGER.info("✅ Аутентификация успешна")
                        self._sw_version = await self.get_version()
                        # try:
                        #     await self.sync_time()
                        # except Exception as e:
                        #     _LOGGER.warning(f"⚠️  Ошибка синхронизации времени: {e}")
                        break
                    else:
                        _LOGGER.warning(f"⚠️  Неудачная попытка аутентификации #{attempt + 1}")
                        await asyncio.sleep(TRIES_INTERVAL)
                except Exception as e:
                    _LOGGER.warning(f"⚠️  Ошибка аутентификации #{attempt + 1}: {e}")
                    await asyncio.sleep(TRIES_INTERVAL)
            if not self._auth_ok:
                _LOGGER.error("🚫 Ошибка аутентификации. Необходимо включить режим сопряжения на мультиварке.")
                raise AuthError("Ошибка аутентификации")