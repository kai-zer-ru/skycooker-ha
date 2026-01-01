# Интеграционное тестирование SkyCooker в Docker

Этот гайд описывает как провести полноценное интеграционное тестирование SkyCooker интеграции в Home Assistant с использованием реального USB Bluetooth адаптера.

## Требования

- Docker и Docker Compose
- USB Bluetooth адаптер
- Linux/macOS система (Windows может потребовать дополнительной настройки)

## Подготовка

### 1. Подключение Bluetooth адаптера

Подключите USB Bluetooth адаптер к компьютеру:

```bash
# Проверка подключения
ls /dev/ttyUSB* /dev/ttyACM*
# или
lsusb
```

### 2. Проверка Bluetooth

```bash
# Проверка статуса Bluetooth
hciconfig
# или
bluetoothctl
```

## Запуск интеграционных тестов

### 1. Запуск тестов

```bash
chmod +x run_integration_test.sh
./run_integration_test.sh
```

**Или вручную:**

```bash
# Остановка предыдущих контейнеров
docker compose -f docker-compose.integration-test.yml down -v

# Запуск новых контейнеров
docker compose -f docker-compose.integration-test.yml up -d
```

### 2. Что происходит при запуске

Скрипт выполняет следующие действия:

1. **Проверка окружения** - наличие Docker, Bluetooth адаптера
2. **Запуск контейнеров** - Home Assistant и тестового окружения
3. **Проброс устройств** - USB Bluetooth адаптера в контейнеры
4. **Запуск Home Assistant** - с интеграцией SkyCooker

### 3. Архитектура тестовой среды

```
┌─────────────────────────────────────────┐
│           Docker Host                   │
│  ┌─────────────────┐  ┌───────────────┐ │
│  │ Home Assistant  │  │ Test Runner   │ │
│  │   Container     │  │   Container   │ │
│  │                 │  │               │ │
│  │ - HA Core       │  │ - Test Script │ │
│  │ - SkyCooker     │  │ - API Tests   │ │
│  │   Integration   │  │ - Integration │ │
│  │                 │  │   Tests       │ │
│  └─────────────────┘  └───────────────┘ │
│           │                    │        │
└───────────┼────────────────────┼────────┘
            │                    │
            └────────────────────┘
                   │
            ┌─────────────────┐
            │ USB Bluetooth   │
            │   Adapter       │
            │ (Real Device)   │
            └─────────────────┘
```

## Использование

### 1. Доступ к Home Assistant

После запуска откройте в браузере:
```
http://localhost:8123
```

### 2. Настройка интеграции

1. Перейдите в **Настройки → Интеграции**
2. Нажмите **Добавить интеграцию**
3. Найдите **SkyCooker**
4. Следуйте инструкциям по настройке

### 3. Проверка обнаружения устройства

Интеграция должна автоматически обнаружить ваш SkyCooker через Bluetooth.

## Команды управления

### Просмотр логов

```bash
# Логи Home Assistant
docker compose -f docker-compose.integration-test.yml logs -f home-assistant-test

# Логи тестового контейнера
docker compose -f docker-compose.integration-test.yml logs -f skycooker-test-runner

# Все логи
docker compose -f docker-compose.integration-test.yml logs -f
```

### Остановка тестов

```bash
docker compose -f docker-compose.integration-test.yml down -v
```

### Перезапуск тестов

```bash
docker compose -f docker-compose.integration-test.yml down -v
./run_integration_test.sh
```

## Файлы конфигурации

### docker-compose.integration-test.yml

Основной файл Docker Compose с двумя сервисами:
- `home-assistant-test` - контейнер с Home Assistant
- `skycooker-test-runner` - контейнер с тестами

### test_config/configuration.yaml

Конфигурация Home Assistant для тестирования:
- Включенный Bluetooth
- Отладочное логирование
- API доступ
- SkyCooker интеграция

### test_runner.py

Тестовый скрипт на Python:
- Проверка запуска Home Assistant
- Проверка Bluetooth
- Сканирование устройств
- Тестирование интеграции

## Возможные проблемы

### 1. Bluetooth не доступен

**Симптомы:**
- Ошибки Bluetooth в логах
- Устройства не обнаруживаются

**Решение:**
```bash
# Проверка Bluetooth адаптера
sudo hciconfig hci0 up

# Проверка прав доступа
ls -la /dev/ttyUSB*
sudo chmod 666 /dev/ttyUSB*
```

### 2. Docker не видит USB устройства

**Симптомы:**
- Ошибки доступа к USB
- Устройства не появляются в контейнере

**Решение:**
```bash
# Проверка проброса устройств
docker exec -it skycooker-ha-test ls /dev/ttyUSB*

# Перезапуск с правильными правами
sudo usermod -a -G dialout $USER
# Перезагрузка или перелогин
```

### 3. Home Assistant не запускается

**Симптомы:**
- Контейнер перезапускается
- Ошибки в логах

**Решение:**
```bash
# Проверка логов
docker compose -f docker-compose.integration-test.yml logs home-assistant-test

# Очистка и перезапуск
docker compose -f docker-compose.integration-test.yml down -v
docker system prune -f
./run_integration_test.sh
```

## Дополнительные возможности

### 1. Тестирование с разными устройствами

Измените MAC-адрес в конфигурации:
```yaml
# test_config/configuration.yaml
skycooker:
  device_address: "ВАШ_MAC_АДРЕС"
```

### 2. Расширенное логирование

Включите детальное логирование в конфигурации:
```yaml
logger:
  logs:
    custom_components.skycooker: debug
    homeassistant.components.bluetooth: debug
    bleak: debug
```

### 3. Автоматическое тестирование

Запустите автоматические тесты:
```bash
docker-compose -f docker-compose.integration-test.yml exec skycooker-test-runner python /app/test_runner.py
```

## Заключение

Эта тестовая среда позволяет:
- Тестировать интеграцию с реальным Bluetooth адаптером
- Проверять обнаружение устройств
- Тестировать все функции SkyCooker
- Отлаживать проблемы с подключением
- Проверять стабильность работы

Тестирование в Docker обеспечивает изолированную и воспроизводимую среду, что особенно важно для Bluetooth-устройств.