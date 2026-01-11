#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import traceback
from time import monotonic

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components import bluetooth

from .const import *
from .skycooker import SkyCooker, SkyCookerError

_LOGGER = logging.getLogger(__name__)


class SkyCookerConnection(SkyCooker):

    def __init__(self, mac, key, persistent=True, adapter=None, hass=None, model=None):
        super().__init__(model)
        self._device = None
        self._client = None
        self._mac = mac
        self._key = key
        self.persistent = persistent
        self.adapter = adapter
        self.hass = hass
        self._auth_ok = False
        self._sw_version = '1.8'
        self._iter = 0
        self._update_lock = asyncio.Lock()
        self._last_set_target = 0
        self._last_get_stats = 0
        self._last_connect_ok = False
        self._last_auth_ok = False
        self._successes = []
        self._target_mode = None
        self._auto_warm_enabled = True  # Значение по умолчанию для автоподогрева
        self._target_temperature = None
        self._target_main_hours = 0  # Значение по умолчанию для часов приготовления
        self._target_main_minutes = 10  # Значение по умолчанию для минут приготовления
        self._target_additional_hours = None
        self._target_additional_minutes = None
        self._status = None
        self._stats = None
        self._disposed = False
        self._last_data = None

    async def command(self, command, params=None):
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
        # For some commands like SELECT_MODE, the device may send asynchronous status updates
        # In such cases, we should check if the device actually processed the command correctly
        if r[2] != command:
            _LOGGER.warning(f"⚠️  Получена неожиданная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
            _LOGGER.warning(f"💡 Это может быть асинхронный ответ от устройства")
            
            # For SELECT_MODE and SET_MAIN_MODE commands, if we get a status update (0x06),
            # it might mean the device processed the command and sent its current status
            if command in [COMMAND_SELECT_MODE, COMMAND_SET_MAIN_MODE] and r[2] == COMMAND_GET_STATUS:
                _LOGGER.debug(f"📊 Устройство отправило обновление статуса после команды {command:02x}")
                _LOGGER.debug(f"💡 Вероятно, команда была обработана успешно")
                # Return a success response for compatibility
                clean = bytes([0x01])  # Success code
                _LOGGER.debug(f"📥 Очищенные данные ответа: 01 (успех)")
                return clean
            # For TURN_ON command, if we get a status update (0x06),
            # it might mean the device processed the command and sent its current status
            elif command == COMMAND_TURN_ON and r[2] == COMMAND_GET_STATUS:
                _LOGGER.debug(f"📊 Устройство отправило обновление статуса после команды {command:02x}")
                _LOGGER.debug(f"💡 Вероятно, команда была обработана успешно")
                # Return a success response for compatibility
                clean = bytes([0x01])  # Success code
                _LOGGER.debug(f"📥 Очищенные данные ответа: 01 (успех)")
                return clean
            elif command == COMMAND_GET_STATUS and r[2] in [COMMAND_SELECT_MODE, COMMAND_SET_MAIN_MODE, COMMAND_TURN_OFF]:
                # If we were expecting a status update but got a command response,
                # this might be a delayed response from a previous command
                _LOGGER.debug(f"📊 Получен отложенный ответ на команду {r[2]:02x} вместо статуса")
                _LOGGER.debug(f"💡 Вероятно, предыдущая команда была обработана успешно")
                # Return the response data for processing
                clean = bytes(r[3:-1])
                _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
                return clean
            else:
                _LOGGER.error(f"❌ Некорректная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
                raise IOError("Некорректная команда ответа")
        
        clean = bytes(r[3:-1])
        _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
        return clean

    def _rx_callback(self, sender, data):
        self._last_data = data

    async def _connect(self):
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected:
            _LOGGER.debug("✅ Уже подключено к мультиварке")
            return
        try:
            # Очистка предыдущих подключений
            await self._cleanup_previous_connections()
            
            self._device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
            if not self._device:
                _LOGGER.error("❌ Устройство %s не найдено", self._mac)
                raise IOError(f"Устройство {self._mac} не найдено")
            _LOGGER.debug("🔌 Подключение к мультиварке %s (%s)...", self._mac, self._device.name)
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self._device.name or "Unknown Device",
                max_attempts=5,
                retry_interval=1.0  # Добавляем задержку между попытками
            )
            _LOGGER.debug("✅ Успешно подключено к мультиварке %s", self._mac)
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

    auth = lambda self: super().auth(self._key)

    async def select_mode(self, mode, subprog=0):
        # Проверяем, поддерживается ли режим устройством
        # Режим MODE_STANDBY (ожидание) не может быть установлен напрямую, но может быть получен как текущий статус
        if mode != MODE_STANDBY and not self._is_mode_supported(mode):
            _LOGGER.error(f"❌ Попытка установить неподдерживаемый режим {mode}")
            raise ValueError(f"Режим {mode} не поддерживается устройством")
          
        # Проверяем, является ли режим MODE_NONE (индекс 15, 16)
        model_type = self.model_code
        if model_type and model_type in MODE_NAMES and mode < len(MODE_NAMES[model_type]):
            mode_constant = MODE_NAMES[model_type][mode]
            if mode_constant == MODE_NONE:
                _LOGGER.error(f"❌ Попытка установить режим MODE_NONE (индекс {mode})")
                raise ValueError(f"Режим {mode} не поддерживается устройством (MODE_NONE)")
            elif mode_constant == MODE_STANDBY:
                _LOGGER.error(f"❌ Попытка установить режим MODE_STANDBY (индекс {mode})")
                raise ValueError(f"Режим {mode} не поддерживается устройством (MODE_STANDBY)")
         
        # Вызываем метод базового класса для отправки команды
        _LOGGER.debug(f"📤 Отправка команды SELECT_MODE для режима {mode}")
        await super().select_mode(mode, subprog)
          
        # При выборе режима устанавливаем Number значения из MODE_DATA для текущего режима
        # ТОЛЬКО ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ ИЗМЕНЯЛ ИХ ВРУЧНУЮ
        model_type = self.model_code
        if model_type and model_type in MODE_DATA and mode < len(MODE_DATA[model_type]):
            mode_data = MODE_DATA[model_type][mode]
            
            # Устанавливаем температуру из MODE_DATA только если пользователь не установил свою
            target_temp_from_mode = mode_data[0]
            if target_temp_from_mode != 0:
                # Проверяем, установил ли пользователь свою температуру
                if not hasattr(self, '_target_temperature') or self._target_temperature is None:
                    self._target_temperature = target_temp_from_mode
               
            # Set cooking time from MODE_DATA only if user hasn't set custom cooking time
            # If user has already set custom cooking time, respect their choice
            if (not hasattr(self, '_target_main_hours') or self._target_main_hours is None or
                not hasattr(self, '_target_main_minutes') or self._target_main_minutes is None):
                self._target_main_hours = mode_data[1]
                self._target_main_minutes = mode_data[2]
               
            # Сбрасываем отложенный старт только если пользователь не установил его
            if getattr(self, '_target_additional_hours', None) is None and getattr(self, '_target_additional_minutes', None) is None:
                self._target_additional_hours = None
                self._target_additional_minutes = None

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
                self._last_connect_ok = True
            except Exception as ex:
                await self.disconnect()
                self._last_connect_ok = False
                _LOGGER.error(f"🚫 Ошибка подключения к мультиварке: {ex}")
                raise ex
        if not self._auth_ok:
            self._last_auth_ok = self._auth_ok = await self.auth()
            if not self._auth_ok:
                _LOGGER.error("🚫 Ошибка аутентификации. Необходимо включить режим сопряжения на мультиварке.")
                raise AuthError("Ошибка аутентификации")
            _LOGGER.debug("✅ Аутентификация успешна")
            self._sw_version = await self.get_version()
            _LOGGER.debug(f"📋 Версия ПО: {self._sw_version}")
            # try:
            #     await self.sync_time()
            # except Exception as e:
            #     _LOGGER.warning(f"⚠️  Ошибка синхронизации времени: {e}")

    async def _disconnect_if_need(self):
        if not self.persistent:
            await self.disconnect()

    async def update(self, tries=MAX_TRIES, force_stats=False, extra_action=None, commit=False):
        try:
            async with self._update_lock:
                if self._disposed: return None
                _LOGGER.debug("🔄 Обновление состояния мультиварки")
                if not self.available: force_stats = True
                await self._connect_if_need()
  
                if extra_action: await extra_action
  
                try:
                    self._status = await self.get_status()
                except Exception as e:
                    _LOGGER.warning(f"⚠️  Ошибка получения статуса: {e}")
                    self._status = None
                    raise
  
                # Метод update() теперь только читает статус и не отправляет команды
                # Все команды отправляются только в методах start() и start_delayed()
                # при явном нажатии пользователем "Старт" или "Отложенный старт"
                _LOGGER.debug("📊 Статус устройства успешно получен, команды не отправляются")

                await self._disconnect_if_need()
                self.add_stat(True)

                return True

        except Exception as ex:
            await self.disconnect()
            if hasattr(self, '_target_mode') and self._target_mode is not None and self._last_set_target + TARGET_TTL < monotonic():
                _LOGGER.warning(f"⚠️  Не удалось установить режим {self._target_mode} в течение {TARGET_TTL} секунд, прекращаю попытки")
                self._target_mode = None
            if type(ex) == AuthError: return None
            self.add_stat(False)
            if tries > 1 and extra_action is None:
                _LOGGER.debug(f"🚫 {type(ex).__name__}: {str(ex)}, повтор #{MAX_TRIES - tries + 1}")
                await asyncio.sleep(TRIES_INTERVAL)
                return await self.update(tries=tries-1, force_stats=force_stats, extra_action=extra_action, commit=commit)
            else:
                _LOGGER.warning(f"⚠️  Не удалось обновить состояние, {type(ex).__name__}: {str(ex)}")
                _LOGGER.debug(traceback.format_exc())
            return False

    def add_stat(self, value):
        self._successes.append(value)
        if len(self._successes) > 100: self._successes = self._successes[-100:]

    @property
    def success_rate(self):
        if len(self._successes) == 0: return 0
        return int(100 * len([s for s in self._successes if s]) / len(self._successes))

    async def commit(self):
        """Commit changes to the device."""
        _LOGGER.debug("Committing changes")
        await self.update()

    def _is_mode_supported(self, mode):
        """Проверяет, поддерживается ли режим устройством."""
        model_type = self.model_code
        if model_type and model_type in MODE_DATA:
            if mode >= len(MODE_DATA[model_type]):
                _LOGGER.warning(f"⚠️  Режим {mode} не поддерживается для модели {model_type}")
                return False
            # Режим MODE_STANDBY - это режим ожидания, его нельзя устанавливать напрямую
            # Но он может быть текущим состоянием устройства, поэтому разрешаем его как допустимое состояние
            if mode == MODE_STANDBY:
                _LOGGER.debug(f"📋 Режим 16 (ожидание) - это допустимое состояние устройства, но его нельзя устанавливать напрямую")
                return True
            if mode == MODE_NONE:
                _LOGGER.debug(f"📋 Режим 15 (ожидание) - это допустимое состояние устройства, но его нельзя устанавливать напрямую")
                return True
        return True

    async def stop(self):
        if self._disposed: return
        await self._disconnect()
        self._disposed = True
        _LOGGER.debug("Stopped.")

    @property
    def available(self):
        return self._last_connect_ok and self._last_auth_ok

    @property
    def last_connect_ok(self):
        return self._last_connect_ok

    @property
    def last_auth_ok(self):
        return self._last_auth_ok

    @property
    def auto_warm(self):
        if self._status:
            return self._status.auto_warm
        return None
    
    @property
    def subprog(self):
        if self._status:
            return self._status.subprog
        return None

    @property
    def current_mode(self):
        if self._status and self._status.is_on:
            return self._status.mode
        return None

    @property
    def target_temp(self):
        if hasattr(self, '_target_temperature') and self._target_temperature is not None:
            return self._target_temperature
        if self._status:
            if self._status.is_on:
                return self._status.target_temp
            else:
                return 25
        return None

    @property
    def target_mode(self):
        if hasattr(self, '_target_mode') and self._target_mode is not None:
            return self._target_mode
        else:
            if self._status and self._status.is_on:
                return self._status.mode
        return None

    @property
    def target_main_hours(self):
        """Return the target boil hours."""
        return self._target_main_hours

    @target_main_hours.setter
    def target_main_hours(self, value):
        """Set the target boil hours."""
        self._target_main_hours = value

    @property
    def target_main_minutes(self):
        """Return the target boil minutes."""
        return self._target_main_minutes

    @target_main_minutes.setter
    def target_main_minutes(self, value):
        """Set the target boil minutes."""
        self._target_main_minutes = value

    @property
    def target_additional_hours(self):
        """Return the target delayed start hours."""
        return getattr(self, '_target_additional_hours', None)

    @target_additional_hours.setter
    def target_additional_hours(self, value):
        """Set the target delayed start hours."""
        self._target_additional_hours = value

    @property
    def target_additional_minutes(self):
        """Return the target delayed start minutes."""
        return getattr(self, '_target_additional_minutes', None)

    @target_additional_minutes.setter
    def target_additional_minutes(self, value):
        """Set the target delayed start minutes."""
        self._target_additional_minutes = value

    @property
    def target_temperature(self):
        """Return the target temperature."""
        if not self._status: return 0
        return self._target_temperature if hasattr(self, '_target_temperature') else self._status.target_temp

    @target_temperature.setter
    def target_temperature(self, value):
        """Set the target temperature."""
        self._target_temperature = value

    @property
    def status(self):
        return self._status

    @property
    def connected(self):
        return True if self._client and self._client.is_connected else False

    @property
    def auth_ok(self):
        return self._auth_ok

    @property
    def sw_version(self):
        return self._sw_version if self._sw_version else "0.0"

    @property
    def sound_enabled(self):
        if not self._status: return None
        return self._status.sound_enabled

    @property
    def status_code(self):
        if not self._status: return None
        return self._status.status if self._status.is_on else STATUS_OFF

    @property
    def remaining_time(self):
        if not self._status: return None
        # If device is off, return 0
        if self._status.status == STATUS_OFF:
            return 0
        if self._status.status == STATUS_DELAYED_LAUNCH:
            # Return remaining time based on target_main_hours and target_main_minutes
            return (self._status.target_additional_hours * 60 + self._status.target_additional_minutes) + (self._status.target_main_hours * 60 + self._status.target_main_minutes)
        return self._status.target_main_hours * 60 + self._status.target_main_minutes

    @property
    def total_time(self):
        if not self._status: return None
        # For total time, we need to calculate based on status
        # If device is off, return 0
        if self._status.status == STATUS_OFF:
            return 0
        # If delayed start is active, include delayed start time in total time
        if self._status.status == STATUS_DELAYED_LAUNCH:
            return (self._status.target_additional_hours * 60 + self._status.target_additional_minutes) + (self._status.target_main_hours * 60 + self._status.target_main_minutes)
        # Otherwise, return only cooking time
        return self._status.target_main_hours * 60 + self._status.target_main_minutes

    @property
    def delayed_start_time(self):
        if not self._status: return None
        # For delayed start time, we need to calculate based on status
        # Return delayed start time only if delayed start is active (STATUS_DELAYED_LAUNCH)
        # Check if delayed start time is set in the status and device is in delayed launch mode
        if hasattr(self._status, 'target_additional_hours') and hasattr(self._status, 'target_additional_minutes'):
            if self._status.target_additional_hours is not None and self._status.target_additional_minutes is not None:
                # Return delayed start time only if device is in delayed launch mode
                if self._status.status == STATUS_DELAYED_LAUNCH:
                    return (self._status.target_additional_hours * 60 + self._status.target_additional_minutes)
        return 0

    @property
    def auto_warm_time(self):
        if not self._status: return None
        # For auto warm time, we need to calculate based on status
        # For now, return target_main_minutes and target_main_minutes if in auto warm mode, else 0
        return (self._status.target_additional_hours * 60 + self._status.target_additional_minutes) if self._status.status == STATUS_AUTO_WARM else 0

    @property
    def auto_warm_enabled(self):
        # Возвращаем значение флага, установленного пользователем, если оно есть
        if hasattr(self, '_auto_warm_enabled'):
            return self._auto_warm_enabled
        # Иначе возвращаем значение из статуса устройства
        if not self._status: return None
        return self._status.status == STATUS_AUTO_WARM

    async def set_boil_time(self, target_main_hours, target_main_minutes):
        target_main_hours = int(target_main_hours)
        target_main_minutes = int(target_main_minutes)
        _LOGGER.debug(f"Setting boil time to {target_main_hours}:{target_main_minutes:02d}")
        self._target_main_hours = target_main_hours
        self._target_main_minutes = target_main_minutes

    async def set_temperature(self, value):
        """Set target temperature."""
        value = int(value)
        _LOGGER.debug(f"Setting target temperature to {value}")
        if self._status and self._status.is_on:
            # If device is on, we need to send temperature command
            # For now, store it and it will be applied on next update
            self._target_temperature = value
        else:
            # If device is off, just store the target temperature
            # It will be applied when device is turned on
            self._target_temperature = value

    async def set_delayed_start(self, target_additional_hours, target_additional_minutes):
        """Set delayed start time."""
        target_additional_hours = int(target_additional_hours)
        target_additional_minutes = int(target_additional_minutes)
        _LOGGER.debug(f"Setting delayed start time to {target_additional_hours}:{target_additional_minutes:02d}")
        # Store the delayed start time for later use in start_delayed()
        self._target_additional_hours = target_additional_hours
        self._target_additional_minutes = target_additional_minutes

    async def start(self):
        """Start cooking with current settings."""
        _LOGGER.debug("Starting cooking with current settings")
        
        # Check if device is connected before proceeding
        if not self.connected:
            _LOGGER.error("❌ Устройство не подключено. Пожалуйста, проверьте соединение и повторите попытку.")
            raise SkyCookerError("Устройство не подключено")
          
        # Get the mode that the user has selected, not the current device mode
        # If user has selected a mode, use that. Otherwise, use current device mode.
        if hasattr(self, '_target_mode') and self._target_mode is not None:
            target_mode = self._target_mode
            _LOGGER.debug(f"🎯 Используется целевой режим {target_mode} (выбран пользователем)")
        else:
            target_mode = self._status.mode if self._status else 0
            _LOGGER.debug(f"🎯 Используется текущий режим устройства {target_mode}")
          
        # Check if auto warm is enabled and set the appropriate flag
        auto_warm_flag = 1 if getattr(self, '_auto_warm_enabled', False) else 0
        _LOGGER.debug(f"🔥 Автоподогрев {'включен' if auto_warm_flag else 'выключен'}")
        
        model_type = self.model_code
          
        # Validate target_mode - if it's invalid (e.g., MODE_STANDBY for MODEL_3), use mode 0 (Multi-chef)
        if model_type and model_type in MODE_DATA and target_mode >= len(MODE_DATA[model_type]):
            _LOGGER.warning(f"⚠️  Некорректный режим {target_mode} для модели {model_type}, использую режим 0 (Multi-chef)")
            target_mode = 0
          
        # Проверяем, поддерживается ли режим устройством
        if not self._is_mode_supported(target_mode):
            _LOGGER.error(f"❌ Режим {target_mode} не поддерживается устройством, использую режим 0 (Multi-chef)")
            target_mode = 0
          
        # Если текущий режим устройства - MODE_STANDBY (ожидание), и пользователь не выбрал режим,
        # используем режим 0 (Multi-chef) вместо режима MODE_STANDBY
        if target_mode == MODE_STANDBY:
            _LOGGER.warning(f"⚠️  Режим 16 (ожидание) не может быть установлен напрямую, использую режим 0 (Multi-chef)")
            target_mode = 0
        if target_mode == MODE_NONE:
            _LOGGER.warning(f"⚠️  Режим 15 (ожидание) не может быть установлен напрямую, использую режим 0 (Multi-chef)")
            target_mode = 0
          
        # Get current values from the connection (which should be set by Number components)
        # These values may have been modified by the user
        target_temp = self._target_temperature if hasattr(self, '_target_temperature') else None
        target_main_hours = self._target_main_hours if self._target_main_hours is not None else 0
        target_main_minutes = self._target_main_minutes if self._target_main_minutes is not None else 0
        
        # Get subprogram value if set by user (for models other than MODEL_3)
        target_subprogram = getattr(self, '_target_subprogram', 0)
        _LOGGER.debug(f"🎯 Используется подпрограмма {target_subprogram}")
        
        # Get subprogram value if set by user (for models other than MODEL_3)
        target_subprogram = getattr(self, '_target_subprogram', 0)
        _LOGGER.debug(f"🎯 Используется подпрограмма {target_subprogram}")
          
        # If user hasn't set custom temperature, use default from MODE_DATA
        if target_temp is None:
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                target_temp = MODE_DATA[model_type][target_mode][0]
          
        # If user hasn't set custom cooking time, use default from MODE_DATA
        # But if user has set custom cooking time, respect their choice
        if (target_main_hours == 0 and target_main_minutes == 0):
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                target_main_hours = MODE_DATA[model_type][target_mode][1]
                target_main_minutes = MODE_DATA[model_type][target_mode][2]
         
        # Ensure all values are integers (not None)
        target_main_hours = target_main_hours or 0
        target_main_minutes = target_main_minutes or 0
         
        _LOGGER.debug(f"Starting cooking: mode={target_mode}, temp={target_temp}, time={target_main_hours}:{target_main_minutes:02d}")
         
        # Check if device is in standby mode (MODE_STANDBY) or if we need to wake it up
        is_in_standby = self._status and self._status.mode == MODE_STANDBY
        current_device_mode = self._status.mode if self._status else None
        device_is_on = self._status.is_on if self._status else False
         
        try:
            # Connect if needed
            await self._connect_if_need()
             
            # Implement the correct sequence according to the requirements
            # 1. Если в режиме ожидания (MODE_STANDBY статус) - отправляем команду 09 с выбранным режимом
            #    и после получения ответа - отправляем COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами
            #    После ответа - отправляем COMMAND_TURN_ON = 0x03
            if is_in_standby:
                _LOGGER.debug("🔄 Устройство находится в режиме ожидания (MODE_STANDBY статус)")
                _LOGGER.debug("📤 Отправка команды 09 с выбранным режимом и подпрограммой")
                await self.select_mode(target_mode, target_subprogram)
                await asyncio.sleep(0.5)
                 
                _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, 0, 0, auto_warm_flag)
                await asyncio.sleep(0.3)
    
                _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
                await self.turn_on()
            # 2. Если на мультиварке уже выбран режим, и он совпадает с выбранным в интерфейсе
            #    отправляем COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами
            #    После ответа - отправляем COMMAND_TURN_ON = 0x03
            elif current_device_mode == target_mode and device_is_on:
                _LOGGER.debug(f"🔄 На мультиварке уже выбран режим {target_mode}, и он совпадает с выбранным в интерфейсе")
                _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, 0, 0, auto_warm_flag)
                await asyncio.sleep(0.3)
                 
                _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
                await self.turn_on()
            # 3. Если на мультиварке уже выбран режим, и он НЕ совпадает с выбранным в интерфейсе
            #    отправляем команду 09 с выбранным режимом
            #    и после получения ответа - отправляем COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами
            #    После ответа - отправляем COMMAND_TURN_ON = 0x03
            elif current_device_mode != target_mode:
                _LOGGER.debug(f"🔄 На мультиварке уже выбран режим {current_device_mode}, и он НЕ совпадает с выбранным в интерфейсе ({target_mode})")
                _LOGGER.debug("📤 Отправка команды 09 с выбранным режимом и подпрограммой")
                await self.select_mode(target_mode, target_subprogram)
                await asyncio.sleep(0.5)
                 
                _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, 0, 0, auto_warm_flag)
                await asyncio.sleep(0.3)
                    
                _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
                await self.turn_on()
            else:
                # Default case - send all commands
                _LOGGER.debug("🔄 Неизвестное состояние устройства, отправляем все команды")
                if is_in_standby:
                    _LOGGER.debug("🔄 Устройство находится в режиме ожидания, отправляем команду SELECT_MODE для пробуждения")
                    await self.select_mode(target_mode, target_subprogram)
                    await asyncio.sleep(0.5)
                 
                await self.select_mode(target_mode, target_subprogram)
                await asyncio.sleep(0.3)
                 
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, 0, 0, auto_warm_flag)
                await asyncio.sleep(0.3)
                 
                await self.turn_on()
             
            # Update status after starting
            self._status = await self.get_status()
              
            # Set target mode and temperature for future reference
            self._target_mode = target_mode
            self._target_temperature = target_temp
            self._target_main_hours = target_main_hours
            self._target_main_minutes = target_main_minutes
             
            _LOGGER.debug("✅ Приготовление успешно начато")
             
        except Exception as ex:
            _LOGGER.error(f"❌ Ошибка при запуске приготовления: {str(ex)}")
            # Add more detailed error handling
            if "Некорректный размер данных статуса" in str(ex):
                _LOGGER.error("💡 Проверьте соединение с устройством и повторите попытку")
            raise
        finally:
            await self._disconnect_if_need()

    async def enable_auto_warm(self):
        """Enable auto warm mode."""
        _LOGGER.debug("Enabling auto warm mode")
        # Автоподогрев - это просто флаг, который будет использоваться при запуске приготовления
        # Никакие команды не отправляются, просто устанавливаем флаг
        self._auto_warm_enabled = True
        _LOGGER.debug("✅ Auto warm mode enabled (flag set)")

    async def disable_auto_warm(self):
        """Disable auto warm mode."""
        _LOGGER.debug("Disabling auto warm mode")
        # Автоподогрев - это просто флаг, который будет использоваться при запуске приготовления
        # Никакие команды не отправляются, просто сбрасываем флаг
        self._auto_warm_enabled = False
        _LOGGER.debug("✅ Auto warm mode disabled (flag cleared)")

    async def stop_cooking(self):
        """Stop cooking."""
        _LOGGER.debug("Stopping cooking")
        
        # Turn off the device
        await self.turn_off()
           
        # Reset target state to default values
        self._target_mode = None
        self._target_temperature = None
        self._target_main_hours = 0  # Стандартное значение для часов приготовления
        self._target_main_minutes = 10  # Стандартное значение для минут приготовления
        self._target_additional_hours = 0  # Стандартное значение для часов отложенного старта
        self._target_additional_minutes = 0  # Стандартное значение для минут отложенного старта
        self._auto_warm_enabled = True  # Стандартное значение для автоподгрева

    async def start_delayed(self):
        """Start cooking with delayed start."""
        _LOGGER.debug("Starting cooking with delayed start")
        
        # Check if device is connected before proceeding
        if not self.connected:
            _LOGGER.error("❌ Устройство не подключено. Пожалуйста, проверьте соединение и повторите попытку.")
            raise SkyCookerError("Устройство не подключено")
        
        # Get subprogram value if set by user (for models other than MODEL_3)
        target_subprogram = getattr(self, '_target_subprogram', 0)
        _LOGGER.debug(f"🎯 Используется подпрограмма {target_subprogram}")
       
        # Get the mode that the user has selected, not the current device mode
        # If user has selected a mode, use that. Otherwise, use current device mode.
        if hasattr(self, '_target_mode') and self._target_mode is not None:
            target_mode = self._target_mode
            _LOGGER.debug(f"🎯 Используется целевой режим {target_mode} (выбран пользователем)")
        else:
            target_mode = self._status.mode if self._status else 0
            _LOGGER.debug(f"🎯 Используется текущий режим устройства {target_mode}")
         
        model_type = self.model_code
          
        # Validate target_mode - if it's invalid (e.g., 16 for MODEL_3), use mode 0 (Multi-chef)
        if model_type and model_type in MODE_DATA and target_mode >= len(MODE_DATA[model_type]):
            _LOGGER.warning(f"⚠️  Некорректный режим {target_mode} для модели {model_type}, использую режим 0 (Multi-chef)")
            target_mode = 0
         
        # Get current values from the connection (which should be set by Number components)
        # These values may have been modified by the user
        target_temp = self._target_temperature if hasattr(self, '_target_temperature') else None
        target_main_hours = self._target_main_hours if self._target_main_hours is not None else 0
        target_main_minutes = self._target_main_minutes if self._target_main_minutes is not None else 0
          
        # Get delayed start time from Number components (not from MODE_DATA)
        # These values should be set by the user through the Number entities
        target_additional_hours = 0
        target_additional_minutes = 0
        
        # Check if we have custom delayed start values set through Number components
        # These values are stored in the connection object
        if hasattr(self, '_target_additional_hours') and self._target_additional_hours is not None:
            target_additional_hours = self._target_additional_hours
        if hasattr(self, '_target_additional_minutes') and self._target_additional_minutes is not None:
            target_additional_minutes = self._target_additional_minutes
         
        # Check if auto warm is enabled and set the appropriate flag
        auto_warm_flag = 1 if getattr(self, '_auto_warm_enabled', False) else 0
        _LOGGER.debug(f"🔥 Автоподогрев {'включен' if auto_warm_flag else 'выключен'}")
          
        # If user hasn't set custom temperature, use default from MODE_DATA
        if target_temp is None:
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                target_temp = MODE_DATA[model_type][target_mode][0]
         
        # If user hasn't set custom cooking time, use default from MODE_DATA
        # But if user has set custom cooking time, respect their choice
        if (target_main_hours == 0 and target_main_minutes == 0):
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                target_main_hours = MODE_DATA[model_type][target_mode][1]
                target_main_minutes = MODE_DATA[model_type][target_mode][2]
        
        # Ensure all values are integers (not None)
        target_main_hours = target_main_hours or 0
        target_main_minutes = target_main_minutes or 0
        target_additional_hours = target_additional_hours or 0
        target_additional_minutes = target_additional_minutes or 0
         
        # Не суммируем время, а храним отдельно часы и минуты для готовки, отложенного старта и автоподогрева
        _LOGGER.debug(f"Delayed start: wait {target_additional_hours}:{target_additional_minutes:02d}, cook {target_main_hours}:{target_main_minutes:02d}")
         
        # Check if device is in standby mode (MODE_STANDBY) or if we need to wake it up
        is_in_standby = self._status and self._status.mode == MODE_STANDBY
        current_device_mode = self._status.mode if self._status else None
        device_is_on = self._status.is_on if self._status else False
         
        try:
            # Connect if needed
            await self._connect_if_need()
             
            # Implement the correct sequence according to the requirements
            # 1. Если в режиме ожидания (MODE_STANDBY статус) - отправляем команду 09 с выбранным режимом
            #    и после получения ответа - отправляем COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами
            #    После ответа - отправляем COMMAND_TURN_ON = 0x03
            if is_in_standby:
                _LOGGER.debug("🔄 Устройство находится в режиме ожидания (MODE_STANDBY статус)")
                _LOGGER.debug("📤 Отправка команды 09 с выбранным режимом и подпрограммой")
                await self.select_mode(target_mode, target_subprogram)
                await asyncio.sleep(0.5)
                 
                _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes)
                await asyncio.sleep(0.3)
                 
                _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
                await self.turn_on()
            # 2. Если на мультиварке уже выбран режим, и он совпадает с выбранным в интерфейсе
            #    отправляем COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами
            #    После ответа - отправляем COMMAND_TURN_ON = 0x03
            elif current_device_mode == target_mode and device_is_on:
                _LOGGER.debug(f"🔄 На мультиварке уже выбран режим {target_mode}, и он совпадает с выбранным в интерфейсе")
                _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes)
                await asyncio.sleep(0.3)
                 
                _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
                await self.turn_on()
            # 3. Если на мультиварке уже выбран режим, и он НЕ совпадает с выбранным в интерфейсе
            #    отправляем команду 09 с выбранным режимом
            #    и после получения ответа - отправляем COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами
            #    После ответа - отправляем COMMAND_TURN_ON = 0x03
            elif current_device_mode != target_mode:
                _LOGGER.debug(f"🔄 На мультиварке уже выбран режим {current_device_mode}, и он НЕ совпадает с выбранным в интерфейсе ({target_mode})")
                _LOGGER.debug("📤 Отправка команды 09 с выбранным режимом и подпрограммой")
                await self.select_mode(target_mode, target_subprogram)
                await asyncio.sleep(0.5)
                 
                _LOGGER.debug("📤 Отправка COMMAND_SET_MAIN_MODE = 0x05 с выбранными параметрами")
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes)
                await asyncio.sleep(0.3)
                 
                _LOGGER.debug("📤 Отправка COMMAND_TURN_ON = 0x03")
                await self.turn_on()
            else:
                # Default case - send all commands
                _LOGGER.debug("🔄 Неизвестное состояние устройства, отправляем все команды")
                if is_in_standby:
                    _LOGGER.debug("🔄 Устройство находится в режиме ожидания, отправляем команду SELECT_MODE для пробуждения")
                    await self.select_mode(target_mode, target_subprogram)
                    await asyncio.sleep(0.5)
                 
                await self.select_mode(target_mode, target_subprogram)
                await asyncio.sleep(0.3)
                 
                await self.set_main_mode(target_mode, target_subprogram, target_temp, target_main_hours, target_main_minutes, target_additional_hours, target_additional_minutes)
                await asyncio.sleep(0.3)
                 
                await self.turn_on()
             
            # Update status after starting
            self._status = await self.get_status()
              
            # Set target mode and temperature for future reference
            self._target_mode = target_mode
            self._target_temperature = target_temp
            self._target_main_hours = target_main_hours
            self._target_main_minutes = target_main_minutes
             
            _LOGGER.debug("✅ Отложенный старт успешно настроен")
        
        except Exception as ex:
            _LOGGER.error(f"❌ Ошибка при настройке отложенного старта: {str(ex)}")
            raise
        finally:
            await self._disconnect_if_need()
             
        # Clear delayed start values after successful setup
        if hasattr(self, '_target_additional_hours'):
            delattr(self, '_target_additional_hours')
        if hasattr(self, '_target_additional_minutes'):
            delattr(self, '_target_additional_minutes')

    async def set_target_temp(self, target_temp, operation_mode = None):
        if target_temp == self.target_temp: return
        _LOGGER.debug(f"Setting target temperature to {target_temp}")
        target_mode = self.target_mode
         
        # Get model type from model_code
        model_type = self.model_code
        if model_type is None:
            _LOGGER.error("Unknown model type")
            return
         
        # Find the appropriate mode based on temperature
        if target_temp < 35:
            target_mode = None
        else:
            # Find the mode that matches the target temperature
            for mode_idx, mode_data in enumerate(MODE_DATA.get(model_type, [])):
                if mode_data[0] == target_temp:
                    # Проверяем, поддерживается ли режим устройством
                    if self._is_mode_supported(mode_idx):
                        target_mode = mode_idx
                        # Set cooking time from MODE_DATA only if user hasn't set custom cooking time
                        if (not hasattr(self, '_target_main_hours') or self._target_main_hours is None or
                            not hasattr(self, '_target_main_minutes') or self._target_main_minutes is None):
                            self._target_main_hours = mode_data[1]
                            self._target_main_minutes = mode_data[2]
                        break
               
            # If no exact match found, use the closest mode
            if target_mode is None:
                closest_diff = float('inf')
                for mode_idx, mode_data in enumerate(MODE_DATA.get(model_type, [])):
                    # Проверяем, поддерживается ли режим устройством
                    if self._is_mode_supported(mode_idx):
                        diff = abs(mode_data[0] - target_temp)
                        if diff < closest_diff:
                            closest_diff = diff
                            target_mode = mode_idx
                            # Set cooking time from MODE_DATA only if user hasn't set custom cooking time
                            if (not hasattr(self, '_target_main_hours') or self._target_main_hours is None or
                                not hasattr(self, '_target_main_minutes') or self._target_main_minutes is None):
                                self._target_main_hours = mode_data[1]
                                self._target_main_minutes = mode_data[2]
         
        if target_mode != self.current_mode:
            _LOGGER.debug(f"Mode autoswitched to {target_mode}")
        self._target_temperature = target_temp
        self._target_mode = target_mode
        self._last_set_target = monotonic()

    async def set_target_mode(self, operation_mode):
        if operation_mode == self._target_mode: return
        _LOGGER.debug(f"Setting target mode to {operation_mode}")
           
        # Проверяем, поддерживается ли режим устройством
        if not self._is_mode_supported(operation_mode):
            _LOGGER.error(f"❌ Режим {operation_mode} не поддерживается устройством")
            return
          
        # Get MODE_DATA values for the selected mode
        model_type = self.model_code
        if model_type and model_type in MODE_DATA and operation_mode < len(MODE_DATA[model_type]):
            mode_data = MODE_DATA[model_type][operation_mode]
            _LOGGER.debug(f"Mode {operation_mode} data: temperature={mode_data[0]}, hours={mode_data[1]}, minutes={mode_data[2]}")
        
        # Set temperature from MODE_DATA only if user hasn't set custom temperature
            target_temp = mode_data[0]
            if hasattr(self, '_target_temperature') and self._target_temperature is not None:
                target_temp = self._target_temperature
               
            # Set cooking time from MODE_DATA only if user hasn't set custom cooking time
            # If user has already set custom cooking time, respect their choice
            target_main_hours = mode_data[1]
            target_main_minutes = mode_data[2]
            if hasattr(self, '_target_main_hours') and self._target_main_hours is not None:
                target_main_hours = self._target_main_hours
            if hasattr(self, '_target_main_minutes') and self._target_main_minutes is not None:
                target_main_minutes = self._target_main_minutes
                
            # Don't reset delayed start values if user has set them
            # Only reset if they are None
            if getattr(self, '_target_additional_hours', None) is None:
                self._target_additional_hours = None
            if getattr(self, '_target_additional_minutes', None) is None:
                self._target_additional_minutes = None
                
            # Set target mode and temperature directly
            self._target_mode = operation_mode
            self._target_temperature = target_temp
            self._last_set_target = monotonic()
               
            # Always update boil time to the default values from MODE_DATA
            self._target_main_hours = target_main_hours
            self._target_main_minutes = target_main_minutes
        else:
            # Fallback to old behavior if MODE_DATA is not available
            target_mode = operation_mode
            target_temp = self.target_temp
            if target_mode in [2]:
                target_temp = 0
            elif target_mode in [3, 4]:
                target_temp = 85
            elif target_temp is None:
                target_temp = 90
            else:
                if target_temp < 35:
                    target_temp = 35
            if target_temp != self.target_temp:
                _LOGGER.debug(f"Target temperature autoswitched to {target_temp}")
            # Set target mode and temperature directly
            self._target_mode = target_mode
            self._target_temperature = target_temp
            self._last_set_target = monotonic()


class AuthError(Exception):
    pass

class DisposedError(Exception):
    pass
