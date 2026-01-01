# SkyCooker HA - Интеграция для мультиварок Redmond

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Интеграция HomeAssistant для управления мультиварками Redmond серии RMC, включая модель RMC-M40S.

## Особенности

✅ **Полная поддержка RMC-M40S**  
✅ **11 программ приготовления** (Суп, Каша, Плов, На пару, Выпечка, Жарка, Тушение, Йогурт, Тесто, Подогрев)  
✅ **Управление температурой** (35-120°C)  
✅ **Таймер отложенного старта** (1-240 минут)  
✅ **Bluetooth подключение** с оптимизацией для стабильной работы  
✅ **Полная интеграция с HomeAssistant** (switch, sensor, number, select)  
✅ **Поддержка автоматизаций и сценариев**  

## Поддерживаемые модели

- **RMC-M40S** (основная поддержка)
- Другие модели серии RMC (через автоматическое определение)

## Установка

### Через HACS (рекомендуется)

1. Установите [HACS](https://hacs.xyz/)
2. Добавьте репозиторий: `https://github.com/ClusterM/skycooker-ha`
3. Установите интеграцию "SkyCooker"
4. Перезагрузите HomeAssistant

### Вручную

1. Скачайте репозиторий
2. Скопируйте папку `custom_components/skycooker` в `custom_components` вашей HomeAssistant
3. Перезагрузите HomeAssistant

## Настройка

1. Перейдите в **Настройки** → **Устройства и службы** → **Интеграции**
2. Нажмите **Добавить интеграцию**
3. Выберите **SkyCooker**
4. Следуйте инструкциям на экране

### Требования

- **Bluetooth адаптер** на сервере HomeAssistant
- **Мультиварка Redmond** включена и в режиме пары
- **Расстояние** до мультиварки не более 10 метров

## Использование

### Через интерфейс HomeAssistant

После настройки вы получите:

- **Основное устройство** - управление включением/выключением
- **Выбор программы** - выпадающий список с 11 программами
- **Температура** - регулировка температуры приготовления
- **Таймер** - установка времени приготовления
- **Отложенный старт** - таймер отложенного включения

### Через Lovelace

Добавьте entity в свою панель:

```yaml
type: entities
entities:
  - entity: switch.skycooker_power
  - entity: select.skycooker_program
  - entity: number.skycooker_temperature
  - entity: number.skycooker_timer
```

### Через автоматизации

Пример автоматизации для приготовления супа:

```yaml
automation:
  - alias: "Приготовить суп вечером"
    trigger:
      - platform: time
        at: "18:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.skycooker_program
        data:
          option: "Soup"
      - service: number.set_value
        target:
          entity_id: number.skycooker_temperature
        data:
          value: 90
      - service: number.set_value
        target:
          entity_id: number.skycooker_timer
        data:
          value: 60
      - service: switch.turn_on
        target:
          entity_id: switch.skycooker_power
```

## Тестирование подключения

Для проверки подключения используйте тестовый скрипт:

```bash
python test_connection.py
```

Скрипт поможет:
- Найти MAC-адрес вашей мультиварки
- Проверить Bluetooth соединение
- Протестировать основные функции
- Диагностировать проблемы

## Решение проблем

### Bluetooth проблемы

**"BleakOutOfConnectionSlotsError"**
- Решение: Используйте постоянное подключение (включено по умолчанию)
- Решение: Перезагрузите Bluetooth адаптер: `sudo systemctl restart bluetooth`

**"Auth failed"**
- Решение: Убедитесь, что мультиварка в режиме пары (индикатор мигает)
- Решение: Попробуйте стандартный ключ: `[0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]`

**Нет устройств в списке**
- Решение: Проверьте, что Bluetooth включен
- Решение: Убедитесь, что мультиварка включена и в режиме пары
- Решение: Проверьте расстояние до устройства

Подробное руководство по решению проблем: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Поддерживаемые функции

### Программы приготовления
- **Soup** (Суп) - приготовление супов
- **Porridge** (Каша) - варка каш
- **Pilaf** (Плов) - приготовление плова
- **Steam** (На пару) - приготовление на пару
- **Bake** (Выпечка) - выпечка хлеба и выпечки
- **Fry** (Жарка) - жарка продуктов
- **Stew** (Тушение) - тушение блюд
- **Yogurt** (Йогурт) - приготовление йогурта
- **Dough** (Тесто) - подъем теста
- **Keep Warm** (Подогрев) - поддержание температуры

### Управление
- Включение/выключение
- Установка температуры (35-120°C)
- Установка времени приготовления (1-240 минут)
- Таймер отложенного старта
- Контроль текущего состояния
- Статистика использования

## Разработка

### Требования
- Python 3.8+
- HomeAssistant 2023.1+
- bleak 0.20.0+
- bleak-retry-connector 2.0.0+

### Тестирование
```bash
# Запуск тестов
python -m pytest tests/

# Тестирование подключения
python test_connection.py
```

### Вклад в проект
1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/AmazingFeature`
3. Закоммитьте изменения: `git commit -m 'Add some AmazingFeature'`
4. Запушьте: `git push origin feature/AmazingFeature`
5. Создайте Pull Request

## Лицензия

Этот проект лицензирован по MIT License - смотрите файл [LICENSE](LICENSE) для подробностей.

## Благодарности

- [ClusterM/skykettle-ha](https://github.com/ClusterM/skykettle-ha) - за основу архитектуры
- [mavrikkk/ha_kettler](https://github.com/mavrikkk/ha_kettler) - за информацию о протоколах
- Сообщество HomeAssistant за поддержку и feedback

## Контакты

По вопросам и предложениям:
- Создайте [Issue](https://github.com/ClusterM/skycooker-ha/issues)
- Или напишите на почту (указана в профиле)

---

**SkyCooker HA** - делает вашу мультиварку умной и управляемой через HomeAssistant!