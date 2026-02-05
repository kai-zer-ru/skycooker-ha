# Константы для интеграции SkyCooker
from collections import namedtuple

DOMAIN = "skycooker"

LANGS = ["ru", "en"]

# Константы для потока настройки
CONF_PERSISTENT_CONNECTION = "persistent_connection"
CONF_MODEL = "model"
CONF_FAVORITE_PROGRAMS = "favorite_programs"

# Значения по умолчанию
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PERSISTENT_CONNECTION = True
MAX_FAVORITE_PROGRAMS = 5

# Дружественные имена
FRIENDLY_NAME = "SkyCooker"
SKYCOOKER_NAME = "SkyCooker"
MANUFACTURER = "Redmond"

# Типы кнопок
BUTTON_TYPE_START = "start"
BUTTON_TYPE_STOP = "stop"
BUTTON_TYPE_START_DELAYED = "start_delayed"

# Типы селектов
SELECT_TYPE_PROGRAM = "program"
SELECT_TYPE_SUBPROGRAM = "subprogram"
SELECT_TYPE_TEMPERATURE = "temperature"
SELECT_TYPE_COOKING_TIME_HOURS = "cooking_time_hours"
SELECT_TYPE_COOKING_TIME_MINUTES = "cooking_time_minutes"
SELECT_TYPE_DELAYED_START_HOURS = "delayed_start_hours"
SELECT_TYPE_DELAYED_START_MINUTES = "delayed_start_minutes"
SELECT_TYPE_FAVORITES = "favorites"

# Типы сенсоров
SENSOR_TYPE_STATUS = "status"
SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_REMAINING_TIME = "remaining_time"
SENSOR_TYPE_COOKING_TIME = "cooking_time"
SENSOR_TYPE_AUTO_WARM_TIME = "auto_warm_time"
SENSOR_TYPE_SUCCESS_RATE = "success_rate"
SENSOR_TYPE_DELAYED_LAUNCH_TIME = "delayed_launch_time"
SENSOR_TYPE_CURRENT_PROGRAM = "current_program"
SENSOR_TYPE_SUBPROGRAM = "subprogram"

# Типы переключателей
SWITCH_TYPE_AUTO_WARM = "auto_warm"

# Настройки BLE
UUID_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UUID_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
BLE_RECV_TIMEOUT = 1.5
MAX_TRIES = 3
TRIES_INTERVAL = 0.5
STATS_INTERVAL = 15
TARGET_TTL = 30

# Ключи данных
DATA_CONNECTION = "connection"
DATA_CANCEL = "cancel"
DATA_WORKING = "working"
DATA_DEVICE_INFO = "device_info"

# Диспетчер
DISPATCHER_UPDATE = "update"

# Команды
COMMAND_GET_VERSION = 0x01
COMMAND_TURN_ON = 0x03
COMMAND_TURN_OFF = 0x04
COMMAND_SET_MAIN_MODE = 0x05
COMMAND_GET_STATUS = 0x06
COMMAND_SELECT_PROGRAM = 0x09
COMMAND_SYNC_TIME = 0x6E
COMMAND_GET_TIME = 0x6F
COMMAND_AUTH = 0xFF

# Битовые флаги для настроек программ (uint8_t)
# Битовые флаги для настроек программ
BIT_FLAG_SUBMODE_ENABLE = 0x80        # B[7] - включение подрежима
BIT_FLAG_AUTOPOWER_ENABLE = 0x40      # B[6] - включение автопита
BIT_FLAG_EXPANSION_MODES_ENABLE = 0x20 # B[5] - включение расширенных программ
BIT_FLAG_TWO_BOWL_ENABLE = 0x10       # B[4] - включение двух чаш
BIT_FLAG_PRESET_TEMP_ENABLE = 0x08    # B[3] - включение предварительной температуры
BIT_FLAG_MASTERCHEF_LIGHT_ENABLE = 0x04 # B[2] - включение подсветки MasterChef
BIT_FLAG_DELAY_START_ENABLE = 0x02    # B[1] - включение отложенного старта
BIT_FLAG_POSTHEAT_ENABLE = 0x01       # B[0] - включение подогрева


