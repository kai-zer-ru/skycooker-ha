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

    # Model types - currently only RMC-M40S (RMC-M4xS) is fully supported
    MODEL_TYPE = {
        "RMC-M40S": MODELS_5,  # Primary supported model (changed from MODELS_3 to MODELS_5 based on ha_kettler)
        "RMC-M42S": MODELS_5,  # Also use MODELS_5 for RMC-M42S based on user feedback
        # Other models commented out for now
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

    Status = namedtuple("Status", ["mode","is_on", "error_code", "current_temp", "target_temp", "cook_hours", "cook_minutes", "wait_hours", "wait_minutes", "boil_time"])
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
        # Support for RMC-M4xS variants
        if model.startswith("RMC-M4") and model.endswith("S"):
            return SkyCooker.MODEL_TYPE.get("RMC-M40S", None)
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

    async def test_connection(self):
        """Test basic connection with simple command."""
        _LOGGER.info(f"🧪 Testing basic connection (model code: {self.model_code})")
        try:
            # Try version command first - it's usually the most basic
            r = await self.command(SkyCooker.COMMAND_GET_VERSION)
            if r is not None:
                _LOGGER.info(f"✅ Basic connection test successful")
                return True
            else:
                _LOGGER.warning(f"⚠️ Basic connection test failed - no response")
                return False
        except Exception as e:
            _LOGGER.error(f"❌ Basic connection test failed: {e}")
            return False

    async def turn_on(self):
        _LOGGER.info(f"⚡ Attempting to turn on device (model code: {self.model_code})")
        try:
            # For RMC-M40S, use specific protocol
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                # RMC-M40S might need different command format
                # Try standard command first
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
            # For RMC-M40S, use specific protocol
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                # RMC-M40S might need different command format
                # Try standard command first
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
            # For RMC-M40S, use specific protocol based on ha_kettler
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                # Based on ha_kettler protocol analysis for RMC-M40S
                # Format: mode (1 byte), padding (1 byte), target_temp (1 byte), padding (13 bytes), boil_time (1 byte), padding (2 bytes)
                data = pack("BBB13xBB", int(mode), 0, int(target_temp), int(0x80 + boil_time))
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
            # For RMC-M40S, use specific protocol based on ESPHome-Ready4Sky
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                # Use command 0x06 for RMC-M40S status
                _LOGGER.debug(f"📡 Using command 0x06 for RMC-M40S status")
                r = await self.command(SkyCooker.COMMAND_GET_STATUS)
                
                if r is None or len(r) == 0:
                    _LOGGER.warning(f"⚠️ No response received for status command")
                    return SkyCooker.Status(
                        mode=0,
                        is_on=False,
                        error_code=None,
                        current_temp=0,
                        target_temp=0,
                        cook_hours=0,
                        cook_minutes=0,
                        wait_hours=0,
                        wait_minutes=0,
                        boil_time=0
                    )
                
                # Log the raw response for debugging
                _LOGGER.info(f"📡 Raw status response: {r.hex() if hasattr(r, 'hex') else r}")
                _LOGGER.info(f"📡 Response length: {len(r)} bytes")
                _LOGGER.info(f"📡 Response bytes: {[hex(b) for b in r]}")
                
                return self._parse_rmc_m40s_status(r)
            else:
                _LOGGER.warning(f"⚠️ get_status is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S (MODELS_5) is currently supported")
                return None
            
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
                wait_minutes=0,
                boil_time=0
            )
    
    def _parse_rmc_m40s_status(self, r):
        """Parse RMC-M40S status response based on ESPHome-Ready4Sky protocol."""
        _LOGGER.debug(f"📦 Parsing RMC-M40S status response: {r.hex() if hasattr(r, 'hex') else r}")
        
        try:
            # Log all bytes for detailed analysis
            _LOGGER.info(f"📦 Detailed byte analysis:")
            for i, byte in enumerate(r):
                _LOGGER.info(f"📦   data[{i}]: {byte} (hex: 0x{byte:02x})")
            
            # RMC-M40S status format based on ESPHome-Ready4Sky:
            # data[3] - режим готовки (нужно прибавить 1)
            # data[15] - статус (0x00 = выключено, > 0x01 = включено)
            
            if len(r) < 16:
                _LOGGER.warning(f"⚠️ Status response too short: {len(r)} bytes, expected at least 16")
                return SkyCooker.Status(
                    mode=0,
                    is_on=False,
                    error_code=None,
                    current_temp=0,
                    target_temp=0,
                    cook_hours=0,
                    cook_minutes=0,
                    wait_hours=0,
                    wait_minutes=0,
                    boil_time=0
                )
            
            # Parse mode (data[3] + 1)
            mode = r[3] + 1
            _LOGGER.debug(f"📦 Parsed mode: {mode} ({SkyCooker.MODE_NAMES.get(mode, 'Unknown')})")
            
            # Parse status (data[15])
            status_byte = r[15]
            # According to ESPHome-Ready4Sky: data[15] > 0x01 means device is on
            is_on = status_byte > 0x01
            _LOGGER.debug(f"📦 Parsed status: {status_byte} -> is_on={is_on}")
            
            # Try to extract additional information if available
            current_temp = 0
            target_temp = 0
            cook_hours = 0
            cook_minutes = 0
            wait_hours = 0
            wait_minutes = 0
            boil_time = 0
            
            # If response is longer, try to extract more data
            if len(r) >= 16:
                try:
                    # Try to parse temperature and timing info
                    if len(r) >= 18:
                        current_temp = r[16]
                        target_temp = r[17]
                    if len(r) >= 20:
                        cook_hours = r[18]
                        cook_minutes = r[19]
                    if len(r) >= 22:
                        wait_hours = r[20]
                        wait_minutes = r[21]
                    if len(r) >= 23:
                        boil_time = r[22] & 0x7F  # Extract boil time from byte
                except Exception as e:
                    _LOGGER.debug(f"📦 Could not parse additional status data: {e}")
            
            _LOGGER.debug(f"📦 Parsed RMC-M40S status: mode={mode}, is_on={is_on}, temp={current_temp}/{target_temp}, cook={cook_hours}:{cook_minutes}, wait={wait_hours}:{wait_minutes}, boil_time={boil_time}")
            
            return SkyCooker.Status(
                mode=mode,
                is_on=is_on,
                error_code=None,
                current_temp=current_temp,
                target_temp=target_temp,
                cook_hours=cook_hours,
                cook_minutes=cook_minutes,
                wait_hours=wait_hours,
                wait_minutes=wait_minutes,
                boil_time=boil_time
            )
            
        except Exception as e:
            _LOGGER.error(f"❌ Error parsing RMC-M40S status response: {e}")
            return SkyCooker.Status(
                mode=0,
                is_on=False,
                error_code=None,
                current_temp=0,
                target_temp=0,
                cook_hours=0,
                cook_minutes=0,
                wait_hours=0,
                wait_minutes=0,
                boil_time=0
            )

    async def sync_time(self):
        _LOGGER.info(f"⏰ Synchronizing device time (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                t = time.localtime()
                offset = calendar.timegm(t) - calendar.timegm(time.gmtime(time.mktime(t)))
                now = int(time.time())
                # Corrected format for time sync - use little-endian 32-bit integers
                data = pack("<II", now, offset)
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
            # Corrected format for time response - use unsigned integers
            t, offset = unpack("<II", r)
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

    # Additional methods needed by CookerConnection
    async def get_stats(self):
        """Get device statistics."""
        _LOGGER.info(f"📊 Requesting device stats (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                r = await self.command(SkyCooker.COMMAND_GET_STATS1)
                if r is None:
                    _LOGGER.error(f"❌ Failed to get stats - no response received")
                    return None
                
                # Parse stats data
                try:
                    ontime, energy_wh, heater_on_count, user_on_count = unpack("<IHHH", r[:10])
                    _LOGGER.debug(f"📦 Parsed stats: ontime={ontime}, energy_wh={energy_wh}, heater_on_count={heater_on_count}, user_on_count={user_on_count}")
                    
                    stats = SkyCooker.Stats(
                        ontime=ontime,
                        energy_wh=energy_wh,
                        heater_on_count=heater_on_count,
                        user_on_count=user_on_count
                    )
                except Exception as e:
                    _LOGGER.error(f"❌ Error unpacking stats: {e}")
                    # Fallback to default stats
                    stats = SkyCooker.Stats(
                        ontime=0,
                        energy_wh=0,
                        heater_on_count=0,
                        user_on_count=0
                    )
                
                _LOGGER.info(f"✅ Stats retrieved: ontime={stats.ontime}, energy_wh={stats.energy_wh}, heater_on_count={stats.heater_on_count}, user_on_count={stats.user_on_count}")
                return stats
            else:
                _LOGGER.warning(f"⚠️ get_stats is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
                return None
        except Exception as e:
            _LOGGER.error(f"❌ Failed to get stats: {e}")
            return SkyCooker.Stats(
                ontime=0,
                energy_wh=0,
                heater_on_count=0,
                user_on_count=0
            )

    async def get_light_switch(self, light_type):
        """Get light switch status."""
        _LOGGER.info(f"💡 Requesting light switch status for type {light_type} (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                r = await self.command(SkyCooker.COMMAND_GET_LIGHT_SWITCH, [light_type])
                if r is None:
                    _LOGGER.error(f"❌ Failed to get light switch - no response received")
                    return None
                
                # Parse light switch data
                try:
                    light_switch = r[0]
                    _LOGGER.debug(f"📦 Parsed light switch: {light_switch}")
                except Exception as e:
                    _LOGGER.error(f"❌ Error unpacking light switch: {e}")
                    light_switch = 0
                
                _LOGGER.info(f"✅ Light switch retrieved: {light_switch}")
                return light_switch
            else:
                _LOGGER.warning(f"⚠️ get_light_switch is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
                return None
        except Exception as e:
            _LOGGER.error(f"❌ Failed to get light switch: {e}")
            return None

    async def get_lamp_auto_off_hours(self):
        """Get lamp auto-off hours."""
        _LOGGER.info(f"⏰ Requesting lamp auto-off hours (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
                if r is None:
                    _LOGGER.error(f"❌ Failed to get lamp auto-off hours - no response received")
                    return None
                
                # Parse lamp auto-off hours data
                try:
                    hours, = unpack("<H", r[:2])
                    _LOGGER.debug(f"📦 Parsed lamp auto-off hours: {hours}")
                except Exception as e:
                    _LOGGER.error(f"❌ Error unpacking lamp auto-off hours: {e}")
                    hours = 0
                
                _LOGGER.info(f"✅ Lamp auto-off hours retrieved: {hours}")
                return hours
            else:
                _LOGGER.warning(f"⚠️ get_lamp_auto_off_hours is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
                return None
        except Exception as e:
            _LOGGER.error(f"❌ Failed to get lamp auto-off hours: {e}")
            return None

    async def get_fresh_water(self):
        """Get fresh water information."""
        _LOGGER.info(f"💧 Requesting fresh water information (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                r = await self.command(SkyCooker.COMMAND_GET_FRESH_WATER)
                if r is None:
                    _LOGGER.error(f"❌ Failed to get fresh water - no response received")
                    return None
                
                # Parse fresh water data
                try:
                    is_on, unknown1, water_freshness_hours = unpack("<BBB", r[:3])
                    _LOGGER.debug(f"📦 Parsed fresh water: is_on={is_on}, unknown1={unknown1}, water_freshness_hours={water_freshness_hours}")
                    
                    fresh_water = SkyCooker.FreshWaterInfo(
                        is_on=is_on,
                        unknown1=unknown1,
                        water_freshness_hours=water_freshness_hours
                    )
                except Exception as e:
                    _LOGGER.error(f"❌ Error unpacking fresh water: {e}")
                    # Fallback to default fresh water info
                    fresh_water = SkyCooker.FreshWaterInfo(
                        is_on=False,
                        unknown1=0,
                        water_freshness_hours=0
                    )
                
                _LOGGER.info(f"✅ Fresh water retrieved: is_on={fresh_water.is_on}, water_freshness_hours={fresh_water.water_freshness_hours}")
                return fresh_water
            else:
                _LOGGER.warning(f"⚠️ get_fresh_water is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
                return None
        except Exception as e:
            _LOGGER.error(f"❌ Failed to get fresh water: {e}")
            return SkyCooker.FreshWaterInfo(
                is_on=False,
                unknown1=0,
                water_freshness_hours=0
            )

    async def get_colors(self, light_type):
        """Get colors for light type."""
        _LOGGER.info(f"🌈 Requesting colors for light type {light_type} (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
                r = await self.command(SkyCooker.COMMAND_GET_COLORS, [light_type])
                if r is None:
                    _LOGGER.error(f"❌ Failed to get colors - no response received")
                    return None
                
                # Parse colors data
                try:
                    r_low, g_low, b_low, brightness, r_mid, g_mid, b_mid, temp_low, temp_mid, r_high, g_high, b_high, temp_high = unpack("<BBBBBBBBBBBBB", r[:13])
                    _LOGGER.debug(f"📦 Parsed colors: r_low={r_low}, g_low={g_low}, b_low={b_low}, brightness={brightness}, r_mid={r_mid}, g_mid={g_mid}, b_mid={b_mid}, temp_low={temp_low}, temp_mid={temp_mid}, r_high={r_high}, g_high={g_high}, b_high={b_high}, temp_high={temp_high}")
                    
                    # Create a simple colors object
                    colors = type('Colors', (), {
                        'r_low': r_low, 'g_low': g_low, 'b_low': b_low,
                        'brightness': brightness,
                        'r_mid': r_mid, 'g_mid': g_mid, 'b_mid': b_mid,
                        'temp_low': temp_low, 'temp_mid': temp_mid,
                        'r_high': r_high, 'g_high': g_high, 'b_high': b_high,
                        'temp_high': temp_high
                    })()
                except Exception as e:
                    _LOGGER.error(f"❌ Error unpacking colors: {e}")
                    # Fallback to default colors
                    colors = type('Colors', (), {
                        'r_low': 0, 'g_low': 0, 'b_low': 0,
                        'brightness': 0,
                        'r_mid': 0, 'g_mid': 0, 'b_mid': 0,
                        'temp_low': 0, 'temp_mid': 0,
                        'r_high': 0, 'g_high': 0, 'b_high': 0,
                        'temp_high': 0
                    })()
                
                _LOGGER.info(f"✅ Colors retrieved for light type {light_type}")
                return colors
            else:
                _LOGGER.warning(f"⚠️ get_colors is not supported by this model (code: {self.model_code})")
                _LOGGER.warning(f"⚠️ Only RMC-M40S is currently supported")
                return None
        except Exception as e:
            _LOGGER.error(f"❌ Failed to get colors: {e}")
            return None


    async def get_wait_hours(self):
        if self.model_code in [SkyCooker.MODELS_5]: # RMC-M40S
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get wait hours - no response received")
                return None
            # Corrected format for auto-off hours response
            hours, = unpack("<H", r[:2])
            _LOGGER.info(f"Wait hours={hours}")
            return hours
        else:
            _LOGGER.debug(f"get_wait_hours is not supported by this model")

    async def get_wait_minutes(self):
        if self.model_code in [SkyCooker.MODELS_5]: # RMC-M40S
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get wait minutes - no response received")
                return None
            # Corrected format for auto-off minutes response
            minutes, = unpack("<H", r[:2])
            _LOGGER.info(f"Wait minutes={minutes}")
            return minutes
        else:
            _LOGGER.debug(f"get_wait_minutes is not supported by this model")

    async def get_cook_hours(self):
        if self.model_code in [SkyCooker.MODELS_5]: # RMC-M40S
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get cook hours - no response received")
                return None
            # Corrected format for cook hours response
            hours, = unpack("<H", r[:2])
            _LOGGER.info(f"Cook hours={hours}")
            return hours
        else:
            _LOGGER.debug(f"get_cook_hours is not supported by this model")

    async def get_cook_minutes(self):
        if self.model_code in [SkyCooker.MODELS_5]: # RMC-M40S
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get cook minutes - no response received")
                return None
            # Corrected format for cook minutes response
            minutes, = unpack("<H", r[:2])
            _LOGGER.info(f"Cook minutes={minutes}")
            return minutes
        else:
            _LOGGER.debug(f"get_cook_minutes is not supported by this model")

    async def get_current_program(self):
        if self.model_code in [SkyCooker.MODELS_5]: # RMC-M40S
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            if r is None:
                _LOGGER.error(f"❌ Failed to get current program - no response received")
                return None
            # Corrected format for current program response
            program, = unpack("<H", r[:2])
            _LOGGER.info(f"Current program={program}")
            return program
        else:
            _LOGGER.debug(f"get_current_program is not supported by this model")

    async def set_target_program(self, program):
        """Set the target program for multicooker."""
        _LOGGER.info(f"🎯 Setting target program: {program} (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
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
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
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
        if self.model_code in [SkyCooker.MODELS_5]:
            # This would need specific command implementation based on protocol
            _LOGGER.info(f"set_cook_hours: {hours} hours")
            # TODO: Implement actual command
        else:
            _LOGGER.debug(f"set_cook_hours is not supported by this model")

    async def set_cook_minutes(self, minutes):
        """Set the cook minutes for multicooker."""
        if self.model_code in [SkyCooker.MODELS_5]:
            # This would need specific command implementation based on protocol
            _LOGGER.info(f"set_cook_minutes: {minutes} minutes")
            # TODO: Implement actual command
        else:
            _LOGGER.debug(f"set_cook_minutes is not supported by this model")

    async def start_cooking(self):
        """Start cooking with current settings."""
        _LOGGER.info(f"🔥 Starting cooking (model code: {self.model_code})")
        try:
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
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
            # Currently only RMC-M40S (MODELS_5) is supported
            if self.model_code == SkyCooker.MODELS_5:  # RMC-M40S
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
