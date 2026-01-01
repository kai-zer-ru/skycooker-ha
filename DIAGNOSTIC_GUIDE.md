# Диагностический гид по SkyCooker

## Проблема: "Устройства Redmond не найдены"

Если вы видите сообщение "Устройства Redmond не найдены" при работающем Bluetooth, следуйте этой инструкции.

## Быстрая диагностика

### 1. Запустите скрипт диагностики Bluetooth

```bash
# Установите зависимости (если нужно)
pip3 install bleak bleak-retry-connector

# Запустите диагностику
python3 diagnose_bluetooth.py
```

**Что делает скрипт:**
- Сканирует все Bluetooth устройства в радиусе действия
- Ищет устройства с именами RMC, SkyCooker, Redmond
- Проверяет наличие устройства по MAC-адресу DA:D8:9F:9E:0B:4C
- Показывает уровень сигнала (RSSI) для каждого устройства

**Ожидаемый результат:**
```
🔍 Начинаем сканирование Bluetooth устройств...
✅ Найдено 5 Bluetooth устройств
🎯 Найдено устройство SkyCooker: RMC-M40S - DA:D8:9F:9E:0B:4C (RSSI: -45)
✅ Найдено 1 устройств SkyCooker
```

### 2. Запустите улучшенный тест подключения

```bash
# Запустите улучшенный тест (указываете свой MAC-адрес)
python3 test_connection_improved.py DA:D8:9F:9E:0B:4C
```

**Что делает скрипт:**
- Ищет целевое устройство по MAC-адресу
- Пытается установить Bluetooth соединение
- Проверяет доступные сервисы и характеристики
- Пробует аутентификацию с ключом по умолчанию

**Ожидаемый результат:**
```
🚀 Starting SkyCooker connection test
🔍 Scanning for device DA:D8:9F:9E:0B:4C...
✅ Found target device: RMC-M40S - DA:D8:9F:9E:0B:4C (RSSI: -45)
🔗 Connecting to DA:D8:9F:9E:0B:4C...
✅ Connected successfully
📋 Available services: 3
  - Service: 00001800-0000-1000-8000-00805f9b34fb
    - Characteristic: 00002a00-0000-1000-8000-00805f9b34fb
    - Characteristic: 00002a01-0000-1000-8000-00805f9b34fb
    - Characteristic: 00002a04-0000-1000-8000-00805f9b34fb
  - Service: 00001801-0000-1000-8000-00805f9b34fb
    - Characteristic: 00002a05-0000-1000-8000-00805f9b34fb
  - Service: 6e400001-b5a3-f393-e0a9-e50e24dcca9e
    - Characteristic: 6e400002-b5a3-f393-e0a9-e50e24dcca9e
    - Characteristic: 6e400003-b5a3-f393-e0a9-e50e24dcca9e
🔑 Attempting authentication...
✅ Authentication successful
📋 Requesting device version...
✅ Device info request sent
🔌 Disconnected
✅ Test completed successfully!
```

## Распространенные проблемы и решения

### Проблема 1: Устройство не найдено вовсе

**Симптомы:**
```
⚠️ Устройства SkyCooker не найдены
📋 Все найденные устройства:
  - Some Other Device: AA:BB:CC:DD:EE:FF (RSSI: -80)
```

**Решение:**
1. **Проверьте питание устройства** - Убедитесь, что RMC-M40S включен
2. **Режим сопряжения** - Устройство должно быть в режиме сопряжения (индикатор Bluetooth мигает)
3. **Расстояние** - Подойдите ближе к устройству (5-10 метров)
4. **Препятствия** - Уберите металлические предметы и другие помехи
5. **Перезагрузка** - Перезагрузите RMC-M40S

### Проблема 2: Устройство найдено, но не подключается

**Симптомы:**
```
🔍 Scanning for device DA:D8:9F:9E:0B:4C...
✅ Found target device: RMC-M40S - DA:D8:9F:9E:0B:4C (RSSI: -70)
🔗 Connecting to DA:D8:9F:9E:0B:4C...
❌ Connection error: [Errno 110] Operation timed out
```

**Решение:**
1. **Улучшите сигнал** - Подойдите ближе к устройству
2. **Проверьте режим сопряжения** - Индикатор должен мигать
3. **Перезагрузите Bluetooth адаптер:**
   ```bash
   sudo systemctl restart bluetooth
   ```
4. **Проверьте другие подключения** - Убедитесь, что устройство не подключено к другому приложению

### Проблема 3: Подключение есть, но аутентификация не проходит

**Симптомы:**
```
✅ Connected successfully
📋 Available services: 3
🔑 Attempting authentication...
❌ Authentication failed: 55 01 ff 00 aa
```

**Решение:**
1. **Проверьте режим сопряжения** - Устройство должно быть в режиме сопряжения
2. **Попробуйте другие ключи:**
   - `000000` (по умолчанию)
   - `123456`
   - `111111`
3. **Перезагрузите устройство** и повторите попытку

## Проверка Bluetooth на сервере HomeAssistant

### Проверка доступности Bluetooth

```bash
# Проверка статуса Bluetooth
systemctl status bluetooth

# Сканирование устройств
hcitool scan

# Проверка адаптера
hciconfig -a
```

### Проверка прав доступа

```bash
# Проверка прав на Bluetooth
ls -la /dev/ttyACM*

# Добавление пользователя в группу Bluetooth
sudo usermod -a -G bluetooth homeassistant
```

## Настройка HomeAssistant

### Включение дебаг логов

Добавьте в `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: debug
    homeassistant.components.bluetooth: debug
```

### Проверка в интерфейсе

1. **Настройки → Система → Журнал**
2. **Фильтр: `skycooker`**
3. **Ищите сообщения:**
   - `🔍 Scanning for Bluetooth devices...`
   - `🎯 Found SkyCooker device`
   - `❌ No SkyCooker devices found`

## Если ничего не помогает

1. **Проверьте MAC-адрес** - Убедитесь, что вы используете правильный MAC-адрес
2. **Попробуйте другой Bluetooth адаптер** - Возможно, текущий адаптер не поддерживает нужные характеристики
3. **Проверьте совместимость** - Убедитесь, что ваша модель RMC-M40S поддерживается
4. **Создайте issue** - Приложите логи и результаты диагностики

## Полезные команды

```bash
# Проверка установленных пакетов
pip3 list | grep bleak

# Проверка Bluetooth устройств
bluetoothctl
> scan on
> devices

# Проверка системных логов
journalctl -u bluetooth -f
```

## Поддержка

Если после всех проверок проблема не решена:
1. Запустите диагностические скрипты
2. Соберите логи HomeAssistant с фильтром `skycooker`
3. Создайте issue в репозитории с описанием проблемы и всеми логами