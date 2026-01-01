import asyncio
import logging
import traceback
from time import monotonic

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


class CookerConnection(SkyCooker):
    UUID_SERVICE = "6e400001-b5a3-f393e-0a9e-50e24dcca9e"
    UUID_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    UUID_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    CONNECTION_TIMEOUT = 10
    BLE_RECV_TIMEOUT = 1.5
    MAX_TRIES = 3
    TRIES_INTERVAL = 0.5
    STATS_INTERVAL = 15
    TARGET_TTL = 30

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
        self._sw_version = None
        self._iter = 0
        self._update_lock = asyncio.Lock()
        self._last_set_target = 0
        self._last_get_stats = 0
        self._last_connect_ok = False
        self._last_auth_ok = False
        self._successes = []
        self._target_state = None
        self._cook_hours = None
        self._cook_minutes = None
        self._wait_hours = None
        self._wait_minutes = None
        self._current_program = None
        self._status = None
        self._fresh_water = None
        self._colors = {}
        self._disposed = False
        self._last_data = None

    async def command(self, command, params=[]):
        if self._disposed:
            raise DisposedError()
        if not self._client or not self._client.is_connected:
            raise IOError("not connected")
        self._iter = (self._iter + 1) % 256
        _LOGGER.warning(f"Writing command {command:02x}, data: [{' '.join([f'{c:02x}' for c in params])}]")
        data = bytes([0x55, self._iter, command] + list(params) + [0xAA])
        _LOGGER.warning(f"Writing {data}")
        self._last_data = None
        await self._client.write_gatt_char(CookerConnection.UUID_TX, data)
        timeout_time = monotonic() + CookerConnection.BLE_RECV_TIMEOUT
        while True:
            await asyncio.sleep(0.05)
            if self._last_data:
                r = self._last_data
                if r[0] != 0x55 or r[-1] != 0xAA:
                    raise IOError("Invalid response magic")
                if r[1] == self._iter:
                    break
                else:
                    self._last_data = None
            if monotonic() >= timeout_time: raise IOError("Receive timeout")
        if r[2] != command:
            raise IOError("Invalid response command")
        clean = bytes(r[3:-1])
        _LOGGER.warning(f"Received: {' '.join([f'{c:02x}' for c in clean])}")
        return clean

    def _rx_callback(self, sender, data):
        _LOGGER.warning(f"Received (full): {' '.join([f'{c:02x}' for c in data])}")
        self._last_data = data

    async def _connect(self):
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected: return
        
        self._device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
        if not self._device:
            raise IOError(f"Device with MAC address {self._mac} not found")
            
        _LOGGER.warning("Connecting to the Cooker...")
        try:
            self._client = await establish_connection(
                BleakClient,
                self._device,
                self._mac,
                timeout=CookerConnection.CONNECTION_TIMEOUT
            )
            _LOGGER.warning("Connected to the Cooker")
            await self._client.start_notify(CookerConnection.UUID_RX, self._rx_callback)
            _LOGGER.warning("Subscribed to RX")
        except Exception as ex:
            _LOGGER.error(f"Failed to connect to device: {ex}")
            self._client = None
            raise

    auth = lambda self: super().auth(self._key)

    async def _disconnect(self):
        try:
            if self._client:
                was_connected = self._client.is_connected
                await self._client.disconnect()
                if was_connected: _LOGGER.warning("Disconnected")
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
            _LOGGER.warning("Connection lost")
            await self.disconnect()
        if not self._client or not self._client.is_connected:
            try:
                await self._connect()
                self._last_connect_ok = True
            except Exception as ex:
                await self.disconnect()
                self._last_connect_ok = False
                raise ex
        if not self._auth_ok:
            self._last_auth_ok = self._auth_ok = await self.auth()
            if not self._auth_ok:
                _LOGGER.error(f"Auth failed. You need to enable pairing mode on the Cooker.")
                raise AuthError("Auth failed")
            _LOGGER.warning("Auth ok")
            self._sw_version = await self.get_version()
            await self.sync_time()

    async def _disconnect_if_need(self):
        if not self.persistent and self.target_mode != SkyCooker.MODE_GAME:
            await self.disconnect()

    async def update(self, tries=MAX_TRIES, force_stats=False, extra_action=None, commit=False):
        try:
            async with self._update_lock:
                if self._disposed: return
                _LOGGER.warning(f"Updating")
                if not self.available: force_stats = True # Update stats after unavailable state
                await self._connect_if_need()

                if extra_action: await extra_action

                # Is there scheduled boil_time?
                self._status = await self.get_status()
                boil_time = self._status.cook_minutes
                if self._cook_hours != None and self._cook_hours != boil_time:
                    try:
                        _LOGGER.warning(f"Need to update boil time from {boil_time} to {self._cook_hours}")
                        boil_time = self._cook_hours
                        if self._target_state == None: # To return previous state
                            self._target_state = self._status.mode if self._status.is_on else None, self._status.target_temp
                            self._last_set_target = monotonic()
                        if self._status.is_on:
                            await self.turn_off()
                            await asyncio.sleep(0.2)
                        await self.set_main_mode(self._status.mode, self._status.target_temp, boil_time)
                        _LOGGER.info(f"Boil time is succesfully set to {boil_time}")
                    except Exception as ex:
                        _LOGGER.error(f"Can't update boil time ({type(ex).__name__}): {str(ex)}")
                    self._status = await self.get_status()
                self._cook_hours = None

                if commit: await self.commit()

                # If there is scheduled state
                if self._target_state != None:
                    target_mode, target_temp = self._target_state
                    # How to set mode?
                    if target_mode == None and self._status.is_on:
                        _LOGGER.info(f"State: {self._status} -> {self._target_state}")
                        _LOGGER.info("Need to turn off the Cooker...")
                        await self.turn_off()
                        _LOGGER.info("The Cooker was turned off")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    elif target_mode != None and not self._status.is_on:
                        _LOGGER.info(f"State: {self._status} -> {self._target_state}")
                        _LOGGER.info("Need to set mode and turn on the Cooker...")
                        await self.set_main_mode(target_mode, target_temp, boil_time)
                        _LOGGER.info("New mode was set")
                        await self.turn_on()
                        _LOGGER.info("The Cooker was turned on")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    elif target_mode != None  and (
                            target_mode != self._status.mode or
                            (target_mode in [SkyCooker.MODE_HEAT, SkyCooker.MODE_BOIL_HEAT] and
                            target_temp != self._status.target_temp)):
                        _LOGGER.info(f"State: {self._status} -> {self._target_state}")
                        _LOGGER.info("Need to switch mode of the Cooker and restart it")
                        await self.turn_off()
                        _LOGGER.info("The Cooker was turned off")
                        await asyncio.sleep(0.2)
                        await self.set_main_mode(target_mode, target_temp, boil_time)
                        _LOGGER.info("New mode was set")
                        await self.turn_on()
                        _LOGGER.info("The Cooker was turned on")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    else:
                        _LOGGER.warning(f"There is no reason to update state")
                    # Not scheduled anymore
                    self._target_state = None

                if self._last_get_stats + CookerConnection.STATS_INTERVAL < monotonic() or force_stats:
                    self._last_get_stats = monotonic()
                    self._wait_hours = await self.get_wait_hours()
                    self._wait_minutes = await self.get_wait_minutes()
                    self._cook_hours = await self.get_cook_hours()
                    self._cook_minutes = await self.get_cook_minutes()
                    self._current_program = await self.get_current_program()

                await self._disconnect_if_need()
                self.add_stat(True)
                return True

        except Exception as ex:
            await self.disconnect()
            if self._target_state != None and self._last_set_target + CookerConnection.TARGET_TTL < monotonic():
                _LOGGER.warning(f"Can't set mode to {self._target_state} for {CookerConnection.TARGET_TTL} seconds, stop trying")
                self._target_state = None
            if type(ex) == AuthError: return
            self.add_stat(False)
            if tries > 1 and extra_action == None:
                _LOGGER.warning(f"{type(ex).__name__}: {str(ex)}, retry #{CookerConnection.MAX_TRIES - tries + 1}")
                await asyncio.sleep(CookerConnection.TRIES_INTERVAL)
                return await self.update(tries=tries-1, force_stats=force_stats, extra_action=extra_action, commit=commit)
            else:
                _LOGGER.warning(f"Can't update status, {type(ex).__name__}: {str(ex)}")
                _LOGGER.warning(traceback.format_exc())
            return False

    def add_stat(self, value):
        self._successes.append(value)
        if len(self._successes) > 100: self._successes = self._successes[-100:]


    @staticmethod
    def get_program_name(mode_id):
        if mode_id == None: return "off"
        return SkyCooker.MODE_NAMES[mode_id]

    @property
    def success_rate(self):
        if len(self._successes) == 0: return 0
        return int(100 * len([s for s in self._successes if s]) / len(self._successes))

    async def _set_target_state(self, target_mode):
        self._target_state = target_mode
        self._last_set_target = monotonic()
        await self.update()

    async def cancel_target(self):
        self._target_state = None

    async def stop(self):
        if self._disposed: return
        await self._disconnect()
        self._disposed = True
        _LOGGER.warning("Stopped.")

    @property
    def available(self):
        return self._last_connect_ok and self._last_auth_ok

    @property
    def current_mode(self):
        if self._status and self._status.is_on:
            return self._status.mode
        return None

    @property
    def target_mode(self):
        if self._target_state:
            target_mode, target_temp = self._target_state
            return target_mode
        else:
            if self._status and self._status.is_on:
                return self._status.mode
        return None

    @property
    def target_program_str(self):
        return self.get_program_name(self.target_mode)

    async def set_target_program(self, operation_mode):
        """Set new operation mode."""
        if operation_mode == self.target_program_str: return # already set
        _LOGGER.warning(f"Setting target mode to {operation_mode}")
        target_mode = None
        # Get target mode ID
        vs = [k for k, v in SkyCooker.MODE_NAMES.items() if v == operation_mode]
        if len(vs) > 0: target_mode = vs[0]

        await self._set_target_state(target_mode)

    @property
    def connected(self):
        return True if self._client and self._client.is_connected else False

    @property
    def auth_ok(self):
        return self._auth_ok

    @property
    def sw_version(self):
        return self._sw_version

    @property
    def sound_enabled(self):
        if not self._status: return None
        return self._status.sound_enabled

    @property
    def cook_hours(self):
        if not self._status: return None
        return self._status.cook_hours

    @property
    def cook_minutes(self):
        if not self._status: return None
        return self._status.cook_minutes

    @property
    def wait_hours(self):
        if not self._status: return None
        return self._status.wait_hours

    @property
    def wait_minutes(self):
        if not self._status: return None
        return self._status.wait_minutes

    @property
    def current_program(self):
        if not self._status: return None
        return self._status.current_program

    @property
    def error_code(self):
        if not self._status: return None
        return self._status.error_code

    async def set_cook_hours(self, value):
        value = int(value)
        _LOGGER.info(f"Setting cook hours to {value}")
        self._cook_hours = value
        await self.update(commit=True)

    async def set_cook_minutes(self, value):
        value = int(value)
        _LOGGER.info(f"Setting cook minutes to {value}")
        self._cook_minutes = value
        await self.update(commit=True)

    async def set_wait_hours(self, value):
        value = int(value)
        _LOGGER.info(f"Setting wait hours to {value}")
        self._wait_hours = value
        await self.update(commit=True)

    async def set_wait_minutes(self, value):
        value = int(value)
        _LOGGER.info(f"Setting wait minutes to {value}")
        self._wait_minutes = value
        await self.update(commit=True)

    async def set_current_program(self, value):
        value = int(value)
        _LOGGER.info(f"Setting current program to {value}")
        self._current_program = value
        await self.update(commit=True)


class AuthError(Exception):
    pass

class DisposedError(Exception):
    pass
