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

    MODEL_TYPE = { # Source: https://github.com/KomX/ESPHome-Ready4Sky/blob/main/components/skycooker/__init__.py
        "RMC-M40S": MODELS_3,
        "RMC-M42S": MODELS_3,
        "RMC-M92S": MODELS_6, "RMC-M92S-A": MODELS_6, "RMC-M92S-C": MODELS_6, "RMC-M92S-E": MODELS_6,
        "RMC-M222S": MODELS_7, "RMC-M222S-A": MODELS_7,
        "RMC-M223S": MODELS_7,"RMC-M223S-E": MODELS_7,
        "RMC-M224S": MODELS_7,"RFS-KMC001": MODELS_7,
        "RMC-M225S": MODELS_7,"RMC-M225S-E": MODELS_7,
        "RMC-M226S": MODELS_7,"RMC-M226S-E": MODELS_7,"JK-MC501": MODELS_7,"NK-MC10": MODELS_7,
        "RMC-M227S": MODELS_7,
        "RMC-M800S": MODELS_0,
        "RMC-M903S": MODELS_5, "RFS-KMC005": MODELS_5,
        "RMC-961S": MODELS_4,
        "RMC-CBD100S": MODELS_1,
        "RMC-CBF390S": MODELS_2,
    }

    MODE_BOIL = 0x00
    MODE_HEAT = 0x01
    MODE_BOIL_HEAT = 0x02
    MODE_LAMP = 0x03
    MODE_GAME = 0x04
    MODE_NAMES = {
        MODE_BOIL: "Boil",
        MODE_HEAT: "Heat",
        MODE_BOIL_HEAT: "Boil+Heat",
        MODE_LAMP: "Lamp",
        MODE_GAME: "Light"
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

    Status = namedtuple("Status", ["mode","is_on", "error_code"])
    Stats = namedtuple("Stats", ["ontime", "energy_wh", "heater_on_count", "user_on_count"])
    FreshWaterInfo = namedtuple("FreshWaterInfo", ["is_on", "unknown1", "water_freshness_hours"])


    def __init__(self, model):
        _LOGGER.info(f"Cooker model: {model}")
        self.model = model
        self.model_code = self.get_model_code(model)
        if not self.model_code:
            raise SkyCookerError("Unknown Cooker model")

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
        r = await self.command(SkyCooker.COMMAND_AUTH, key)
        ok = r[0] != 0
        _LOGGER.warning(f"Auth: ok={ok}")
        return ok

    async def get_version(self):
        r = await self.command(SkyCooker.COMMAND_GET_VERSION)
        major, minor = unpack("BB", r)
        ver = f"{major}.{minor}"
        _LOGGER.warning(f"Version: {ver}")
        return (major, minor)

    async def turn_on(self):
        if self.model_code in [SkyCooker.MODELS_3, SkyCooker.MODELS_4]: # All except RK-M171S, RK-M172S, RK-M173S
            r = await self.command(SkyCooker.COMMAND_TURN_ON)
            if r[0] != 1: raise SkyCookerError("can't turn on")
            _LOGGER.warning(f"Turned on")
        else:
            _LOGGER.warning(f"turn_on is not supported by this model")

    async def turn_off(self):
        if self.model_code in [SkyCooker.MODELS_1, SkyCooker.MODELS_2, SkyCooker.MODELS_3, SkyCooker.MODELS_4]: # All known models
            r = await self.command(SkyCooker.COMMAND_TURN_OFF)
            if r[0] != 1: raise SkyCookerError("can't turn off")
            _LOGGER.warning(f"Turned off")
        else:
            _LOGGER.warning(f"turn_off is not supported by this model")

    async def set_main_mode(self, mode, target_temp = 0, boil_time = 0):
        if self.model_code in [SkyCooker.MODELS_1, SkyCooker.MODELS_2]: # RK-M170S, RK-M171S and RK-M173S but not sure about RK-M170S and RK-M173S
            if mode == SkyCooker.MODE_BOIL_HEAT:
                mode = SkyCooker.MODE_BOIL # MODE_BOIL_HEAT not supported
            elif mode == SkyCooker.MODE_BOIL:
                target_temp = 0
        if self.model_code in [SkyCooker.MODELS_1]: # RK-M170S (?)
            if target_temp == 0:
                pass
            elif target_temp < 50:
                target_temp = 1
            elif target_temp < 65:
                target_temp = 2
            elif target_temp < 80:
                target_temp = 3
            elif target_temp < 90:
                target_temp = 4
            else:
                target_temp = 5
        if self.model_code in [SkyCooker.MODELS_1]: # RK-M170S and
            data = pack("BBxx", int(mode), int(target_temp))
        if self.model_code in [SkyCooker.MODELS_2]: # RK-M171S, RK-M173S and RK-G200
            data = pack("BxBx", int(mode), int(target_temp))
        elif self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S
            data = pack("BxBxxxxxxxxxxBxx", int(mode), int(target_temp), int(0x80 + boil_time))
        else:
            _LOGGER.warning(f"set_main_mode is not supported by this model")
            return
        r = await self.command(SkyCooker.COMMAND_SET_MAIN_MODE, data)
        if r[0] != 1: raise SkyCookerError("can't set mode")
        _LOGGER.warning(f"Mode set: mode={mode} ({SkyCooker.MODE_NAMES[mode]}), target_temp={target_temp}, boil_time={boil_time}")

    async def get_status(self):
        r = await self.command(SkyCooker.COMMAND_GET_STATUS)
        # if self.model_code in [MODELS_1] # ???
        if self.model_code in [SkyCooker.MODELS_3]: # RK-M173S (?), RK-G200
            mode, is_on = unpack("<BxBxxxxx?xBxxxxx", r)
            status = SkyCooker.Status(mode=mode,
                                      is_on=is_on,
                                      error_code=None)
        # elif self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S
        #     # New models
        #     status = SkyCooker.Status(*unpack("<BxBx?BB??BxxxBxx", r))
        #     status = status._replace(
        #         error_code=None if status.error_code == 0 else status.error_code
        #     )
        else:
            _LOGGER.warning(f"get_status is not supported by this model")
            return
        # if self.model_code in [SkyCooker.MODELS_2, SkyCooker.MODELS_3]: # RK-M173S (?), RK-G200
        #     if status.mode == SkyCooker.MODE_BOIL and status.target_temp > 0:
        #         status = status._replace(
        #             mode=SkyCooker.MODE_BOIL_HEAT
        #         )
        # if self.model_code in [SkyCooker.MODELS_1]: # RK-M170S (?)
        #     status = status._replace(
        #         target_temp=target_temp
        #     )
        _LOGGER.warning(f"Status: mode={status.mode} ({SkyCooker.MODE_NAMES[status.mode]}), is_on={status.is_on}")
        return status

    async def sync_time(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S
            t = time.localtime()
            offset = calendar.timegm(t) - calendar.timegm(time.gmtime(time.mktime(t)))
            now = int(time.time())
            data = pack("<ii", now, offset)
            r = await self.command(SkyCooker.COMMAND_SYNC_TIME, data)
            if r[0] != 0: raise SkyCookerError("can't sync time")
            _LOGGER.warning(f"Writed time={now} ({datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
        else:
            _LOGGER.warning(f"sync_time is not supported by this model")

    async def get_time(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_TIME)
            t, offset = unpack("<ii", r)
            _LOGGER.warning(f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
            return t, offset
        else:
            _LOGGER.warning(f"get_time is not supported by this model")

    async def commit(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_COMMIT_SETTINGS)
            if r[0] != 1: raise SkyCookerError("can't commit settings")
            _LOGGER.warning(f"Settings commited")
        else:
            _LOGGER.warning(f"commit is not supported by this model")


    async def get_wait_hours(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            hours, = unpack("<H", r)
            _LOGGER.warning(f"Wait hours={hours}")
            return hours
        else:
            _LOGGER.debug(f"get_wait_hours is not supported by this model")

    async def get_wait_minutes(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            minutes, = unpack("<H", r)
            _LOGGER.warning(f"Wait minutes={minutes}")
            return minutes
        else:
            _LOGGER.debug(f"get_wait_minutes is not supported by this model")

    async def get_cook_hours(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            hours, = unpack("<H", r)
            _LOGGER.warning(f"Cook hours={hours}")
            return hours
        else:
            _LOGGER.debug(f"get_cook_hours is not supported by this model")

    async def get_cook_minutes(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            minutes, = unpack("<H", r)
            _LOGGER.warning(f"Cook minutes={minutes}")
            return minutes
        else:
            _LOGGER.debug(f"get_cook_minutes is not supported by this model")

    async def get_current_program(self):
        if self.model_code in [SkyCooker.MODELS_3]: # RK-G2xxS, RK-M13xS, RK-M21xS, RK-M223S but not sure
            r = await self.command(SkyCooker.COMMAND_GET_AUTO_OFF_HOURS)
            program, = unpack("<H", r)
            _LOGGER.warning(f"Current program={program}")
            return program
        else:
            _LOGGER.debug(f"get_current_program is not supported by this model")

class SkyCookerError(Exception):
    pass