######## Константы моделей мультиварок ########

MODEL_0 = 0
MODEL_1 = 1
MODEL_2 = 2
MODEL_3 = 3
MODEL_4 = 4
MODEL_5 = 5
MODEL_6 = 6
MODEL_7 = 7

MODELS = {
    "RMC-M40S": MODEL_3,
    "RMC-M42S": MODEL_3,
    "RMC-M92S": MODEL_6,
    "RMC-M92S-A": MODEL_6,
    "RMC-M92S-C": MODEL_6,
    "RMC-M92S-E": MODEL_6,
    "RMC-M222S": MODEL_7,
    "RMC-M222S-A": MODEL_7,
    "RMC-M223S": MODEL_7,
    "RMC-M223S-E": MODEL_7,
    "RMC-M224S": MODEL_7,
    "RFS-KMC001": MODEL_7,
    "RMC-M225S": MODEL_7,
    "RMC-M225S-E": MODEL_7,
    "RMC-M226S": MODEL_7,
    "RMC-M226S-E": MODEL_7,
    "JK-MC501": MODEL_7,
    "NK-MC10": MODEL_7,
    "RMC-M227S": MODEL_7,
    "RFS-KMC004": MODEL_7,
    "RMC-M800S": MODEL_0,
    "RMC-M903S": MODEL_5,
    "RFS-KMC005": MODEL_5,
    "RMC-961S": MODEL_4,
    "RMC-CBD100S": MODEL_1,
    "RMC-CBF390S": MODEL_2,
}

# Список поддерживаемых моделей
SUPPORTED_MODELS = {
    "RMC-M40S": {"supported": True, "type": MODEL_3},
    "RMC-M42S": {"supported": True, "type": MODEL_3},
    "RMC-M92S": {"supported": False, "type": MODEL_6},
    "RMC-M92S-A": {"supported": False, "type": MODEL_6},
    "RMC-M92S-C": {"supported": False, "type": MODEL_6},
    "RMC-M92S-E": {"supported": False, "type": MODEL_6},
    "RMC-M222S": {"supported": False, "type": MODEL_7},
    "RMC-M222S-A": {"supported": False, "type": MODEL_7},
    "RMC-M223S": {"supported": False, "type": MODEL_7},
    "RMC-M223S-E": {"supported": False, "type": MODEL_7},
    "RMC-M224S": {"supported": False, "type": MODEL_7},
    "RFS-KMC001": {"supported": False, "type": MODEL_7},
    "RMC-M225S": {"supported": False, "type": MODEL_7},
    "RMC-M225S-E": {"supported": False, "type": MODEL_7},
    "RMC-M226S": {"supported": False, "type": MODEL_7},
    "RMC-M226S-E": {"supported": False, "type": MODEL_7},
    "JK-MC501": {"supported": False, "type": MODEL_7},
    "NK-MC10": {"supported": False, "type": MODEL_7},
    "RMC-M227S": {"supported": False, "type": MODEL_7},
    "RFS-KMC004": {"supported": False, "type": MODEL_7},
    "RMC-M800S": {"supported": False, "type": MODEL_0},
    "RMC-M903S": {"supported": False, "type": MODEL_5},
    "RFS-KMC005": {"supported": False, "type": MODEL_5},
    "RMC-961S": {"supported": False, "type": MODEL_4},
    "RMC-CBD100S": {"supported": False, "type": MODEL_1},
    "RMC-CBF390S": {"supported": False, "type": MODEL_2},
}


######## Константы продуктов ########

# Константы для названий продуктов
PRODUCT_NO_CHOICE = "no_choice"
PRODUCT_VEGETABLES = "vegetables"
PRODUCT_FISH = "fish"
PRODUCT_MEAT = "meat"
PRODUCT_BIRD = "bird"
PRODUCT_DESSERTS = "desserts"


