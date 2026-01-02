import calendar
import logging
import time
from abc import abstractmethod
from collections import namedtuple
from datetime import datetime, timedelta
from struct import pack, unpack

_LOGGER = logging.getLogger(__name__)


class SkyCooker():
    MODELS_0 = 0
    MODELS_1 = 1
    MODELS_2 = 2
    MODELS_3 = 3
    MODELS_4 = 4
    MODELS_5 = 5
    MODELS_6 = 6
    MODELS_7 = 7

    # Model types - currently only RMC-M40S is fully supported
    MODEL_TYPE = {
        "RMC-M40S": MODELS_3,  # Primary supported model
        # Other models commented out for now
        # "RMC-M42S": MODELS_3,
        # "RMC-M92S": MODELS_6, "RMC-M92S-A": MODELS_6, "RMC-M92S-C": MODELS_6, "RMC-M92S-E": MODELS_6,
        # "RMC-M222S": MODELS_7, "RMC-M222S-A": MODELS_7,
        # "RMC-M223S": MODELS_7,"RMC-M223S-E": MODELS_7,
        # "RMC-M224S": MODELS_7,"RFS-KMC001": MODELS_7,
        # "RMC-M225S": MODELS_7,"RMC-M225S-E": MODELS_7,
        # "RMC-M226S": MODELS_7,"RMC-M226S-E": MODELS_7,"JK-MC501": MODELS_7,"NK-MC10": MODELS_7,
        # "RMC-M227S": MODELS_7,
        # "RMC-M800S": MODELS_0,
        # "RMC-M903S": MODELS_5, "RFS-KMC005": MODELS_5,
        # "RMC-961S": MODELS_4,
        # "RMC-CBD100S": MODELS_1,
        # "RMC-CBF390S": MODELS_2,
    }

    # Basic modes (for kettles)
    MODE_BOIL = 0x00
    MODE_HEAT = 0x01
    MODE_BOIL_HEAT = 0x02
    MODE_LAMP = 0x03
    MODE_GAME = 0x04
    
    # Multicooker modes (for RMC-M40S and similar)
    MODE_STANDBY = 0x00
    MODE_MULTI_CHEF = 0x01
    MODE_RICE_CEREALS = 0x02
    MODE_LANGUOR = 0x03
    MODE_PILAF = 0x04
    MODE_FRYING = 0x05
    MODE_STEWING = 0x06
    MODE_PASTA = 0x07
    MODE_BAKING = 0x08
    MODE_STEAMING = 0x09
    MODE_YOGURT = 0x0A
    MODE_DOUGH = 0x0B
    MODE_KEEP_WARM = 0x0C
    MODE_YOGURT2 = 0x0D
    MODE_BAKING2 = 0x0E
    MODE_STEAMING2 = 0x0F
    MODE_STEWING2 = 0x10
    MODE_FRYING2 = 0x11
    MODE_PILAF2 = 0x12
    MODE_LANGUOR2 = 0x13
    MODE_RICE_CEREALS2 = 0x14
    MODE_MULTI_CHEF2 = 0x15
    
    MODE_NAMES = {
        # Basic modes
        MODE_BOIL: "Boil",
        MODE_HEAT: "Heat",
        MODE_BOIL_HEAT: "Boil+Heat",
        MODE_LAMP: "Lamp",
        MODE_GAME: "Light",
        # Multicooker modes
        MODE_STANDBY: "Standby",
        MODE_MULTI_CHEF: "Multi-chef",
        MODE_RICE_CEREALS: "Rice/Cereals",
        MODE_LANGUOR: "Languor",
        MODE_PILAF: "Pilaf",
        MODE_FRYING: "Frying",
        MODE_STEWING: "Stewing",
        MODE_PASTA: "Pasta",
        MODE_BAKING: "Baking",
        MODE_STEAMING: "Steaming",
        MODE_YOGURT: "Yogurt",
        MODE_DOUGH: "Dough",
        MODE_KEEP_WARM: "Keep Warm",
        MODE_YOGURT2: "Yogurt 2",
        MODE_BAKING2: "Baking 2",
        MODE_STEAMING2: "Steaming 2",
        MODE_STEWING2: "Stewing 2",
        MODE_FRYING2: "Frying 2",
        MODE_PILAF2: "Pilaf 2",
        MODE_LANGUOR2: "Languor 2",
        MODE_RICE_CEREALS2: "Rice/Cereals 2",
        MODE_MULTI_CHEF2: "Multi-chef 2"
    }

    LIGHT_BOIL = 0x00
    LIGHT_LAMP = 0x01
    LIGHT_SYNC = 0xC8
    LIGHT_NAMES = {
        LIGHT_BOIL: "boiling_light",
        LIGHT_LAMP: "lamp_light",
        LIGHT_SYNC: "sync_light"
    }

    MAX_TEMP = 90
    MIN_TEMP = 35

    COMMAND_GET_VERSION = 0x01
    # COMMAND_UNKNOWN1 = 0x02 # [] -> [00] ???
    COMMAND_TURN_ON = 0x03
    COMMAND_TURN_OFF = 0x04
    COMMAND_SET_MAIN_MODE = 0x05
    COMMAND_GET_STATUS = 0x06
    COMMAND_GET_AUTO_OFF_HOURS = 0x30
    COMMAND_SET_COLORS = 0x32
    COMMAND_GET_COLORS = 0x33
    COMMAND_SET_COLOR_INTERVAL = 0x34
    COMMAND_GET_LIGHT_SWITCH = 0x35
    COMMAND_COMMIT_SETTINGS = 0x36
    COMMAND_SET_LIGHT_SWITCH = 0x37
    COMMAND_IMPULSE_COLOR = 0x38
    COMMAND_SET_AUTO_OFF_HOURS = 0x39
    COMMAND_SET_SOUND = 0x3C
    COMMAND_GET_STATS1 = 0x47
    COMMAND_GET_STATS2 = 0x50
    COMMAND_SET_FRESH_WATER = 0x51
    COMMAND_GET_FRESH_WATER = 0x52
    COMMAND_SYNC_TIME = 0x6E
    COMMAND_GET_TIME = 0x6F
    COMMAND_GET_SCHEDULE_RECORD = 0x70
    COMMAND_ADD_SCHEDULE_RECORD = 0x71
    COMMAND_GET_SCHEDULE_COUNT = 0x73
    COMMAND_DEL_SCHEDULE_RECORD  = 0x74
    COMMAND_AUTH = 0xFF

    Status = namedtuple("Status", ["mode","is_on", "error_code", "current_temp", "target_temp", "cook_hours", "cook_minutes", "wait_hours", "wait_minutes"])
    Stats = namedtuple("Stats", ["ontime", "energy_wh", "heater_on_count", "user_on_count"])
    FreshWaterInfo = namedtuple("FreshWaterInfo", ["is_on", "unknown1", "water_freshness_hours"])


    def __init__(self, model):
        _LOGGER.info(f"🔧 Initializing SkyCooker with model: {model}")
        self.model = model
        self.model_code = self.get_model_code(model)
        if not self.model_code:
            _LOGGER.error(f"❌ Unknown Cooker model: {model}")
            raise SkyCookerError(f"Unknown Cooker model: {model}")
        _LOGGER.info(f"✅ Model recognized as code: {self.model_code}")

    @staticmethod
    def get_model_code(model):
        if model in SkyCooker.MODEL_TYPE:
            return SkyCooker.MODEL_TYPE[model]
        if model.endswith("-E"):
            return SkyCooker.MODEL_TYPE.get(model[:-2], None)
        return None

    @abstractmethod
    async def command(self, command, params=[]):
        pass

    async def auth(self, key):
        _LOGGER.info(f"🔑 Starting authentication with key: {key.hex() if hasattr(key, 'hex') else key}")
        try:
            r = await self.command(SkyCooker.COMMAND_AUTH, key)
            if r is None:
                _LOGGER.error(f"❌ Authentication failed - no response received")
                return False
            ok = r[0] != 0
            if ok:
                _LOGGER.info(f"✅ Authentication successful")
            else:
                _LOGGER.warning(f"⚠️ Authentication failed - response: {r}")
            return ok
        except Exception as e:
            _LOGGER.error(f"❌ Authentication error: {e}")
            raise

    async def get_version(self):
        _LOGGER.info(f"📋 Requesting device version...")
        try:
            r = await self.command(SkyCooker.COMMAND_GET_VERSION)
            if r is None:
                _LOGGER.error(f"❌ Failed to get version - no response received")
                raise SkyCookerError("Failed to get version - no response")
            
            # Проверяем длину ответа
            if len(r) < 2:
                _LOGGER.error(f"❌ Invalid version response length: {len(r)} bytes")
                raise SkyCookerError(f"Invalid version response length: {len(r)} bytes")
            
            major, minor = unpack("BB", r[:2])
            ver = f"{major}.{minor}"
            _LOGGER.info(f"✅ Device version: {ver}")
            return (major, minor)
        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ Version request timeout")
            raise SkyCookerError("Version request timeout")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to get version: {e}")
            raise

    async def turn_on(self):
        _LOGGER.info(f"⚡ Attempting to turn on device (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                r = await self.command(SkyCooker.COMMAND_TURN_ON)
                if r is None:
                    _LOGGER.error(f"❌ Failed to turn on device - no response received")
                    raise SkyCookerError("can't turn on - no response")
                if r[0] != 1:
                    _LOGGER.error(f"❌ Failed to turn on device - response: {r}")
                    raise SkyCookerError("can't turn on")
                _LOGGER.info(f"✅ Device turned on successfully")
            else:
                _LOGGER.warning(f"⚠️ turn_on is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
        except Exception as e:
            _LOGGER.error(f"❌ Error during turn_on: {e}")
            raise

    async def turn_off(self):
        _LOGGER.info(f"🛑 Attempting to turn off device (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                r = await self.command(SkyCooker.COMMAND_TURN_OFF)
                if r is None:
                    _LOGGER.error(f"❌ Failed to turn off device - no response received")
                    raise SkyCookerError("can't turn off - no response")
                if r[0] != 1:
                    _LOGGER.error(f"❌ Failed to turn off device - response: {r}")
                    raise SkyCookerError("can't turn off")
                _LOGGER.info(f"✅ Device turned off successfully")
            else:
                _LOGGER.warning(f"⚠️ turn_off is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
        except Exception as e:
            _LOGGER.error(f"❌ Error during turn_off: {e}")
            raise

    async def set_main_mode(self, mode, target_temp = 0, boil_time = 0):
        _LOGGER.info(f"⚙️ Setting main mode: mode={mode} ({SkyCooker.MODE_NAMES.get(mode, 'Unknown')}), target_temp={target_temp}, boil_time={boil_time}")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                # Pack data for RMC-M40S
                data = pack("BxBxxxxxxxxxxBxx", int(mode), int(target_temp), int(0x80 + boil_time))
                _LOGGER.debug(f"📦 Packed data for RMC-M40S: {data.hex()}")
            else:
                _LOGGER.warning(f"⚠️ set_main_mode is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
                return
            
            # Send command
            r = await self.command(SkyCooker.COMMAND_SET_MAIN_MODE, data)
            if r is None:
                _LOGGER.error(f"❌ Failed to set mode - no response received")
                raise SkyCookerError("can't set mode - no response")
            if r[0] != 1:
                _LOGGER.error(f"❌ Failed to set mode - response: {r}")
                raise SkyCookerError("can't set mode")
            
            _LOGGER.info(f"✅ Mode set successfully: mode={mode} ({SkyCooker.MODE_NAMES.get(mode, 'Unknown')}), target_temp={target_temp}, boil_time={boil_time}")
        except Exception as e:
            _LOGGER.error(f"❌ Error setting main mode: {e}")
            raise

    async def get_status(self):
        _LOGGER.info(f"📊 Requesting device status (model code: {self.model_code})")
        try:
            r = await self.command(SkyCooker.COMMAND_GET_STATUS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get status - no response received")
                raise SkyCookerError("Failed to get status - no response")
            _LOGGER.debug(f"📡 Raw status response: {r.hex() if hasattr(r, 'hex') else r}")
            
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                # For RMC-M40S, try to unpack detailed status
                try:
                    # Try to unpack with more fields for RMC-M40S
                    if len(r) >= 9:
                        # Multicooker status format: mode, is_on, current_temp, target_temp, cook_hours, cook_minutes, wait_hours, wait_minutes
                        mode, is_on, current_temp, target_temp, cook_hours, cook_minutes, wait_hours, wait_minutes = unpack("<B?BBBBBBB", r[:9])
                        _LOGGER.debug(f"📦 Parsed RMC-M40S status: mode={mode}, is_on={is_on}, temp={current_temp}/{target_temp}, cook={cook_hours}:{cook_minutes}, wait={wait_hours}:{wait_minutes}")
                    elif len(r) >= 4:
                        # Fallback to basic format but try to extract available data
                        mode, is_on, current_temp, target_temp = unpack("<B?BB", r[:4])
                        cook_hours, cook_minutes, wait_hours, wait_minutes = 0, 0, 0, 0
                        _LOGGER.debug(f"📦 Parsed basic RMC-M40S status: mode={mode}, is_on={is_on}, temp={current_temp}/{target_temp}")
                    else:
                        # Minimal data
                        mode, is_on = unpack("<B?", r[:2])
                        current_temp, target_temp, cook_hours, cook_minutes, wait_hours, wait_minutes = 0, 0, 0, 0, 0, 0
                        _LOGGER.debug(f"📦 Parsed minimal RMC-M40S status: mode={mode}, is_on={is_on}")
                    
                    status = SkyCooker.Status(
                        mode=mode,
                        is_on=is_on,
                        error_code=None,
                        current_temp=current_temp,
                        target_temp=target_temp,
                        cook_hours=cook_hours,
                        cook_minutes=cook_minutes,
                        wait_hours=wait_hours,
                        wait_minutes=wait_minutes
                    )
                except Exception as e:
                    _LOGGER.error(f"❌ Error unpacking RMC-M40S status: {e}")
                    # Fallback to minimal status
                    status = SkyCooker.Status(
                        mode=0,
                        is_on=False,
                        error_code=None,
                        current_temp=0,
                        target_temp=0,
                        cook_hours=0,
                        cook_minutes=0,
                        wait_hours=0,
                        wait_minutes=0
                    )
            else:
                _LOGGER.warning(f"⚠️ get_status is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
                return None
            
            _LOGGER.info(f"✅ Status retrieved: mode={status.mode} ({SkyCooker.MODE_NAMES.get(status.mode, 'Unknown')}), is_on={status.is_on}, temp={status.current_temp}/{status.target_temp}, cook={status.cook_hours}:{status.cook_minutes}, wait={status.wait_hours}:{status.wait_minutes}")
            return status
            
        except Exception as e:
            _LOGGER.error(f"❌ Failed to get status: {e}")
            # Return safe default status
            return SkyCooker.Status(
                mode=0,
                is_on=False,
                error_code=None,
                current_temp=0,
                target_temp=0,
                cook_hours=0,
                cook_minutes=0,
                wait_hours=0,
                wait_minutes=0
            )

    async def sync_time(self):
        _LOGGER.info(f"⏰ Synchronizing device time (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                t = time.localtime()
                offset = calendar.timegm(t) - calendar.timegm(time.gmtime(time.mktime(t)))
                now = int(time.time())
                data = pack("<ii", now, offset)
                _LOGGER.debug(f"📦 Packed time data: timestamp={now}, offset={offset}")
                
                # Use shorter timeout for time sync to avoid blocking
                original_timeout = CookerConnection.BLE_RECV_TIMEOUT
                CookerConnection.BLE_RECV_TIMEOUT = 3.0  # Reduce timeout to 3 seconds
                
                try:
                    r = await self.command(SkyCooker.COMMAND_SYNC_TIME, data)
                    if r is None:
                        _LOGGER.error(f"❌ Failed to sync time - no response received")
                        raise SkyCookerError("can't sync time - no response")
                    if r[0] != 0:
                        _LOGGER.error(f"❌ Failed to sync time - response: {r}")
                        raise SkyCookerError("can't sync time")
                    
                    _LOGGER.info(f"✅ Time synchronized: {datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')} (GMT{offset/60/60:+.2f})")
                finally:
                    # Restore original timeout
                    CookerConnection.BLE_RECV_TIMEOUT = original_timeout
                    
            else:
                _LOGGER.warning(f"⚠️ sync_time is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
        except Exception as e:
            _LOGGER.warning(f"⚠️ Time synchronization failed (non-critical): {e}")
            # Don't raise exception for time sync failure - it's not critical

    async def get_time(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_TIME)
            t, offset = unpack("<ii", r)
            _LOGGER.info(f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
            return t, offset
        else:
            _LOGGER.debug(f"get_time is not supported by this model")

    async def commit(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_COMMIT_SETTINGS)
            if r is None: raise SkyCookerError("can't commit settings - no response")
            if r[0] != 1: raise SkyCookerError("can't commit settings")
            _LOGGER.info(f"Settings committed")
        else:
            _LOGGER.debug(f"commit is not supported by this model")


    async def get_wait_hours(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get wait hours - no response received")
                return None
            hours, = unpack("<H", r)
            _LOGGER.info(f"Wait hours={hours}")
            return hours
        else:
            _LOGGER.debug(f"get_wait_hours is not supported by this model")

    async def get_wait_minutes(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get wait minutes - no response received")
                return None
            minutes, = unpack("<H", r)
            _LOGGER.info(f"Wait minutes={minutes}")
            return minutes
        else:
            _LOGGER.debug(f"get_wait_minutes is not supported by this model")

    async def get_cook_hours(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get cook hours - no response received")
                return None
            hours, = unpack("<H", r)
            _LOGGER.info(f"Cook hours={hours}")
            return hours
        else:
            _LOGGER.debug(f"get_cook_hours is not supported by this model")

    async def get_cook_minutes(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get cook minutes - no response received")
                return None
            minutes, = unpack("<H", r)
            _LOGGER.info(f"Cook minutes={minutes}")
            return minutes
        else:
            _LOGGER.debug(f"get_cook_minutes is not supported by this model")

    async def get_current_program(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get current program - no response received")
                return None
            program, = unpack("<H", r)
            _LOGGER.info(f"Current program={program}")
            return program
        else:
            _LOGGER.debug(f"get_current_program is not supported by this model")

    async def set_target_program(self, program):
        """Set the target program for multicooker."""
        _LOGGER.info(f"🎯 Setting target program: {program} (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                if program is None:
                    # Turn off
                    _LOGGER.debug(f"🔧 Turning off device (program=None)")
                    await self.turn_off()
                else:
                    # Set the program
                    _LOGGER.debug(f"🔧 Setting program to: {program} ({SkyCooker.MODE_NAMES.get(program, 'Unknown')})")
                    await self.set_main_mode(program)
            else:
                _LOGGER.warning(f"⚠️ set_target_program is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
        except Exception as e:
            _LOGGER.error(f"❌ Error setting target program: {e}")
            raise

    async def set_target_temperature(self, temperature):
        """Set the target temperature for multicooker."""
        _LOGGER.info(f"🌡️ Setting target temperature: {temperature}°C (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                # Get current mode and set it with new temperature
                _LOGGER.debug(f"🔧 Getting current status to preserve mode...")
                status = await self.get_status()
                if status:
                    _LOGGER.debug(f"🔧 Current mode: {status.mode} ({SkyCooker.MODE_NAMES.get(status.mode, 'Unknown')}), setting temperature to {temperature}°C")
                    await self.set_main_mode(status.mode, temperature)
                else:
                    _LOGGER.warning(f"⚠️ Could not get current status, temperature setting may fail")
            else:
                _LOGGER.warning(f"⚠️ set_target_temperature is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
        except Exception as e:
            _LOGGER.error(f"❌ Error setting target temperature: {e}")
            raise

    async def set_cook_hours(self, hours):
        """Set the cook hours for multicooker."""
        if self.model_code in [SkyCooker.MODELS_3]:
            # This would need specific command implementation based on protocol
            _LOGGER.info(f"set_cook_hours: {hours} hours")
            # TODO: Implement actual command
        else:
            _LOGGER.debug(f"set_cook_hours is not supported by this model")

    async def set_cook_minutes(self, minutes):
        """Set the cook minutes for multicooker."""
        if self.model_code in [SkyCooker.MODELS_3]:
            # This would need specific command implementation based on protocol
            _LOGGER.info(f"set_cook_minutes: {minutes} minutes")
            # TODO: Implement actual command
        else:
            _LOGGER.debug(f"set_cook_minutes is not supported by this model")

    async def start_cooking(self):
        """Start cooking with current settings."""
        _LOGGER.info(f"🔥 Starting cooking (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                _LOGGER.debug(f"🔧 Turning on device to start cooking...")
                await self.turn_on()
                _LOGGER.info(f"✅ Cooking started successfully")
            else:
                _LOGGER.warning(f"⚠️ start_cooking is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
        except Exception as e:
            _LOGGER.error(f"❌ Error starting cooking: {e}")
            raise

    async def stop_cooking(self):
        """Stop cooking."""
        _LOGGER.info(f"🛑 Stopping cooking (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_3) is supported
            if self.model_code == SkyCooker.MODELS_3:  # RMC-M40S
                _LOGGER.debug(f"🔧 Turning off device to stop cooking...")
                await self.turn_off()
                _LOGGER.info(f"✅ Cooking stopped successfully")
            else:
                _LOGGER.warning(f"⚠️ stop_cooking is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
        except Exception as e:
            _LOGGER.error(f"❌ Error stopping cooking: {e}")
            raise

class SkyCookerError(Exception):
    pass
