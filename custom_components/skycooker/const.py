# Constants for SkyCooker integration
DOMAIN = "skycooker"

MODEL_0 = 0
MODEL_1 = 1
MODEL_2 = 2
MODEL_3 = 3
MODEL_4 = 4
MODEL_5 = 5
MODEL_6 = 6
MODEL_7 = 7

# List of supported models
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

# Mode data for each model
MODE_DATA = {
    MODEL_0: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [100, 0, 35, 7], [97, 3, 0, 7], [110, 1, 0, 7],
        [180, 0, 15, 133], [100, 1, 0, 135], [100, 0, 8, 5], [95, 0, 35, 7],
        [99, 1, 0, 7], [40, 8, 0, 6], [145, 0, 45, 7], [100, 0, 40, 135],
        [100, 0, 40, 7]
    ],
    MODEL_1: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [100, 0, 30, 7], [100, 1, 0, 135], [100, 1, 30, 7],
        [100, 0, 35, 135], [100, 0, 40, 135], [100, 0, 50, 135], [97, 3, 0, 7],
        [170, 0, 18, 133], [145, 1, 0, 7], [150, 0, 30, 7], [110, 0, 35, 7],
        [38, 8, 0, 6], [150, 3, 0, 7], [100, 0, 8, 4], [98, 0, 15, 7],
        [40, 0, 10, 7], [63, 2, 30, 6], [160, 0, 18, 132], [98, 0, 20, 7],
        [100, 0, 20, 64]
    ],
    MODEL_2: [
        [0, 0, 0, 0],
        [100, 3, 0, 135], [170, 0, 18, 133], [100, 0, 8, 4], [145, 1, 0, 7],
        [100, 1, 0, 135], [38, 8, 0, 6], [100, 0, 30, 15], [40, 0, 10, 7],
        [110, 0, 35, 7], [100, 0, 40, 135], [140, 1, 0, 7], [98, 0, 20, 7],
        [150, 3, 0, 7], [100, 0, 20, 135], [100, 0, 15, 7], [98, 0, 30, 7],
        [97, 3, 0, 7], [100, 0, 30, 4], [160, 0, 16, 132], [100, 0, 40, 135],
        [100, 0, 30, 64], [70, 0, 0, 64]
    ],
    MODEL_3: [
        [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
        [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
        [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
        [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
        [0, 0, 0, 0], [62, 2, 30, 6]
    ],
    MODEL_4: [
        [0, 0, 0, 0],
        [100, 0, 10, 7], [150, 0, 15, 5], [100, 0, 25, 7], [140, 1, 0, 7],
        [100, 1, 0, 7], [100, 0, 30, 15], [110, 1, 0, 7], [100, 1, 0, 7],
        [100, 0, 30, 7], [38, 8, 0, 6], [100, 0, 0, 64]
    ],
    MODEL_5: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [97, 0, 10, 7], [100, 1, 0, 7], [170, 0, 15, 5],
        [99, 1, 0, 7], [100, 0, 20, 7], [100, 0, 8, 4], [97, 5, 0, 7],
        [100, 0, 40, 7], [145, 1, 0, 7], [100, 0, 35, 7], [110, 1, 0, 7],
        [38, 8, 0, 6], [150, 0, 25, 7], [150, 3, 0, 7], [98, 0, 20, 7],
        [100, 0, 20, 64]
    ],
    MODEL_6: [
        [0, 0, 0, 0],
        [100, 0, 30, 15], [97, 0, 10, 7], [100, 1, 0, 7], [170, 0, 15, 5],
        [99, 1, 0, 7], [100, 0, 20, 7], [100, 0, 8, 4], [97, 5, 0, 7],
        [100, 0, 40, 7], [145, 1, 0, 7], [100, 0, 35, 7], [110, 1, 0, 7],
        [38, 8, 0, 6], [150, 0, 25, 7], [150, 3, 0, 7], [98, 0, 20, 7],
        [100, 0, 0, 64], [100, 70, 30, 64]
    ],
    MODEL_7: [
        [0, 0, 0, 0],
        [150, 0, 15, 5], [100, 0, 25, 7], [100, 0, 30, 15], [110, 1, 0, 7],
        [100, 0, 25, 7], [140, 1, 0, 7], [100, 1, 0, 7], [100, 1, 0, 7],
        [100, 0, 30, 7], [40, 8, 0, 6], [100, 0, 20, 64], [70, 0, 30, 64]
    ],
}

# Constants for mode names
MODE_STANDBY = [
    "Standby Mode",
    "Режим ожидания",
]

MODE_MULTI_CHEF = [
    "Multi-chef",
    "Мультиповар",
]

MODE_RICE_CEREALS = [
    "Rice/Cereals",
    "Рис/Крупы",
]

MODE_LANGUOR = [
    "Languor",
    "Томление",
]

MODE_PILAF = [
    "Pilaf",
    "Плов",
]

MODE_FRYING = [
    "Frying",
    "Жарка",
]

MODE_STEWING = [
    "Stewing",
    "Тушение",
]

MODE_PASTA = [
    "Pasta",
    "Паста/Макароны",
]

MODE_MILK_PORRIDGE = [
    "Milk porridge",
    "Молочная каша",
]

MODE_SOUP = [
    "Soup",
    "Суп",
]

MODE_YOGURT = [
    "Yogurt",
    "Йогурт",
]

MODE_BAKING = [
    "Baking",
    "Выпечка",
]

MODE_STEAM = [
    "Steam",
    "На пару",
]

MODE_COOKING_LEGUMES = [
    "Cooking/Legumes",
    "Варка/Бобовые",
]

MODE_WILDFOWL = [
    "Wildfowl",
    "Дичь",
]

MODE_PIZZA = [
    "Pizza",
    "Пицца",
]

MODE_BREAD = [
    "Bread",
    "Хлеб",
]

MODE_BABY_FOOD = [
    "Baby food",
    "Детское питание",
]

MODE_SOUS_VIDE = [
    "Sous-vide",
    "Вакуум",
]

MODE_DEEP_FRYING = [
    "Deep frying",
    "Фритюр",
]

MODE_DESSERTS = [
    "Desserts",
    "Десерты",
]

MODE_EXPRESS = [
    "Express",
    "Экспресс",
]

MODE_GALANTINE = [
    "Galantine",
    "Холодец",
]

MODE_YOGURT_DOUGH = [
    "Yogurt/Dough",
    "Йогурт/Тесто",
]

MODE_CHEESECAKE = [
    "Cheesecake",
    "Запеканка/Чизкейк",
]

MODE_SOUS = [
    "Sous",
    "Соус",
]

MODE_WARMING_UP = [
    "Warming up",
    "Разогрев",
]

MODE_WARMING = [
    "Warming",
    "Подогрев",
]

MODE_COOKING = [
    "Cooking",
    "Варка",
]

MODE_NONE = [
    "None",
    "Нет"
]

# Mode names for each model
MODE_NAMES = {
    MODEL_0: [
        MODE_STANDBY,
        MODE_MULTI_CHEF, MODE_RICE_CEREALS, MODE_LANGUOR, MODE_PILAF,
        MODE_FRYING, MODE_STEWING, MODE_PASTA, MODE_MILK_PORRIDGE,
        MODE_SOUP, MODE_YOGURT, MODE_BAKING, MODE_STEAM,
        MODE_COOKING_LEGUMES
    ],
    MODEL_1: [
        MODE_STANDBY,
        MODE_MULTI_CHEF, MODE_RICE_CEREALS, MODE_SOUP, MODE_WILDFOWL,
        MODE_STEAM, MODE_COOKING, MODE_STEWING, MODE_LANGUOR,
        MODE_FRYING, MODE_BAKING, MODE_PIZZA, MODE_PILAF,
        MODE_YOGURT, MODE_BREAD, MODE_PASTA, MODE_MILK_PORRIDGE,
        MODE_BABY_FOOD, MODE_SOUS_VIDE, MODE_DEEP_FRYING, MODE_DESSERTS,
        MODE_EXPRESS
    ],
    MODEL_2: [
        MODE_STANDBY,
        MODE_GALANTINE, MODE_FRYING, MODE_PASTA, MODE_BAKING,
        MODE_STEWING, MODE_YOGURT_DOUGH, MODE_MULTI_CHEF, MODE_BABY_FOOD,
        MODE_PILAF, MODE_SOUP, MODE_CHEESECAKE, MODE_MILK_PORRIDGE,
        MODE_BREAD, MODE_STEAM, MODE_RICE_CEREALS, MODE_DESSERTS,
        MODE_LANGUOR, MODE_SOUS, MODE_DEEP_FRYING, MODE_COOKING,
        MODE_EXPRESS, MODE_WARMING_UP
    ],
    MODEL_3: [
        MODE_MULTI_CHEF, MODE_MILK_PORRIDGE, MODE_STEWING, MODE_FRYING,
        MODE_SOUP, MODE_STEAM, MODE_PASTA, MODE_LANGUOR,
        MODE_COOKING, MODE_BAKING, MODE_RICE_CEREALS, MODE_PILAF,
        MODE_YOGURT, MODE_PIZZA, MODE_BREAD, MODE_NONE,
        MODE_SOUS_VIDE, MODE_STANDBY
    ],
    MODEL_4: [
        MODE_STANDBY,
        MODE_RICE_CEREALS, MODE_FRYING, MODE_STEAM, MODE_BAKING,
        MODE_STEWING, MODE_MULTI_CHEF, MODE_PILAF, MODE_SOUP,
        MODE_MILK_PORRIDGE, MODE_YOGURT, MODE_EXPRESS
    ],
    MODEL_5: [
        MODE_STANDBY,
        MODE_MULTI_CHEF, MODE_MILK_PORRIDGE, MODE_STEWING, MODE_FRYING,
        MODE_SOUP, MODE_STEAM, MODE_PASTA, MODE_LANGUOR,
        MODE_COOKING, MODE_BAKING, MODE_RICE_CEREALS, MODE_PILAF,
        MODE_YOGURT, MODE_PIZZA, MODE_BREAD, MODE_DESSERTS,
        MODE_EXPRESS
    ],
    MODEL_6: [
        MODE_STANDBY,
        MODE_MULTI_CHEF, MODE_MILK_PORRIDGE, MODE_STEWING, MODE_FRYING,
        MODE_SOUP, MODE_STEAM, MODE_PASTA, MODE_LANGUOR,
        MODE_COOKING, MODE_BAKING, MODE_RICE_CEREALS, MODE_PILAF,
        MODE_YOGURT, MODE_PIZZA, MODE_BREAD, MODE_DESSERTS,
        MODE_EXPRESS, MODE_WARMING
    ],
    MODEL_7: [
        MODE_STANDBY,
        MODE_FRYING, MODE_RICE_CEREALS, MODE_MULTI_CHEF, MODE_PILAF,
        MODE_STEAM, MODE_BAKING, MODE_STEWING, MODE_SOUP,
        MODE_MILK_PORRIDGE, MODE_YOGURT, MODE_EXPRESS, MODE_WARMING_UP
    ],
}

# Product data for each model
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

# Cooking modes

# Product names for each model
PRODUCT_NAMES = {
    MODEL_0: [
        [
            "No choice", "Vegetables", "Fish", "Meat", "Bird"
        ],
        [
            "Нет выбора", "Овощи", "Рыба", "Мясо", "Птица"
        ],
    ],
    MODEL_1: [
        [
            "No choice", "Vegetables", "Fish", "Meat", "Bird", "Desserts"
        ],
        [
            "Нет выбора", "Овощи", "Рыба", "Мясо", "Птица", "Десерты"
        ],
    ],
    MODEL_2: [
        [
            "No choice", "Vegetables", "Fish", "Meat", "Bird", "Desserts"
        ],
        [
            "Нет выбора", "Овощи", "Рыба", "Мясо", "Птица", "Десерты"
        ],
    ],
}

# Status codes
STATUS_OFF = 0x00
STATUS_WAIT = 0x01
STATUS_DELAYED_LAUNCH = 0x02
STATUS_WARMING = 0x03
STATUS_COOKING = 0x05
STATUS_AUTO_WARM = 0x06
STATUS_FULL_OFF = 0x0A

STATUS_CODES = [
    {
        STATUS_OFF: "Off",
        STATUS_WAIT: "Waiting",
        STATUS_COOKING: "Cooking",
        STATUS_WARMING: "Warming",
        STATUS_DELAYED_LAUNCH: "Delayed Launch",
        STATUS_AUTO_WARM: "Auto Warm",
    },
    {
        STATUS_OFF: "Выключена",
        STATUS_WAIT: "Ожидание",
        STATUS_COOKING: "Готовка",
        STATUS_WARMING: "Разогрев",
        STATUS_DELAYED_LAUNCH: "Отложенный старт",
        STATUS_AUTO_WARM: "Подогрев",
    }
]


# Config flow constants
CONF_PERSISTENT_CONNECTION = "persistent_connection"
CONF_MODEL = "model"

# Default values
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PERSISTENT_CONNECTION = True

# Friendly names
FRIENDLY_NAME = "SkyCooker"
SKYCOOKER_NAME = "SkyCooker"
MANUFACTORER = "Redmond"

# Button types
BUTTON_TYPE_START = "start"
BUTTON_TYPE_STOP = "stop"
BUTTON_TYPE_START_DELAYED = "start_delayed"

# Select types
SELECT_TYPE_MODE = "mode"
SELECT_TYPE_SUBPROGRAM = "subprogram"
SELECT_TYPE_TEMPERATURE = "temperature"
SELECT_TYPE_COOKING_TIME_HOURS = "cooking_time_hours"
SELECT_TYPE_COOKING_TIME_MINUTES = "cooking_time_minutes"
SELECT_TYPE_DELAYED_START_HOURS = "delayed_start_hours"
SELECT_TYPE_DELAYED_START_MINUTES = "delayed_start_minutes"

# Sensor types
SENSOR_TYPE_STATUS = "status"
SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_REMAINING_TIME = "remaining_time"
SENSOR_TYPE_TOTAL_TIME = "total_time"
SENSOR_TYPE_AUTO_WARM_TIME = "auto_warm_time"
SENSOR_TYPE_SUCCESS_RATE = "success_rate"
SENSOR_TYPE_DELAYED_LAUNCH_TIME = "delayed_launch_time"
SENSOR_TYPE_CURRENT_MODE = "current_mode"
SENSOR_TYPE_SUBPROGRAM = "subprogram"

# Switch types
SWITCH_TYPE_AUTO_WARM = "auto_warm"

# BLE settings
UUID_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UUID_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
BLE_RECV_TIMEOUT = 1.5
MAX_TRIES = 3
TRIES_INTERVAL = 0.5
STATS_INTERVAL = 15
TARGET_TTL = 30

# Data keys
DATA_CONNECTION = "connection"
DATA_CANCEL = "cancel"
DATA_WORKING = "working"
DATA_DEVICE_INFO = "device_info"

# Dispatcher
DISPATCHER_UPDATE = "update"

# Commands
COMMAND_GET_VERSION = 0x01
COMMAND_TURN_ON = 0x03
COMMAND_TURN_OFF = 0x04
COMMAND_SET_MAIN_MODE = 0x05
COMMAND_GET_STATUS = 0x06
COMMAND_SELECT_MODE = 0x09
COMMAND_SYNC_TIME = 0x6E
COMMAND_GET_TIME = 0x6F
COMMAND_AUTH = 0xFF

# Bit flags for mode settings (uint8_t)
# Битовые флаги для настроек режима
BIT_FLAG_SUBMODE_ENABLE = 0x80        # B[7] - включение подрежима
BIT_FLAG_AUTOPOWER_ENABLE = 0x40      # B[6] - включение автопита
BIT_FLAG_EXPANSION_MODES_ENABLE = 0x20 # B[5] - включение расширенных режимов
BIT_FLAG_TWO_BOWL_ENABLE = 0x10       # B[4] - включение двух чаш
BIT_FLAG_PRESET_TEMP_ENABLE = 0x08    # B[3] - включение предварительной температуры
BIT_FLAG_MASTERCHEF_LIGHT_ENABLE = 0x04 # B[2] - включение подсветки MasterChef
BIT_FLAG_DELAY_START_ENABLE = 0x02    # B[1] - включение отложенного старта
BIT_FLAG_POSTHEAT_ENABLE = 0x01       # B[0] - включение подогрева