# Данные продуктов для каждой модели
PRODUCT_DATA = {
    MODEL_0: [
        [4, 18, 12, 15, 0], [5, 40, 35, 60, 0], [11, 30, 25, 40, 0]
    ],
    MODEL_1: [
        [2, 60, 50, 40, 30], [4, 35, 30, 25, 20], [5, 40, 30, 20, 18], [6, 50, 40, 20, 18],
        [8, 18, 15, 12, 16], [18, 18, 16, 15, 13]
    ],
    MODEL_2: [
        [2, 60, 50, 40, 30], [4, 35, 30, 25, 20], [5, 40, 30, 20, 18], [6, 50, 40, 20, 18],
        [8, 18, 15, 12, 16], [18, 18, 16, 15, 13]
    ],
}

# Product names for each model
PRODUCT_NAMES = {
    MODEL_0: [
        [
            PRODUCT_NO_CHOICE, PRODUCT_VEGETABLES, PRODUCT_FISH, PRODUCT_MEAT, PRODUCT_BIRD
        ],
        [
            PRODUCT_NO_CHOICE, PRODUCT_VEGETABLES, PRODUCT_FISH, PRODUCT_MEAT, PRODUCT_BIRD
        ],
    ],
    MODEL_1: [
        [
            PRODUCT_NO_CHOICE, PRODUCT_VEGETABLES, PRODUCT_FISH, PRODUCT_MEAT, PRODUCT_BIRD, PRODUCT_DESSERTS
        ],
        [
            PRODUCT_NO_CHOICE, PRODUCT_VEGETABLES, PRODUCT_FISH, PRODUCT_MEAT, PRODUCT_BIRD, PRODUCT_DESSERTS
        ],
    ],
    MODEL_2: [
        [
            PRODUCT_NO_CHOICE, PRODUCT_VEGETABLES, PRODUCT_FISH, PRODUCT_MEAT, PRODUCT_BIRD, PRODUCT_DESSERTS
        ],
        [
            PRODUCT_NO_CHOICE, PRODUCT_VEGETABLES, PRODUCT_FISH, PRODUCT_MEAT, PRODUCT_BIRD, PRODUCT_DESSERTS
        ],
    ],
}



######## Константы программ ########



