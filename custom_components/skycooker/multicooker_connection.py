#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import traceback
from time import monotonic

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components import bluetooth

from .const import *

_LOGGER = logging.getLogger(__name__)

# Стандартные UUID для R4S устройств (резервные)
DEFAULT_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
DEFAULT_NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
DEFAULT_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"


def get_model_constant(model_name, constant_type, key):
    """Get model-specific constant."""
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Model {model_name} not supported")
    
    model_config = SUPPORTED_MODELS[model_name]
    
    if constant_type == "command":
        return model_config["commands"].get(key)
    elif constant_type == "mode":
        # Return the mode name for display
        return model_config["modes"].get(key)
    elif constant_type == "status":
        # Return the status text for display
        return model_config["status_codes"].get(key)
    
    raise ValueError(f"Unknown constant type: {constant_type}")


class MulticookerConnection:
    """Main class for multicooker connection based on working library."""
    
    def __init__(self, mac, key, persistent=True, adapter=None, hass=None, model=None):
        """Initialize the multicooker connection."""
        self._device = None
        self._client = None
        self._mac = mac
        self._key = key
        self.persistent = persistent
        self.adapter = adapter
        self.hass = hass
        self._auth_ok = False
        self._sw_version = None
        self._iter = 0
        self._update_lock = asyncio.Lock()
        self._last_set_target = 0
        self._last_get_stats = 0
        self._last_connect_ok = False
        self._last_auth_ok = False
        self._successes = []
        self._target_state = None
        self._status = None
        self._stats = None
        self._disposed = False
        self._last_data = None
        self.model = model
        
        # Динамически определённые UUID
        self._service_uuid = None
        self._notify_uuid = None
        self._write_uuid = None
        
        # Get UUIDs for the specific model
        if model and model in SUPPORTED_MODELS:
            model_config = SUPPORTED_MODELS[model]
            self._service_uuid = model_config["uuid_service"]
            self._write_uuid = model_config["uuid_tx"]
            self._notify_uuid = model_config["uuid_rx"]
        else:
            # Default to RMC-M40S
            self._service_uuid = DEFAULT_SERVICE_UUID
            self._write_uuid = DEFAULT_WRITE_UUID
            self._notify_uuid = DEFAULT_NOTIFY_UUID

    async def command(self, command, params=[]):
        """Send a command to the multicooker."""
        if self._disposed:
            raise DisposedError()
        if not self._client or not self._client.is_connected:
            raise IOError("🔌 Не подключено")
        
        self._iter = (self._iter + 1) % 256
        _LOGGER.debug(f"📤 Отправка команды {command:02x}, данные: [{' '.join([f'{c:02x}' for c in params])}]")
        
        # Формируем пакет как в рабочей версии: [0x55, iter, command, data..., 0xAA]
        # Структура пакета:
        # 0x55 - заголовок
        # iter - итерация (последовательный номер)
        # command - команда
        # data... - данные
        # 0xAA - конец пакета
        data = bytes([0x55, self._iter, command] + list(params) + [0xAA])
        self._last_data = None
        
        try:
            await self._client.write_gatt_char(self._write_uuid, data)
            _LOGGER.debug(f"📋 Отправленный пакет: {data.hex().upper()}")
        except BleakError as e:
            _LOGGER.error(f"🚫 Ошибка отправки команды: {e}")
            raise IOError(f"Ошибка отправки команды: {e}")
        except Exception as e:
            _LOGGER.error(f"🚫 Неизвестная ошибка отправки: {e}")
            raise IOError(f"Неизвестная ошибка отправки: {e}")
        
        timeout_time = monotonic() + BLE_RECV_TIMEOUT
        while True:
            await asyncio.sleep(0.05)
            if self._last_data:
                r = self._last_data
                _LOGGER.debug(f"📥 Получен сырой ответ: {r.hex().upper()}")
                
                # Проверяем формат ответа
                if len(r) < 4 or r[0] != 0x55 or r[-1] != 0xAA:
                    _LOGGER.error(f"❌ Некорректный формат ответа: {r.hex().upper()}")
                    raise IOError("Некорректный формат ответа")
                
                # Проверяем итерацию (байт 1) - это идентификатор запроса
                # Он должен совпадать с текущей итерацией, чтобы убедиться,
                # что это ответ на наш запрос, а не на предыдущий
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
        
        # Проверяем команду в ответе (байт 2)
        if r[2] != command:
            _LOGGER.error(f"❌ Некорректная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
            raise IOError("Некорректная команда ответа")
        
        # Извлекаем чистые данные (без заголовка 0x55, итерации, команды и конца 0xAA)
        clean = bytes(r[3:-1])
        _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
        return clean

    def _rx_callback(self, sender, data):
        """Callback for receiving data."""
        self._last_data = data

    async def _connect(self):
        """Connect to the multicooker using working approach from skycooker_dev."""
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected:
            _LOGGER.debug("✅ Уже подключено к %s", self._mac)
            return
        
        # Ensure any previous connection is properly cleaned up
        await self._cleanup_previous_connections()
        
        try:
            _LOGGER.info("🔍 Поиск устройства %s...", self._mac)
            self._device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
            if not self._device:
                _LOGGER.error("❌ Устройство %s не найдено", self._mac)
                raise BleakError(f"Device {self._mac} not found")
            
            _LOGGER.info("🔌 Подключение к устройству: %s (%s)", self._device.name, self._mac)
            
            # Use max_attempts=3 like in working version
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self._device.name or "Unknown Device",
                max_attempts=3,  # Like in working version!
                disconnected_callback=self._handle_disconnect
            )
            _LOGGER.info("✅ Успешное подключение к %s", self._mac)
            
            # Auto-discover service UUIDs (like in working version)
            if not await self._discover_service_uuids():
                _LOGGER.warning("⚠️  Используем резервные UUID для подключения")
            
            # Start notification с найденной характеристикой
            if self._notify_uuid:
                try:
                    await asyncio.wait_for(
                        self._client.start_notify(self._notify_uuid, self._rx_callback),
                        timeout=5.0
                    )
                    _LOGGER.info("📡 Уведомления включены для %s через характеристику %s", self._mac, self._notify_uuid)
                except asyncio.TimeoutError:
                    _LOGGER.error("⏱️  Таймаут при подписке на уведомления")
                    await self._disconnect()
                    raise
            else:
                _LOGGER.error("❌ Не удалось определить характеристику для уведомлений")
                await self._disconnect()
                raise BleakError("Notification characteristic not found")
          
        except BleakError as e:
            error_str = str(e)
            _LOGGER.error(f"🚫 Ошибка Bluetooth: {e}")
            
            # More specific error handling for common Bluetooth issues
            if "connection slots" in error_str.lower() or "out of connection slots" in error_str.lower():
                _LOGGER.error("💡 Это может означать, что:")
                _LOGGER.error("   1. Bluetooth адаптер не настроен в Home Assistant")
                _LOGGER.error("   2. Bluetooth адаптер не подключен к системе")
                _LOGGER.error("   3. Нужно перезагрузить Bluetooth адаптер")
                _LOGGER.error("   4. Нужно добавить Bluetooth прокси (https://esphome.github.io/bluetooth-proxies/)")
                _LOGGER.error("   5. Проверьте, что мультиварка находится в режиме сопряжения")
            elif "not found" in error_str.lower():
                _LOGGER.error("💡 Устройство не найдено. Проверьте:")
                _LOGGER.error("   1. MAC адрес устройства правильный")
                _LOGGER.error("   2. Устройство включено и находится рядом")
                _LOGGER.error("   3. Устройство находится в режиме сопряжения")
                _LOGGER.error("   4. Bluetooth адаптер работает и обнаружен системой")
            elif "backend" in error_str.lower() or "proxy" in error_str.lower():
                _LOGGER.error("💡 Проблема с Bluetooth бэкендом. Проверьте:")
                _LOGGER.error("   1. Bluetooth интеграция включена в Home Assistant")
                _LOGGER.error("   2. Bluetooth адаптер правильно настроен")
                _LOGGER.error("   3. У вас есть хотя бы один работающий Bluetooth прокси")
                _LOGGER.error("   4. Проверьте логи Home Assistant на ошибки Bluetooth")
            elif "att error" in error_str.lower() or "0x0e" in error_str.lower():
                _LOGGER.error("💡 Ошибка ATT протокола. Это может означать:")
                _LOGGER.error("   1. Устройство не в режиме сопряжения")
                _LOGGER.error("   2. Неправильный ключ аутентификации")
                _LOGGER.error("   3. Устройство отвергло команду")
                _LOGGER.error("   4. Проблема с протоколом обмена")
                _LOGGER.error("💡 Попробуйте:")
                _LOGGER.error("   1. Переведите устройство в режим сопряжения")
                _LOGGER.error("   2. Проверьте правильность ключа аутентификации")
                _LOGGER.error("   3. Перезагрузите устройство")
                _LOGGER.error("   4. Попробуйте подключиться снова")
            
            await self._disconnect()
            raise
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка подключения: {e}")
            _LOGGER.debug("📋 Подробности ошибки:", exc_info=True)
            await self._disconnect()
            raise

    async def _discover_service_uuids(self):
        """Auto-discover service UUIDs like in working version."""
        try:
            _LOGGER.debug("🔍 Поиск сервисов и характеристик")
            
            # Try to get services
            try:
                services = await self._client.get_services()
            except AttributeError:
                services = self._client.services
            
            service_count = len(list(services))
            _LOGGER.debug("📦 Найдено сервисов: %s", service_count)
            
            for service in services:
                _LOGGER.debug("📡 Сервис: %s", service.uuid)
                
                # Check if this is Nordic UART Service
                if service.uuid.lower() == self._service_uuid.lower():
                    _LOGGER.info("✅ Найден Nordic UART Service: %s", service.uuid)
                    
                    # Find notification and write characteristics
                    for characteristic in service.characteristics:
                        _LOGGER.debug("📡 Характеристика: %s, свойства: %s",
                                    characteristic.uuid, characteristic.properties)
                        
                        if 'notify' in characteristic.properties:
                            self._notify_uuid = characteristic.uuid
                            _LOGGER.info("📢 Найдена характеристика для уведомлений: %s", self._notify_uuid)
                        
                        if 'write' in characteristic.properties or 'write-without-response' in characteristic.properties:
                            self._write_uuid = characteristic.uuid
                            _LOGGER.info("✏️  Найдена характеристика для записи: %s", self._write_uuid)
                    
                    # If found all necessary characteristics, return
                    if self._notify_uuid and self._write_uuid:
                        _LOGGER.info("✅ Все необходимые характеристики найдены для %s", self._mac)
                        return True
            
            # If not found, use default UUIDs
            if not self._service_uuid:
                _LOGGER.warning("⚠️  Nordic UART Service не найден, используем резервные UUID")
            
            return True
            
        except Exception as e:
            _LOGGER.error("❌ Ошибка определения UUID: %s", e)
            # Use default UUIDs in case of error
            return False

    async def _cleanup_previous_connections(self):
        """Clean up any previous connections to free up slots."""
        try:
            if self._client:
                if self._client.is_connected:
                    _LOGGER.debug("🧹 Очистка предыдущего соединения...")
                    await self._client.disconnect()
                self._client = None
            self._device = None
        except Exception as e:
            _LOGGER.warning(f"⚠️  Ошибка очистки предыдущего соединения: {e}")

    def _handle_disconnect(self, client):
        """Handle unexpected disconnections."""
        _LOGGER.warning("⚠️  Неожиданное отключение от мультиварки")
        self._last_connect_ok = False
        self._auth_ok = False

    async def auth(self):
        """Authenticate with the multicooker using correct key format."""
        try:
            # Get the AUTH command code for this specific model
            auth_command = get_model_constant(self.model, "command", "AUTH") or COMMAND_AUTH
            _LOGGER.info("🔑 Начало аутентификации...")
            
            # Use the correct key format: "0000000000000000" as hex string
            # Convert to bytes using bytes.fromhex() like in scripts/scaner/lib/auth.py
            if isinstance(self._key, str):
                # If key is provided as hex string, convert using bytes.fromhex()
                try:
                    key_bytes = list(bytes.fromhex(self._key))
                    _LOGGER.debug("🔑 Ключ конвертирован из hex строки: %s", key_bytes)
                except ValueError as e:
                    _LOGGER.error("🚫 Ошибка конвертации ключа: %s. Ключ должен быть hex строкой из 16 символов", e)
                    return False
            elif isinstance(self._key, list):
                # If key is already list of bytes, use as is
                key_bytes = self._key
                _LOGGER.debug("🔑 Ключ уже список байтов: %s", key_bytes)
            else:
                # Try to convert from other types
                try:
                    key_bytes = list(self._key)
                    _LOGGER.debug("🔑 Ключ конвертирован из другого типа: %s", key_bytes)
                except Exception as e:
                    _LOGGER.error("🚫 Ошибка конвертации ключа: %s", e)
                    return False
            
            # Verify key length (should be 8 bytes for 16 hex chars)
            if len(key_bytes) != 8:
                _LOGGER.error("🚫 Неправильная длина ключа: %s (ожидается 8 байт). Проверьте ключ аутентификации", len(key_bytes))
                return False
            
            _LOGGER.debug("🔑 Финальный ключ для аутентификации: %s", key_bytes)
            
            auth_data = await self.command(auth_command, key_bytes)
            if auth_data and auth_data[0] == 0x01:
                _LOGGER.info("🔐 Аутентификация успешна")
                return True
            else:
                _LOGGER.error("🚫 Аутентификация не удалась. Код ответа: %s", auth_data[0] if auth_data else 'None')
                if auth_data and auth_data[0] == 0x00:
                    _LOGGER.error("💡 Убедитесь, что мультиварка находится в режиме сопряжения")
                    _LOGGER.error("💡 Также проверьте:")
                    _LOGGER.error("   1. Ключ аутентификации правильный")
                    _LOGGER.error("   2. Устройство включено и готово к сопряжению")
                    _LOGGER.error("   3. Нет других активных подключений к устройству")
                    _LOGGER.error("   4. Попробуйте перезагрузить устройство")
                return False
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка аутентификации: {e}")
            _LOGGER.debug("📋 Подробности ошибки аутентификации:", exc_info=True)
            return False

    async def _disconnect(self):
        """Disconnect from the multicooker."""
        try:
            if self._client:
                was_connected = self._client.is_connected
                await self._client.disconnect()
                if was_connected: _LOGGER.debug("🔌 Отключено")
        finally:
            self._auth_ok = False
            self._device = None
            self._client = None

    async def disconnect(self):
        """Public disconnect method."""
        try:
            await self._disconnect()
        except:
            pass

    async def _connect_if_need(self):
        """Connect if needed with better error handling."""
        if self._client and not self._client.is_connected:
            _LOGGER.debug("🔌 Подключение потеряно")
            await self.disconnect()
        if not self._client or not self._client.is_connected:
            try:
                await self._connect()
                self._last_connect_ok = True
            except Exception as ex:
                error_str = str(ex).lower()
                # Проверяем, связано ли это с нехваткой слотов соединения
                if "connection slots" in error_str or "out of connection slots" in error_str:
                    _LOGGER.error("🚫 Bluetooth адаптер исчерпал лимит соединений. Попробуйте:")
                    _LOGGER.error("   1. Перезагрузите Bluetooth адаптер")
                    _LOGGER.error("   2. Уменьшите количество активных Bluetooth устройств")
                    _LOGGER.error("   3. Используйте дополнительный Bluetooth прокси")
                    _LOGGER.error("   4. Проверьте, что мультиварка находится в режиме сопряжения")
                elif "backend" in error_str or "proxy" in error_str or "not found" in error_str:
                    _LOGGER.error("🚫 Проблема с Bluetooth интеграцией. Проверьте:")
                    _LOGGER.error("   1. Bluetooth интеграция включена в Home Assistant")
                    _LOGGER.error("   2. Bluetooth адаптер правильно настроен и подключен")
                    _LOGGER.error("   3. У вас есть работающий Bluetooth прокси")
                    _LOGGER.error("   4. Проверьте логи Home Assistant на ошибки Bluetooth")
                    _LOGGER.error("   5. MAC адрес устройства правильный: %s", self._mac)
                else:
                    _LOGGER.error(f"🚫 Ошибка подключения: {ex}")
                await self.disconnect()
                self._last_connect_ok = False
                raise
        if not self._auth_ok:
            self._last_auth_ok = self._auth_ok = await self.auth()
            if not self._auth_ok:
                _LOGGER.error("🚫 Ошибка аутентификации. Нужно включить режим сопряжения на мультиварке.")
                _LOGGER.error("💡 Убедитесь, что:")
                _LOGGER.error("   1. Мультиварка включена")
                _LOGGER.error("   2. Мультиварка находится в режиме сопряжения")
                _LOGGER.error("   3. Ключ аутентификации правильный")
                _LOGGER.error("   4. Устройство находится рядом с адаптером")
                raise AuthError("Ошибка аутентификации")
            _LOGGER.debug("✅ Аутентификация успешна")

    async def _disconnect_if_need(self):
        """Disconnect if needed."""
        if not self.persistent:
            await self.disconnect()

    async def get_status(self):
        """Get the current status of the multicooker."""
        try:
            # Get the GET_STATUS command code for this specific model
            get_status_command = get_model_constant(self.model, "command", "GET_STATUS") or COMMAND_GET_STATUS
            
            # Add small delay before sending status command
            # Some devices need time after authentication
            await asyncio.sleep(0.5)
            
            data = await self.command(get_status_command)
            if len(data) >= 11:
                mode = data[0]
                temperature = data[2]
                hours = data[3]
                minutes = data[4]
                remaining_hours = data[5]
                remaining_minutes = data[6]
                auto_warm = data[7]
                status = data[8]
                
                # Get status text for logging
                status_text = get_model_constant(self.model, "status", status) or STATUS_CODES.get(status, f"Неизвестно ({status})")
                _LOGGER.debug(f"📊 Статус устройства: {status_text}")
                
                # When device is off, set default values
                if status == STATUS_OFF or status_text == "Выключена":
                    temperature = 0
                    hours = 0
                    minutes = 0
                    remaining_hours = 0
                    remaining_minutes = 0
                
                return {
                    'mode': mode,
                    'temperature': temperature,
                    'time_hours': hours,
                    'time_minutes': minutes,
                    'time_total': hours * 60 + minutes,
                    'remaining_hours': remaining_hours,
                    'remaining_minutes': remaining_minutes,
                    'remaining_time_total': remaining_hours * 60 + remaining_minutes,
                    'auto_warm_enable': bool(auto_warm),
                    'status': status,
                    'status_text': status_text
                }
            return None
        except Exception as e:
            error_str = str(e)
            if "att error" in error_str.lower() or "0x0e" in error_str.lower():
                _LOGGER.error(f"🚫 Ошибка ATT протокола при получении статуса: {e}")
                _LOGGER.error("💡 Устройство может не быть готово к командам. Попробуем позже...")
                return None
            else:
                _LOGGER.error(f"🚫 Ошибка получения статуса: {e}")
                return None

    async def set_mode(self, mode_id):
        """Set the cooking mode."""
        try:
            # Get the SET_MODE command code for this specific model
            set_mode_command = get_model_constant(self.model, "command", "SET_MODE") or COMMAND_SET_MODE
            await self.command(set_mode_command, [mode_id])
            
            # Get the mode name for logging
            mode_name = get_model_constant(self.model, "mode", mode_id) or MODES.get(mode_id, f"Неизвестно ({mode_id})")
            _LOGGER.info(f"✅ Режим установлен: {mode_id} ({mode_name})")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка установки режима: {e}")
            return False

    async def start(self):
        """Start the cooking program."""
        try:
            # Get the START command code for this specific model
            start_command = get_model_constant(self.model, "command", "START") or COMMAND_START
            await self.command(start_command)
            _LOGGER.info("✅ Программа запущена")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка запуска программы: {e}")
            return False

    async def stop(self):
        """Stop the cooking program."""
        try:
            # Get the STOP command code for this specific model
            stop_command = get_model_constant(self.model, "command", "STOP") or COMMAND_STOP
            await self.command(stop_command)
            _LOGGER.info("✅ Программа остановлена")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка остановки программы: {e}")
            return False

    async def update(self, tries=MAX_TRIES):
        """Update the multicooker status."""
        try:
            async with self._update_lock:
                if self._disposed: return
                _LOGGER.debug("🔄 Обновление статуса")
                  
                # Проверяем доступность перед попыткой обновления
                if not self.available:
                    _LOGGER.debug("📡 Устройство недоступно, пытаемся подключиться...")
                  
                try:
                    # Add timeout for connection attempt
                    await asyncio.wait_for(self._connect_if_need(), timeout=30.0)
                except asyncio.TimeoutError:
                    _LOGGER.error("⏱️  Таймаут подключения, устройство не отвечает")
                    await self.disconnect()
                    self.add_stat(False)
                    return False
                except Exception as e:
                    _LOGGER.error(f"🚫 Ошибка подключения: {e}")
                    await self.disconnect()
                    self.add_stat(False)
                    return False
                  
                # Проверяем, что подключение и авторизация прошли успешно
                if not self.available:
                    _LOGGER.error("🚫 Не удалось подключиться или авторизоваться")
                    await self.disconnect()
                    self.add_stat(False)
                    return False
                  
                _LOGGER.debug("✅ Подключение и авторизация успешны, запрашиваем статус...")
                  
                # Get current status with timeout
                try:
                    self._status = await asyncio.wait_for(self.get_status(), timeout=10.0)
                except asyncio.TimeoutError:
                    _LOGGER.error("⏱️  Таймаут получения статуса")
                    await self._disconnect_if_need()
                    self.add_stat(False)
                    return False
                  
                if self._status:
                    _LOGGER.debug(f"📊 Статус получен: режим={self._status.get('mode')}, температура={self._status.get('temperature')}°C")
                else:
                    _LOGGER.warning("⚠️  Не удалось получить статус")
                  
                await self._disconnect_if_need()
                self.add_stat(True)
                return True

        except Exception as ex:
            await self.disconnect()
            self.add_stat(False)
            if tries > 1:
                _LOGGER.debug(f"🚫 {type(ex).__name__}: {str(ex)}, повтор #{MAX_TRIES - tries + 1}")
                await asyncio.sleep(TRIES_INTERVAL)
                return await self.update(tries=tries-1)
            else:
                _LOGGER.warning(f"🚫 Не удалось обновить статус, {type(ex).__name__}: {str(ex)}")
                _LOGGER.debug(traceback.format_exc())
            return False

    def add_stat(self, value):
        """Add a success/failure statistic."""
        self._successes.append(value)
        if len(self._successes) > 100: self._successes = self._successes[-100:]

    @property
    def success_rate(self):
        """Get the success rate of commands."""
        if len(self._successes) == 0: return 0
        return int(100 * len([s for s in self._successes if s]) / len(self._successes))

    @property
    def available(self):
        """Check if the multicooker is available."""
        # Consider available if we had at least one successful connection
        # This prevents entities from becoming unavailable immediately after setup
        if self._last_connect_ok and self._last_auth_ok:
            return True
        # If we never connected successfully, check if we're currently trying to connect
        if self._client and self._client.is_connected:
            return True
        return False

    @property
    def current_status(self):
        """Get the current status."""
        return self._status

    @property
    def current_mode(self):
        """Get the current mode."""
        if self._status:
            return self._status.get('mode')
        return None

    @property
    def current_temperature(self):
        """Get the current temperature."""
        if self._status:
            return self._status.get('temperature')
        return None

    @property
    def remaining_time(self):
        """Get the remaining time."""
        if self._status:
            return self._status.get('remaining_time_total')
        return None

    @property
    def total_time(self):
        """Get the total cooking time."""
        if self._status:
            return self._status.get('time_total')
        return None

    @property
    def auto_warm_enabled(self):
        """Check if auto warm is enabled."""
        if self._status:
            return self._status.get('auto_warm_enable')
        return None

    @property
    def status_code(self):
        """Get the status code."""
        if self._status:
            return self._status.get('status')
        return None

    async def stop_connection(self):
        """Stop the connection."""
        if self._disposed: return
        await self._disconnect()
        self._disposed = True
        _LOGGER.info("🛑 Соединение остановлено")


class AuthError(Exception):
    """Authentication error."""
    pass


class DisposedError(Exception):
    """Connection disposed error."""
    pass