# Устранение неполадок SkyCooker

## Проблемы с подключением

### Ошибка: "No backend with an available connection slot" / "BleakOutOfConnectionSlotsError"

**Причина:** Bluetooth адаптер исчерпал лимит одновременных подключений. Это может происходить при:
- Наличии других Bluetooth интеграций (например, ha_kettler)
- Слишком частом опросе устройств
- Неправильном управлении соединениями

**Решение:**
1. **Увеличьте интервал опроса** в настройках интеграции (рекомендуется 30-60 секунд)
2. **Включите постоянное соединение** в настройках интеграции
3. **Перезагрузите Bluetooth адаптер:**
   ```bash
   sudo systemctl restart bluetooth
   ```
4. **Перезагрузите HomeAssistant**
5. **Проверьте другие Bluetooth интеграции** - временно отключите другие Bluetooth устройства для тестирования
6. **Убедитесь, что устройство включено** и в режиме сопряжения

**Для пользователей с несколькими Bluetooth устройствами:**
- **Рассмотрите возможность использования Bluetooth прокси** (если возможно)
- **Увеличьте интервалы опроса** для всех Bluetooth устройств (рекомендуется 60+ секунд)
- **Используйте постоянные соединения** только для критически важных устройств
- **Временно отключите другие Bluetooth интеграции** для тестирования
- **Перезагрузите Bluetooth адаптер** при возникновении проблем:
  ```bash
  sudo systemctl restart bluetooth
  ```
- **Проверьте физическое расположение устройств** - Bluetooth адаптер может не справляться с несколькими устройствами на расстоянии

### Ошибка: "BleakClient.connect() called without bleak-retry-connector"

**Причина:** Интеграция не может использовать bleak-retry-connector для надежного подключения.

**Решение:**
1. **Проверьте зависимости** - убедитесь, что bleak-retry-connector установлен:
   ```bash
   pip3 list | grep bleak-retry-connector
   ```
2. **Перезагрузите HomeAssistant** для загрузки зависимостей
3. **Проверьте manifest.json** - убедитесь, что зависимость указана:
   ```json
   "requirements": ["bleak-retry-connector>=1.0.0"]
   ```
4. **Если проблема сохраняется** - попробуйте переустановить интеграцию

### Ошибка: "Device with MAC address XX:XX:XX:XX:XX:XX not found"

### Ошибка: "Device with MAC address XX:XX:XX:XX:XX:XX not found"

**Причина:** HomeAssistant не может найти устройство по MAC-адресу.

**Решение:**
1. Проверьте MAC-адрес устройства
2. Убедитесь, что устройство включено и в пределах досягаемости
3. Проверьте, что Bluetooth адаптер работает:
   ```bash
   hcitool scan
   ```
4. Перезагрузите устройство и попробуйте снова

### Ошибка: "Auth failed"

**Причина:** Неверный ключ авторизации или устройство не в режиме сопряжения.

**Решение:**
1. Убедитесь, что устройство в режиме сопряжения (обычно мигает индикатор)
2. Попробуйте стандартный ключ "000000"
3. Если не работает, попробуйте другие варианты: "123456", "111111"
4. Перезагрузите устройство и повторите попытку

## Проблемы с управлением

### Команды не выполняются

**Причина:** Проблемы с соединением или протоколом.

**Решение:**
1. Проверьте статус подключения в интерфейсе HomeAssistant
2. Включите постоянное соединение в настройках интеграции
3. Попробуйте перезагрузить интеграцию:
   - Настройки → Интеграции → SkyCooker → Удалить
   - Добавьте интеграцию заново

### Неправильные показания

**Причина:** Устройство не поддерживает запрашиваемые данные.

**Решение:**
1. Проверьте, что ваша модель поддерживается
2. Попробуйте перезагрузить устройство
3. Проверьте логи HomeAssistant на наличие ошибок

## Проблемы с производительностью

### Частые разрывы соединения

**Причина:** Слабый Bluetooth сигнал или помехи.

**Решение:**
1. Уменьшите расстояние между устройством и сервером HomeAssistant
2. Уберите препятствия между устройствами
3. Отключите другие Bluetooth устройства, которые могут создавать помехи
4. Включите постоянное соединение в настройках

### Медленное реагирование

**Причина:** Высокая нагрузка на систему или проблемы с Bluetooth.