# Данные режимов для каждой модели
PROGRAM_DATA = {
    0: [
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 100, "hours": 0, "minutes": 35, "byte_flag": 7},
        {"temperature": 97, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 110, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 180, "hours": 0, "minutes": 15, "byte_flag": 133},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 135},
        {"temperature": 100, "hours": 0, "minutes": 8, "byte_flag": 5},
        {"temperature": 95, "hours": 0, "minutes": 35, "byte_flag": 7},
        {"temperature": 99, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 40, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 145, "hours": 0, "minutes": 45, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 135},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 7}
    ],
    1: [
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 135},
        {"temperature": 100, "hours": 1, "minutes": 30, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 35, "byte_flag": 135},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 135},
        {"temperature": 100, "hours": 0, "minutes": 50, "byte_flag": 135},
        {"temperature": 97, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 170, "hours": 0, "minutes": 18, "byte_flag": 133},
        {"temperature": 145, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 150, "hours": 0, "minutes": 30, "byte_flag": 7},
        {"temperature": 110, "hours": 0, "minutes": 35, "byte_flag": 7},
        {"temperature": 38, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 150, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 8, "byte_flag": 4},
        {"temperature": 98, "hours": 0, "minutes": 15, "byte_flag": 7},
        {"temperature": 40, "hours": 0, "minutes": 10, "byte_flag": 7},
        {"temperature": 63, "hours": 2, "minutes": 30, "byte_flag": 6},
        {"temperature": 160, "hours": 0, "minutes": 18, "byte_flag": 132},
        {"temperature": 98, "hours": 0, "minutes": 20, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 20, "byte_flag": 64}
    ],
    2: [
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 100, "hours": 3, "minutes": 0, "byte_flag": 135},
        {"temperature": 170, "hours": 0, "minutes": 18, "byte_flag": 133},
        {"temperature": 100, "hours": 0, "minutes": 8, "byte_flag": 4},
        {"temperature": 145, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 135},
        {"temperature": 38, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 40, "hours": 0, "minutes": 10, "byte_flag": 7},
        {"temperature": 110, "hours": 0, "minutes": 35, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 135},
        {"temperature": 140, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 98, "hours": 0, "minutes": 20, "byte_flag": 7},
        {"temperature": 150, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 20, "byte_flag": 135},
        {"temperature": 100, "hours": 0, "minutes": 15, "byte_flag": 7},
        {"temperature": 98, "hours": 0, "minutes": 30, "byte_flag": 7},
        {"temperature": 97, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 4},
        {"temperature": 160, "hours": 0, "minutes": 16, "byte_flag": 132},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 135},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 64},
        {"temperature": 70, "hours": 0, "minutes": 0, "byte_flag": 64}
    ],
    3: [
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 101, "hours": 0, "minutes": 30, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 165, "hours": 0, "minutes": 18, "byte_flag": 5},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 35, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 8, "byte_flag": 4},
        {"temperature": 98, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 7},
        {"temperature": 140, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 25, "byte_flag": 7},
        {"temperature": 110, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 40, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 145, "hours": 0, "minutes": 20, "byte_flag": 7},
        {"temperature": 140, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 0, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 62, "hours": 2, "minutes": 30, "byte_flag": 6}
    ],
    4: [
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 100, "hours": 0, "minutes": 10, "byte_flag": 7},
        {"temperature": 150, "hours": 0, "minutes": 15, "byte_flag": 5},
        {"temperature": 100, "hours": 0, "minutes": 25, "byte_flag": 7},
        {"temperature": 140, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 110, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 7},
        {"temperature": 38, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 64}
    ],
    5: [
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 97, "hours": 0, "minutes": 10, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 170, "hours": 0, "minutes": 15, "byte_flag": 5},
        {"temperature": 99, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 20, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 8, "byte_flag": 4},
        {"temperature": 97, "hours": 5, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 7},
        {"temperature": 145, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 35, "byte_flag": 7},
        {"temperature": 110, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 38, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 150, "hours": 0, "minutes": 25, "byte_flag": 7},
        {"temperature": 150, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 98, "hours": 0, "minutes": 20, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 20, "byte_flag": 64}
    ],
    6: [
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 97, "hours": 0, "minutes": 10, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 170, "hours": 0, "minutes": 15, "byte_flag": 5},
        {"temperature": 99, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 20, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 8, "byte_flag": 4},
        {"temperature": 97, "hours": 5, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 40, "byte_flag": 7},
        {"temperature": 145, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 35, "byte_flag": 7},
        {"temperature": 110, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 38, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 150, "hours": 0, "minutes": 25, "byte_flag": 7},
        {"temperature": 150, "hours": 3, "minutes": 0, "byte_flag": 7},
        {"temperature": 98, "hours": 0, "minutes": 20, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 64},
        {"temperature": 100, "hours": 70, "minutes": 30, "byte_flag": 64}
    ],
    7: [
        {"temperature": 100, "hours": 0, "minutes": 0, "byte_flag": 0},
        {"temperature": 150, "hours": 0, "minutes": 15, "byte_flag": 5},
        {"temperature": 100, "hours": 0, "minutes": 25, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 15},
        {"temperature": 110, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 25, "byte_flag": 7},
        {"temperature": 140, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 1, "minutes": 0, "byte_flag": 7},
        {"temperature": 100, "hours": 0, "minutes": 30, "byte_flag": 7},
        {"temperature": 40, "hours": 8, "minutes": 0, "byte_flag": 6},
        {"temperature": 100, "hours": 0, "minutes": 20, "byte_flag": 64},
        {"temperature": 70, "hours": 0, "minutes": 30, "byte_flag": 64}
    ]
}

# Константы для названий режимов

