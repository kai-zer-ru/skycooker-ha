"""Constants for SkyCoocker component."""

DOMAIN = "skycooker"
FRIENDLY_NAME = "SkyCoocker"
MANUFACTORER = "Redmond"

# Supported models
SUPPORTED_MODELS = {
    "RMC-M40S": {
        "name": "Redmond RMC-M40S",
        "supported": True,
        "uuid_service": "6e400001-b5a3-f393-e0a9-e50e24dcca9e",
        "uuid_tx": "6e400002-b5a3-f393-e0a9-e50e24dcca9e",
        "uuid_rx": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
        "commands": {
            "AUTH": 0xFF,
            "SET_MODE": 0x09,
            "GET_STATUS": 0x06,
            "START": 0x03,
            "STOP": 0x04
        },
        "modes": {
            0: "Мультиповар",
            1: "Молочная каша",
            2: "Тушение",
            3: "Жарка",
            4: "Суп",
            5: "Пар",
            6: "Паста",
            7: "Томление",
            8: "Варка",
            9: "Выпечка",
            10: "Рис/крупы",
            11: "Плов",
            12: "Йогурт",
            13: "Пицца",
            14: "Хлеб",
            16: "Ожидание",
            17: "Вакуум"
        },
        "status_codes": {
            0x00: "Выключена",
            0x01: "Ожидание",
            0x02: "Отложенный запуск",
            0x03: "Разогрев",
            0x05: "Готовка",
            0x06: "Автоподогрев",
            0x0A: "Полностью выключена"
        }
    }
    # Other models can be added here when supported
    # "RMC-M45S": {
    #     "name": "Redmond RMC-M45S",
    #     "supported": False,
    #     "uuid_service": "...",
    #     "uuid_tx": "...",
    #     "uuid_rx": "...",
    #     "commands": {
    #         "AUTH": 0xFF,
    #         "SET_MODE": 0x09,
    #         "GET_STATUS": 0x06,
    #         "START": 0x03,
    #         "STOP": 0x04
    #     },
    #     "modes": {
    #         0: "Мультиповар",
    #         ...
    #     },
    #     "status_codes": {
    #         0x00: "Выключена",
    #         ...
    #     }
    # }
}

# Commands (backward compatibility - will be deprecated)
COMMAND_AUTH = 0xFF
COMMAND_SET_MODE = 0x09
COMMAND_GET_STATUS = 0x06
COMMAND_START = 0x03
COMMAND_STOP = 0x04

# Status codes (backward compatibility - will be deprecated)
STATUS_OFF = 0x00
STATUS_WAIT = 0x01
STATUS_DELAYED_LAUNCH = 0x02
STATUS_WARMING = 0x03
STATUS_COOKING = 0x05
STATUS_AUTO_WARM = 0x06
STATUS_FULL_OFF = 0x0A

STATUS_CODES = {
    STATUS_OFF: "Выключена",
    STATUS_WAIT: "Ожидание",
    STATUS_DELAYED_LAUNCH: "Отложенный запуск",
    STATUS_WARMING: "Разогрев",
    STATUS_COOKING: "Готовка",
    STATUS_AUTO_WARM: "Автоподогрев",
    STATUS_FULL_OFF: "Полностью выключена"
}

# Cooking modes (backward compatibility - will be deprecated)
MODES = {
    0: "Мультиповар",
    1: "Молочная каша",
    2: "Тушение",
    3: "Жарка",
    4: "Суп",
    5: "Пар",
    6: "Паста",
    7: "Томление",
    8: "Варка",
    9: "Выпечка",
    10: "Рис/крупы",
    11: "Плов",
    12: "Йогурт",
    13: "Пицца",
    14: "Хлеб",
    16: "Ожидание",
    17: "Вакуум"
}

# Config flow constants
CONF_PERSISTENT_CONNECTION = "persistent_connection"
CONF_MODEL = "model"

# Default values
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_PERSISTENT_CONNECTION = True

# Data keys
DATA_CONNECTION = "connection"
DATA_CANCEL = "cancel"
DATA_WORKING = "working"
DATA_DEVICE_INFO = "device_info"

# Dispatcher
DISPATCHER_UPDATE = "update"

# BLE settings
BLE_RECV_TIMEOUT = 1.5
MAX_TRIES = 3  # Like in working version
TRIES_INTERVAL = 0.5