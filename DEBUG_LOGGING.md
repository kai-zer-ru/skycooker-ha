# Включение Debug-логов для SkyCooker

## Как включить debug-логи

Для диагностики проблем с интеграцией SkyCooker можно включить подробное логирование.

### 1. Через Configuration.yaml

Добавьте в ваш `configuration.yaml` следующую конфигурацию:

```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: debug
    bleak: debug
    bleak_retry_connector: debug
```

### 2. Через веб-интерфейс HomeAssistant

1. Перейдите в **Настройки** → **Система** → **Журнал**
2. Нажмите на **Настроить уровень ведения журнала**
3. Добавьте следующие компоненты:
   - `custom_components.skycooker: debug`
   - `bleak: debug`
   - `bleak_retry_connector: debug`
4. Нажмите **Сохранить**

### 3. Через Lovelace UI

1. Перейдите в **Настройки** → **Панели** → **Lovelace**
2. Найдите карточку **Журнал**
3. Нажмите на **Настроить уровень ведения журнала**
4. Добавьте нужные компоненты

## Уровни логирования

### INFO (рекомендуется для повседневного использования)
- Включение/выключение устройства
- Установка температуры и режимов
- Ошибки подключения
- Статус устройства

### DEBUG (для диагностики проблем)
- Все команды Bluetooth
- Детали подключения
- Отладочная информация о протоколе
- Внутренние состояния

### WARNING
- Предупреждения о неоптимальных настройках
- Проблемы с производительностью

### ERROR
- Критические ошибки
- Сбои подключения
- Проблемы с аутентификацией

## Примеры полезных логов

### Успешное подключение
```
2026-01-01 15:30:15 INFO (MainThread) [custom_components.skycooker.cooker_connection] Connecting to the Cooker DA:D8:9F:9E:0B:4C...
2026-01-01 15:30:15 INFO (MainThread) [custom_components.skycooker.cooker_connection] Connected to the Cooker
2026-01-01 15:30:15 INFO (MainThread) [custom_components.skycooker.cooker_connection] Subscribed to RX
2026-01-01 15:30:15 INFO (MainThread) [custom_components.skycooker.skycooker] Auth: ok=True
2026-01-01 15:30:15 INFO (MainThread) [custom_components.skycooker.skycooker] Version: 1.0
```

### Ошибка подключения
```
2026-01-01 15:30:15 ERROR (MainThread) [custom_components.skycooker.cooker_connection] Failed to connect to cooker: Device with MAC address DA:D8:9F:9E:0B:4C not found
2026-01-01 15:30:15 ERROR (MainThread) [custom_components.skycooker.cooker_connection] Can't update status, BleakOutOfConnectionSlotsError: RMC-M40S - DA:D8:9F:9E:0B:4C: Failed to connect after 9 attempt(s)
```

### Команды Bluetooth (только в debug-режиме)
```
2026-01-01 15:30:15 DEBUG (MainThread) [custom_components.skycooker.cooker_connection] Writing command 05, data: [05 00 5a 00]
2026-01-01 15:30:15 DEBUG (MainThread) [custom_components.skycooker.cooker_connection] Received: 55 05 05 00 5a 00 aa
```

## Фильтрация логов

### Через командную строку
```bash
# Просмотр логов SkyCooker
sudo journalctl -u home-assistant -f | grep "skycooker"

# Просмотр только ошибок
sudo journalctl -u home-assistant -f | grep "skycooker.*ERROR"

# Просмотр за определенный период
sudo journalctl -u home-assistant --since="2026-01-01 15:00:00" | grep "skycooker"
```

### Через веб-интерфейс
1. Перейдите в **Настройки** → **Система** → **Журнал**
2. В поле **Фильтр** введите: `skycooker`
3. Выберите нужный уровень логирования

## Советы по диагностике

### Проблемы с Bluetooth
1. Включите debug-логи для `bleak` и `bleak_retry_connector`
2. Ищите сообщения о подключении и ошибках
3. Проверьте MAC-адрес устройства

### Проблемы с аутентификацией
1. Включите debug-логи для `custom_components.skycooker`
2. Ищите сообщения об аутентификации
3. Проверьте, что устройство в режиме пары

### Проблемы с командами
1. Включите debug-логи для `custom_components.skycooker`
2. Ищите сообщения о отправке и получении команд
3. Проверьте формат данных

## Отключение debug-логов

После диагностики рекомендуется отключить debug-логи, так как они могут сильно увеличивать размер лог-файлов:

```yaml
logger:
  default: info
  logs:
    custom_components.skycooker: info  # Измените с debug на info
```

Или удалите строки с debug-логами из конфигурации.

## Перезагрузка HomeAssistant

После изменения настроек логирования необходимо перезагрузить HomeAssistant:

1. Перейдите в **Настройки** → **Система**
2. Нажмите **Перезагрузить**
3. Дождитесь полной перезагрузки системы

## Пример полной конфигурации для диагностики

```yaml
logger:
  default: info
  logs:
    # Основные логи интеграции
    custom_components.skycooker: debug
    
    # Bluetooth логи
    bleak: debug
    bleak_retry_connector: debug
    
    # Системные логи
    homeassistant.components.bluetooth: debug
    homeassistant.components.bluetooth_tracker: debug

# Дополнительные настройки
homeassistant:
  allowlist_external_dirs:
    - /config
```

Эта конфигурация поможет максимально подробно диагностировать любые проблемы с подключением и работой интеграции.