**Решение:**
1. Проверьте загрузку CPU и памяти сервера
2. Увеличьте интервал опроса в настройках интеграции
3. Перезагрузите HomeAssistant

## Проверка Bluetooth

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

## Логи и диагностика

### Включение дебаг логов

Для подробной диагностики включите дебаг логирование:

#### Через configuration.yaml
Добавьте в ваш `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: debug
    homeassistant.components.bluetooth: debug
```

#### Через UI (HomeAssistant 2021.6+)
1. Перейдите в Настройки → Система → Журнал
2. Нажмите "Load Full Home Assistant Log"
3. Нажмите "Add Filter"
4. Добавьте фильтр для `custom_components.skycooker` с уровнем `DEBUG`
5. Нажмите "Start Logging"

### Что показывают дебаг логи

- **Подключение устройства**: `🔗 Starting connection to cooker`, `✅ Successfully connected`
- **Аутентификация**: `🔑 Performing authentication`, `✅ Authentication successful`
- **Команды**: `📡 Sending command`, `📥 Received response`
- **Статус**: `📊 Requesting device status`, `✅ Status retrieved`
- **Ошибки**: `❌ Connection failed`, `⚠️ Connection attempt failed`

### Просмотр логов HomeAssistant

1. Настройки → Система → Журнал
2. Фильтр: `skycooker`
3. Ищите сообщения об ошибках
4. Для дебаг логов используйте фильтр: `custom_components.skycooker`

### Проверка состояния интеграции

1. Настройки → Интеграции → SkyCooker
2. Проверьте статус подключения
3. Проверьте доступные entity
4. Включите дебаг логи для подробной информации (см. раздел выше)

### Примеры полезных логов

#### Успешное подключение
```
🔗 Starting connection to cooker DA:D8:9F:9E:0B:4C (model: RMC-M40S)
✅ Device found: RMC-M40S (DA:D8:9F:9E:0B:4C)
🔌 Connection attempt 1/5...
✅ Successfully connected to cooker (attempt 1)
📡 Starting notifications on RX characteristic...
✅ Subscribed to RX notifications
🔑 Performing authentication...
✅ Authentication successful
📋 Getting device version...
📋 Device version: (1, 0)
⏰ Synchronizing device time...
✅ Time synchronized: 2026-01-01 17:00:00 (GMT+8.00)
✅ Authentication and setup completed successfully
```

#### Ошибки подключения
```
❌ Failed to connect to cooker DA:D8:9F:9E:0B:4C after 5 attempts: [Errno 110] Operation timed out
⚠️ Connection attempt 1 failed: [Errno 110] Operation timed out
❌ Bluetooth connection slots exhausted for DA:D8:9F:9E:0B:4C
❌ Auth failed. You need to enable pairing mode on the cooker.
❌ Command failed: not connected
❌ Failed to get status: [Errno 110] Operation timed out
```

#### Команды и ответы
```
⚙️ Setting main mode: mode=2 (Rice/Cereals), target_temp=60, boil_time=0
📦 Packed data for RMC-M40S: 55 01 05 02 3c 80 aa
📡 Sending command 05, data: [02 3c 80]
📤 Data sent successfully
📥 Received response: 55 01 05 01 aa
✅ Mode set successfully: mode=2 (Rice/Cereals), target_temp=60, boil_time=0
```

## Поддержка

Если проблемы не решаются:

1. Соберите логи HomeAssistant с фильтром `skycooker`
2. Проверьте, что ваша модель устройства поддерживается
3. Создайте issue в репозитории с описанием проблемы и логами

## Языковые версии

- [Русская версия](TROUBLESHOOTING.md)
- [English version](TROUBLESHOOTING_EN.md)
4. Укажите модель устройства, версию HomeAssistant и систему

## Часто задаваемые вопросы

**Q: Почему интеграция не видит мое устройство?**
A: Проверьте, что устройство включено, в режиме сопряжения и в пределах досягаемости Bluetooth.

**Q: Можно ли использовать несколько устройств?**
A: Да, каждое устройство добавляется отдельно с уникальным MAC-адресом.

**Q: Нужно ли постоянно держать соединение?**
A: Рекомендуется включить постоянное соединение для лучшей производительности, но это увеличивает энергопотребление.

**Q: Что делать, если устройство перестало работать после обновления?**
A: Попробуйте удалить и добавить интеграцию заново, проверьте обновления интеграции.