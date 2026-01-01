# Тестирование SkyCooker в HomeAssistant VM (ProxMox)

## Ситуация
- HomeAssistant установлен как виртуальная машина в ProxMox
- Компонент уже скачан в `custom_components/skycooker`
- Доступ к терминалу через аддон HomeAssistant

## Варианты тестирования

### Вариант 1: Тестирование через SSH (рекомендуется)

#### 1. Подключение к VM через SSH
```bash
# Подключитесь к вашей ProxMox VM
ssh root@ваш_адрес_vm

# Или через ProxMox консоль
# В ProxMox → ваша VM → Console
```

#### 2. Проверка наличия Bluetooth
```bash
# Проверьте, есть ли Bluetooth адаптер
hciconfig -a

# Если нет, возможно, нужно добавить USB Bluetooth адаптер к VM
# В ProxMox: VM → Hardware → Add → USB Device
```

#### 3. Установка зависимостей (если нужно)
```bash
# Обновите пакеты
apt update

# Установите Python и зависимости
apt install python3 python3-pip
pip3 install bleak bleak-retry-connector

# Или установите через apt (если доступно)
apt install python3-bleak python3-bleak-retry-connector
```

#### 4. Запуск автономного теста
```bash
# Перейдите в директорию с компонентом
cd /config/custom_components/skycooker

# Скопируйте автономный тест (если его нет)
# Скачайте test_connection_standalone.py из репозитория

# Запустите тест
python3 test_connection_standalone.py
```

### Вариант 2: Тестирование через HomeAssistant аддон

#### 1. Установка Terminal & SSH аддона
- В HomeAssistant → Supervisor → Add-on Store
- Найдите "Terminal & SSH" и установите
- Запустите аддон

#### 2. Подключение к аддону
```bash
# Подключитесь к аддону через SSH
ssh root@ваш_адрес_ha -p 22222

# Пароль: ваш пароль от HomeAssistant
```

#### 3. Запуск тестов
```bash
# Перейдите в директорию с компонентом
cd /config/custom_components/skycooker

# Запустите автономный тест
python3 test_connection_standalone.py
```

### Вариант 3: Тестирование через Python аддон

#### 1. Установка Python аддона
- В HomeAssistant → Supervisor → Add-on Store
- Найдите "Python" аддон и установите
- Запустите аддон

#### 2. Создание тестового скрипта
```python
# В аддоне Python создайте новый скрипт
import sys
sys.path.insert(0, '/config/custom_components/skycooker')

from test_connection_standalone import main

if __name__ == "__main__":
    main()
```

## Что делать, если нет Bluetooth адаптера

### 1. Добавление USB Bluetooth адаптера в ProxMox VM

#### Через ProxMox веб-интерфейс:
1. Остановите VM
2. ProxMox → ваша VM → Hardware → Add → USB Device
3. Выберите ваш Bluetooth адаптер
4. Запустите VM

#### Через командную строку:
```bash
# Найдите Bluetooth адаптер
lsusb

# Добавьте в конфигурацию VM (например, для VM ID 100)
qm set 100 -usb0 host=vendor_id:product_id,usb3=1

# Где vendor_id:product_id - ID вашего Bluetooth адаптера
```

### 2. Проверка доступности Bluetooth в VM
```bash
# Проверьте, виден ли Bluetooth адаптер
hciconfig -a

# Если виден, включите его
hciconfig hci0 up

# Проверьте статус
systemctl status bluetooth
```

## Типичные проблемы и решения

### Проблема: "No Bluetooth adapter found"
**Решение:**
1. Убедитесь, что Bluetooth адаптер подключен к VM
2. Проверьте, что адаптер поддерживается Linux
3. Перезагрузите VM после подключения адаптера

### Проблема: "Permission denied"
**Решение:**
```bash
# Дайте права на Bluetooth
sudo usermod -a -G bluetooth homeassistant

# Или запустите от root
sudo python3 test_connection_standalone.py
```

### Проблема: "ModuleNotFoundError"
**Решение:**
```bash
# Установите зависимости
pip3 install bleak bleak-retry-connector

# Или через apt
apt install python3-bleak python3-bleak-retry-connector
```

### Проблема: "Device not found"
**Решение:**
1. Убедитесь, что мультиварка включена и в режиме пары
2. Проверьте расстояние до устройства (не более 10 метров)
3. Попробуйте перезагрузить Bluetooth:
   ```bash
   sudo systemctl restart bluetooth
   ```

## Рекомендуемый порядок действий

### Шаг 1: Проверка Bluetooth
```bash
# Проверьте наличие адаптера
hciconfig -a

# Если нет адаптера - добавьте USB Bluetooth адаптер к VM
```

### Шаг 2: Установка зависимостей
```bash
# Установите Python и зависимости
apt update
apt install python3 python3-pip
pip3 install bleak bleak-retry-connector
```

### Шаг 3: Запуск автономного теста
```bash
# Перейдите в директорию с компонентом
cd /config/custom_components/skycooker

# Запустите тест
python3 test_connection_standalone.py
```

### Шаг 4: Проверка результатов
- Если тест проходит - Bluetooth работает
- Если нет - проверьте настройки VM и Bluetooth адаптер

## Альтернативные варианты

### Если нет возможности добавить Bluetooth адаптер:
1. **Тестирование на другом устройстве** - запустите тесты на другом компьютере
2. **Использование Bluetooth прокси** - рассмотрите использование ESPHome Bluetooth прокси
3. **Проверка логики** - автономный тест проверяет логику протокола без реального подключения

### Для проверки логики протокола:
```bash
# Автономный тест работает без реального Bluetooth
python3 test_connection_standalone.py

# Он проверяет:
# - Корректность протокола
# - Логику команд
# - Обработку данных
```

## Полезные команды

```bash
# Проверка Bluetooth адаптера
hciconfig -a

# Сканирование устройств
hcitool scan

# Проверка статуса Bluetooth
systemctl status bluetooth

# Перезагрузка Bluetooth
sudo systemctl restart bluetooth

# Проверка логов
journalctl -u bluetooth -f

# Проверка Python версии
python3 --version

# Проверка установленных пакетов
pip3 list | grep bleak
```

## Следующие шаги после успешного тестирования

1. **Настройка интеграции** в HomeAssistant
2. **Добавление устройства** через интерфейс
3. **Проверка работы** всех функций
4. **Настройка автоматизаций** при необходимости