PROGRAM_MULTI_CHEF = 'multi_chef'
PROGRAM_RICE_CEREALS = 'rice_cereals'
PROGRAM_LANGUOR = 'languor'
PROGRAM_PILAF = 'pilaf'
PROGRAM_FRYING = 'frying'
PROGRAM_STEWING = 'stewing'
PROGRAM_PASTA = 'pasta'
PROGRAM_MILK_PORRIDGE = 'milk_porridge'
PROGRAM_SOUP = 'soup'
PROGRAM_YOGURT = 'yogurt'
PROGRAM_BAKING = 'baking'
PROGRAM_STEAM = 'steam'
PROGRAM_COOKING_LEGUMES = 'cooking_legumes'
PROGRAM_WILDFOWL = 'wildfowl'
PROGRAM_PIZZA = 'pizza'
PROGRAM_BREAD = 'bread'
PROGRAM_BABY_FOOD = 'baby_food'
PROGRAM_SOUS_VIDE = 'sous_vide'
PROGRAM_DEEP_FRYING = 'deep_frying'
PROGRAM_DESSERTS = 'desserts'
PROGRAM_EXPRESS = 'express'
PROGRAM_GALANTINE = 'galantine'
PROGRAM_YOGURT_DOUGH = 'yogurt_dough'
PROGRAM_CHEESECAKE = 'cheesecake'
PROGRAM_SOUS = 'sous'

PROGRAM_STANDBY = 'standby'
PROGRAM_WARMING_UP = 'warming_up'
PROGRAM_WARMING = 'warming'
PROGRAM_COOKING = 'cooking'
PROGRAM_NONE = 'none'

# Названия режимов для каждой модели
PROGRAM_NAMES = {
    0: [
        PROGRAM_STANDBY,
        PROGRAM_MULTI_CHEF, PROGRAM_RICE_CEREALS, PROGRAM_LANGUOR, PROGRAM_PILAF,
        PROGRAM_FRYING, PROGRAM_STEWING, PROGRAM_PASTA, PROGRAM_MILK_PORRIDGE,
        PROGRAM_SOUP, PROGRAM_YOGURT, PROGRAM_BAKING, PROGRAM_STEAM,
        PROGRAM_COOKING_LEGUMES
    ],
    1: [
        PROGRAM_STANDBY,
        PROGRAM_MULTI_CHEF, PROGRAM_RICE_CEREALS, PROGRAM_SOUP, PROGRAM_WILDFOWL,
        PROGRAM_STEAM, PROGRAM_COOKING, PROGRAM_STEWING, PROGRAM_LANGUOR,
        PROGRAM_FRYING, PROGRAM_BAKING, PROGRAM_PIZZA, PROGRAM_PILAF,
        PROGRAM_YOGURT, PROGRAM_BREAD, PROGRAM_PASTA, PROGRAM_MILK_PORRIDGE,
        PROGRAM_BABY_FOOD, PROGRAM_SOUS_VIDE, PROGRAM_DEEP_FRYING, PROGRAM_DESSERTS,
        PROGRAM_EXPRESS
    ],
    2: [
        PROGRAM_STANDBY,
        PROGRAM_GALANTINE, PROGRAM_FRYING, PROGRAM_PASTA, PROGRAM_BAKING,
        PROGRAM_STEWING, PROGRAM_YOGURT_DOUGH, PROGRAM_MULTI_CHEF, PROGRAM_BABY_FOOD,
        PROGRAM_PILAF, PROGRAM_SOUP, PROGRAM_CHEESECAKE, PROGRAM_MILK_PORRIDGE,
        PROGRAM_BREAD, PROGRAM_STEAM, PROGRAM_RICE_CEREALS, PROGRAM_DESSERTS,
        PROGRAM_LANGUOR, PROGRAM_SOUS, PROGRAM_DEEP_FRYING, PROGRAM_COOKING,
        PROGRAM_EXPRESS, PROGRAM_WARMING_UP
    ],
    3: [
        PROGRAM_MULTI_CHEF, PROGRAM_MILK_PORRIDGE, PROGRAM_STEWING, PROGRAM_FRYING,
        PROGRAM_SOUP, PROGRAM_STEAM, PROGRAM_PASTA, PROGRAM_LANGUOR,
        PROGRAM_COOKING, PROGRAM_BAKING, PROGRAM_RICE_CEREALS, PROGRAM_PILAF,
        PROGRAM_YOGURT, PROGRAM_PIZZA, PROGRAM_BREAD, PROGRAM_NONE, PROGRAM_STANDBY,
        PROGRAM_SOUS_VIDE
    ],
    4: [
        PROGRAM_STANDBY,
        PROGRAM_RICE_CEREALS, PROGRAM_FRYING, PROGRAM_STEAM, PROGRAM_BAKING,
        PROGRAM_STEWING, PROGRAM_MULTI_CHEF, PROGRAM_PILAF, PROGRAM_SOUP,
        PROGRAM_MILK_PORRIDGE, PROGRAM_YOGURT, PROGRAM_EXPRESS
    ],
    5: [
        PROGRAM_STANDBY,
        PROGRAM_MULTI_CHEF, PROGRAM_MILK_PORRIDGE, PROGRAM_STEWING, PROGRAM_FRYING,
        PROGRAM_SOUP, PROGRAM_STEAM, PROGRAM_PASTA, PROGRAM_LANGUOR,
        PROGRAM_COOKING, PROGRAM_BAKING, PROGRAM_RICE_CEREALS, PROGRAM_PILAF,
        PROGRAM_YOGURT, PROGRAM_PIZZA, PROGRAM_BREAD, PROGRAM_DESSERTS,
        PROGRAM_EXPRESS
    ],
    6: [
        PROGRAM_STANDBY,
        PROGRAM_MULTI_CHEF, PROGRAM_MILK_PORRIDGE, PROGRAM_STEWING, PROGRAM_FRYING,
        PROGRAM_SOUP, PROGRAM_STEAM, PROGRAM_PASTA, PROGRAM_LANGUOR,
        PROGRAM_COOKING, PROGRAM_BAKING, PROGRAM_RICE_CEREALS, PROGRAM_PILAF,
        PROGRAM_YOGURT, PROGRAM_PIZZA, PROGRAM_BREAD, PROGRAM_DESSERTS,
        PROGRAM_EXPRESS, PROGRAM_WARMING
    ],
    7: [
        PROGRAM_STANDBY,
        PROGRAM_FRYING, PROGRAM_RICE_CEREALS, PROGRAM_MULTI_CHEF, PROGRAM_PILAF,
        PROGRAM_STEAM, PROGRAM_BAKING, PROGRAM_STEWING, PROGRAM_SOUP,
        PROGRAM_MILK_PORRIDGE, PROGRAM_YOGURT, PROGRAM_EXPRESS, PROGRAM_WARMING_UP
    ],
}


######## Константы статусов ########


# Коды статусов
STATUS_OFF = 0x00
STATUS_WAIT = 0x01
STATUS_DELAYED_LAUNCH = 0x02
STATUS_WARMING = 0x03
STATUS_COOKING = 0x05
STATUS_AUTO_WARM = 0x06
STATUS_FULL_OFF = 0x0A

# Отображение кодов статусов на ключи переводов
STATUS_CODE_TO_TRANSLATION_KEY = {
    STATUS_OFF: "off",
    STATUS_WAIT: "wait",
    STATUS_COOKING: "cooking",
    STATUS_WARMING: "warming",
    STATUS_DELAYED_LAUNCH: "delayed_launch",
    STATUS_AUTO_WARM: "auto_warm",
    STATUS_FULL_OFF: "full_off"
}

# Определение структуры статуса
Status = namedtuple(
    "Status", [
        "program_id", "subprogram_id", "target_temperature", "auto_warm", "is_on",
        "sound_enabled", "parental_control", "error_code",
        "target_main_hours", "target_main_minutes",
        "target_additional_hours", "target_additional_minutes", "status", "program_name"
    ]
)
