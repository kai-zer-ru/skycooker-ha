# SkyCoocker - Интеграция для Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Donate](https://img.shields.io/badge/Donate-❤️-ff69b4.svg)](https://dzen.ru/kai_zer_ru?donate=true)

**Управляйте своей мультиваркой Redmond RMC-M40S через Bluetooth прямо из Home Assistant!**

## 📋 Обзор

Эта интеграция позволяет полностью контролировать вашу мультиварку Redmond RMC-M40S:
- Удаленный запуск и остановка программ
- Мониторинг статуса и температуры в реальном времени
- Выбор режимов готовки
- Отображение оставшегося времени и прогресса

## 🚀 Установка

### 🔧 Требования

- **Home Assistant 2026.6 или новее**
- **Bluetooth адаптер**, поддерживаемый Home Assistant (рекомендуется ESP32 с ESPHome Bluetooth Proxy)
- **Мультиварка Redmond RMC-M40S** с включенным Bluetooth

### 📦 Через HACS (рекомендуется)

1. Убедитесь, что у вас установлен [HACS](https://hacs.xyz/)
2. Добавьте этот репозиторий как пользовательский:
   ```
   https://github.com/kai-zer-ru/skycooker-ha
   ```
3. Найдите "SkyCoocker" в HACS и установите
4. **Перезагрузите Home Assistant**

### 📁 Вручную

1. Скопируйте папку `custom_components/skycooker` в директорию `custom_components` вашего Home Assistant:
   ```bash
   cp -r custom_components/skycooker /config/custom_components/
   ```
2. **Перезагрузите Home Assistant**

### 🔌 Настройка Bluetooth

Для стабильной работы рекомендуется использовать **ESPHome Bluetooth Proxy**:

1. Установите ESPHome добавку в Home Assistant
2. Создайте устройство с конфигурацией:
   ```yaml
   bluetooth_proxy:
     active: true
   ```
3. Разместите прокси рядом с мультиваркой (в пределах 5 метров)

**Важно**: Убедитесь, что Bluetooth интеграция включена в Home Assistant:
- Перейдите в **Настройки → Устройства и службы → Bluetooth**
- Проверьте, что ваш адаптер или прокси отображается

## ⚙️ Настройка

1. **Переведите мультиварку в режим сопряжения**:
   - Выключите мультиварку
   - Нажмите и удерживайте кнопку Bluetooth 5-10 секунд
   - Дождитесь мигания индикатора Bluetooth

2. **Добавьте интеграцию в Home Assistant**:
   - Перейдите в **Настройки → Устройства и службы**
   - Нажмите **Добавить интеграцию**
   - Найдите "SkyCoocker" и выберите его
   - Следуйте инструкциям на экране

3. **Ключ аутентификации**:
   - Используйте стандартный ключ: `0000000000000000` (16 нулей)
   - Этот ключ зашит в прошивке RMC-M40S

## 🎯 Возможности

### 📊 Сенсоры

| Сенсор | Описание | Сущность | Единица измерения | Пример значений |
|--------|-----------|----------|-------------------|-----------------|
| **Статус** | Текущий статус мультиварки | `sensor.skycoocker_status` | - | Выключена, Ожидание, Готовка, Автоподогрев, Разогрев |
| **Температура** | Текущая температура внутри мультиварки | `sensor.skycoocker_temperature` | °C | 25, 90, 100 |
| **Оставшееся время** | Оставшееся время до завершения программы | `sensor.skycoocker_remaining_time` | - | 0 ч. 0 м., 0 ч. 15 м., 1 ч. 30 м. |
| **Общее время** | Общее время выбранной программы | `sensor.skycoocker_total_time` | - | 0 ч. 30 м., 1 ч. 0 м., 1 ч. 30 м. |
| **Время автоподогрева** | Время работы в режиме автоподогрева | `sensor.skycoocker_auto_warm_time` | - | 0 ч. 0 м., 0 ч. 30 м., 1 ч. 0 м. |
| **Процент успеха** | Процент успешных команд (показатель стабильности соединения) | `sensor.skycoocker_success_rate` | % | 0-100 |
| **Время до отложенного старта** | Время до начала отложенного старта | `sensor.skycoocker_delayed_launch_time` | - | 0 ч. 0 м., 0 ч. 30 м., 1 ч. 0 м. |

**Примечание**: Когда устройство выключено или в режиме ожидания, большинство значений сбрасываются на 0 или показывают текущее состояние.

**Дополнительные сенсоры:**
- `sensor.skycoocker_current_mode` - Текущий режим мультиварки (числовой идентификатор)
- `sensor.skycoocker_subprogram` - Текущая подпрограмма (для расширенных режимов)

### ⚡ Переключатели

| Переключатель | Описание | Сущность | Значения |
|-------------|-----------|----------|----------|
| **Автоподогрев** | Включение/выключение режима автоподогрева | `switch.skycoocker_auto_warm` | Вкл/Выкл |

**Примечание**: Режим автоподогрева активируется автоматически после завершения программы приготовления, если он был включен до старта. Это позволяет сохранить блюдо теплым до момента подачи.

### 🎚️ Выбор

| Выбор | Описание | Сущность | Диапазон значений |
|--------|-----------|----------|-------------------|
| **Режим** | Выбор режима готовки | `select.skycoocker_mode` | Мультиповар, Молочная каша, Тушение, Жарка, Суп, На пару, Паста, Томление, Варка, Выпечка, Рис/крупы, Плов, Йогурт, Пицца, Хлеб, Вакуум, Ожидание |
| **Температура** | Ручная настройка температуры | `select.skycoocker_temperature` | 40-200°C (шаг 5°C) |
| **Время приготовления (часы)** | Настройка часов приготовления | `select.skycoocker_cooking_time_hours` | 0-23 часа |
| **Время приготовления (минуты)** | Настройка минут приготовления | `select.skycoocker_cooking_time_minutes` | 0-59 минут |
| **Время отложенного старта (часы)** | Настройка часов отложенного старта | `select.skycoocker_delayed_start_hours` | 0-23 часа |
| **Время отложенного старта (минуты)** | Настройка минут отложенного старта | `select.skycoocker_delayed_start_minutes` | 0-59 минут |

**Автоматическое обновление времени приготовления**: При выборе режима время приготовления автоматически обновляется в соответствии с рекомендуемыми значениями для выбранного режима, если пользователь не установил свои собственные значения.

**Доступные режимы для RMC-M40S/M42S:**
- Мультиповар (Multi-chef) - универсальный режим
- Молочная каша (Milk porridge) - идеально для каш
- Тушение (Stewing) - для мясных блюд
- Жарка (Frying) - для обжаривания
- Суп (Soup) - для супов и бульонов
- На пару (Steam) - здоровое приготовление
- Паста (Pasta) - для макаронных изделий
- Томление (Languor) - медленное приготовление
- Варка (Cooking) - для варки овощей и др.
- Выпечка (Baking) - для выпечки
- Рис/крупы (Rice/Cereals) - для круп
- Плов (Pilaf) - традиционный плов
- Йогурт (Yogurt) - для приготовления йогурта
- Пицца (Pizza) - для пиццы
- Хлеб (Bread) - для выпечки хлеба
- Вакуум (Sous-vide) - вакуумное приготовление

### 🔘 Кнопки

| Кнопка | Описание | Сущность |
|--------|-----------|----------|
| **Старт** | Старт выбранной программы с текущими настройками | `button.skycoocker_start` |
| **Стоп** | Остановка текущей программы и сброс всех настроек | `button.skycoocker_stop` |
| **Отложенный старт** | Старт программы с заданным временем отложенного старта | `button.skycoocker_start_delayed` |

**Примечание**: Кнопка "Стоп" сбрасывает все пользовательские настройки (температуру, время приготовления, отложенный старт) к значениям по умолчанию.

## 📱 Пример автоматизации

```yaml
# Автоматический запуск утром
alias: "Утренняя каша"
trigger:
  - platform: time
    at: "07:00:00"
action:
  - service: select.select_option
    target:
      entity_id: select.skycoocker_mode
    data:
      option: "Молочная каша"
  - service: button.press
    target:
      entity_id: button.skycoocker_start

# Уведомление о завершении готовки
alias: "Готовка завершена"
trigger:
  - platform: state
    entity_id: sensor.skycoocker_status
    to: "Автоподогрев"
action:
  - service: notify.mobile_app
    data:
      message: "Готовка завершена! Вкусной каши! 🍲"
```

## 🔧 Устранение неполадок

### 🚨 Проблемы с подключением

**Симптом**: Устройство не находится или не подключается

**Решение**:
1. Убедитесь, что мультиварка в режиме сопряжения (мигает индикатор Bluetooth)
2. Проверьте, что Bluetooth адаптер работает и обнаружен Home Assistant
3. Разместите мультиварку ближе к адаптеру (в пределах 1-2 метров)
4. Перезагрузите Bluetooth адаптер:
   ```bash
   sudo systemctl restart bluetooth
   ```

### ❌ Ошибка аутентификации

**Симптом**: `ATT error 0x0e` или `Ошибка аутентификации`

**Решение**:
1. Убедитесь, что используется правильный ключ: `0000000000000000`
2. Переведите мультиварку в режим сопряжения
3. Проверьте, что нет других активных подключений к устройству
4. Перезагрузите мультиварку

### ⏱️ Время приготовления не обновляется

**Симптом**: При смене режима время приготовления остается прежним

**Решение**:
1. Проверьте, что вы не установили пользовательские значения времени вручную
2. Если вы хотите сбросить к автоматическим значениям, установите время на 0 часов и 10 минут
3. Переключите режим - время должно обновиться автоматически
4. Если проблема сохраняется, перезагрузите интеграцию или Home Assistant

**Примечание**: Это ожидаемое поведение - интеграция сохраняет пользовательские настройки времени приготовления.

### ⏱️ Зависание при подключении

**Симптом**: Подключение занимает слишком много времени

**Решение**:
1. Проверьте, что Bluetooth адаптер не перегружен
2. Уменьшите количество активных Bluetooth устройств
3. Используйте выделенный Bluetooth прокси
4. Проверьте логи на наличие таймаутов

## 🔍 Особенности и поведение

### Автоматическое обновление времени приготовления

При выборе режима готовки время приготовления автоматически обновляется в соответствии с рекомендуемыми значениями для выбранного режима. Однако, если пользователь вручную установил собственные значения времени приготовления, они будут сохранены и не будут перезаписаны при смене режима.

**Примеры:**
- Если время приготовления имеет значения по умолчанию (0 часов, 10 минут) и вы выбираете режим "На пару", время автоматически обновится до значений из режима (0 часов, 25 минут)
- Если вы вручную установили время приготовления (2 часа, 30 минут) и затем выбираете другой режим, ваши пользовательские значения будут сохранены

### Сохранение пользовательских настроек

Интеграция уважает выбор пользователя и сохраняет следующие настройки:
- Пользовательские значения температуры
- Пользовательские значения времени приготовления
- Настройки отложенного старта
- Состояние автоподогрева

### Сброс к значениям по умолчанию

При нажатии кнопки "Стоп" все пользовательские настройки сбрасываются к значениям по умолчанию:
- Температура: сбрасывается
- Время приготовления: 0 часов, 10 минут
- Отложенный старт: 0 часов, 0 минут
- Автоподогрев: включен

## 📊 Поддерживаемые модели

| Модель | Поддержка | Примечания |
|--------|-----------|------------|
| **Redmond RMC-M40S** | ✅ Полная | Основная поддерживаемая модель |
| **Redmond RMC-M42S** | ✅ Полная | Аналогична RMC-M40S |
| Другие модели | ❌ Нет | Может работать с ограниченным функционалом |

## 📝 Логирование

Интеграция предоставляет обширное логирование с использованием иконок:

- 📊 - Информация о статусе
- 📤 - Отправка команд
- 📥 - Получение данных
- ✅ - Успешные операции
- ❌ - Ошибки
- ⚠️ - Предупреждения
- 🔍 - Поиск устройств
- 🔌 - Подключение

**Включение отладочного логирования**:

Добавьте в `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.skycooker: debug
```

## 🎨 Пример карточки для Lovelace

### Полноценный пример с card-mod (полный view)

![Пример карточки для Lovelace](.images/image1.png)

```yaml
views:
  - title: Кухня
    cards:
      - type: vertical-stack
        cards:
          # Основная карточка с информацией
          - type: entities
            title: Мультиварка Redmond RMC-M40S
            show_header_toggle: false
            entities:
              - entity: switch.skycoocker_auto_warm
                name: Автоподогрев
                icon: mdi:heat-wave
              - entity: sensor.skycoocker_status
                name: Статус
                icon: mdi:information
              - entity: sensor.skycoocker_temperature
                name: Температура
                icon: mdi:thermometer
              - entity: sensor.skycoocker_remaining_time
                name: Оставшееся время
                icon: mdi:timer
            card_mod:
              style: |
                ha-card {
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  border-radius: 20px;
                  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }
                .card-header {
                  color: white;
                  font-weight: bold;
                  font-size: 1.2em;
                }
                .card-content {
                  padding: 16px;
                }
                .entity {
                  color: white;
                  margin: 8px 0;
                }
                .name {
                  font-weight: 500;
                }
                .state {
                  font-weight: 300;
                }

          # Карточка управления
          - type: horizontal-stack
            cards:
              - type: button
                tap_action:
                  action: call-service
                  service: select.select_option
                  target:
                    entity_id: select.skycoocker_mode
                  data:
                    option: "Молочная каша"
                name: Каша
                icon: mdi:bowl-mix
                card_mod:
                  style: |
                    ha-card {
                      background: rgba(255,255,255,0.2);
                      color: white;
                      border-radius: 15px;
                      padding: 12px;
                      transition: all 0.3s;
                    }
                    ha-card:hover {
                      background: rgba(255,255,255,0.3);
                      transform: scale(1.05);
                    }

              - type: button
                tap_action:
                  action: call-service
                  service: select.select_option
                  target:
                    entity_id: select.skycoocker_mode
                  data:
                    option: "Суп"
                name: Суп
                icon: mdi:pot-mix
                card_mod:
                  style: |
                    ha-card {
                      background: rgba(255,255,255,0.2);
                      color: white;
                      border-radius: 15px;
                      padding: 12px;
                      transition: all 0.3s;
                    }
                    ha-card:hover {
                      background: rgba(255,255,255,0.3);
                      transform: scale(1.05);
                    }

              - type: button
                tap_action:
                  action: call-service
                  service: select.select_option
                  target:
                    entity_id: select.skycoocker_mode
                  data:
                    option: "Тушение"
                name: Тушение
                icon: mdi:pot-steam
                card_mod:
                  style: |
                    ha-card {
                      background: rgba(255,255,255,0.2);
                      color: white;
                      border-radius: 15px;
                      padding: 12px;
                      transition: all 0.3s;
                    }
                    ha-card:hover {
                      background: rgba(255,255,255,0.3);
                      transform: scale(1.05);
                    }

          # Карточка управления
          - type: horizontal-stack
            cards:
              - type: button
                tap_action:
                  action: call-service
                  service: button.press
                  target:
                    entity_id: button.skycoocker_start
                name: Старт
                icon: mdi:play
                card_mod:
                  style: |
                    ha-card {
                      background: #4CAF50;
                      color: white;
                      border-radius: 15px;
                      padding: 12px;
                      transition: all 0.3s;
                    }
                    ha-card:hover {
                      background: #45a049;
                      transform: scale(1.05);
                    }

              - type: button
                tap_action:
                  action: call-service
                  service: button.press
                  target:
                    entity_id: button.skycoocker_stop
                name: Стоп
                icon: mdi:stop
                card_mod:
                  style: |
                    ha-card {
                      background: #f44336;
                      color: white;
                      border-radius: 15px;
                      padding: 12px;
                      transition: all 0.3s;
                    }
                    ha-card:hover {
                      background: #d32f2f;
                      transform: scale(1.05);
                    }

          # Карточка с выбором режима
          - type: entities
            title: Режимы готовки
            show_header_toggle: false
            entities:
              - entity: select.skycoocker_mode
                name: Выбор режима
                icon: mdi:tune
            card_mod:
              style: |
                ha-card {
                  background: rgba(255,255,255,0.1);
                  border-radius: 15px;
                  backdrop-filter: blur(10px);
                }
                .card-header {
                  color: white;
                  font-weight: bold;
                }
                .card-content {
                  padding: 16px;
                }
                .entity {
                  color: white;
                }
```

### Простая карточка для вставки в существующий view

![Простая карточка для вставки](.images/image2.png)

```yaml
- type: vertical-stack
  cards:
    # Основная информация
    - type: entities
      title: Мультиварка
      show_header_toggle: false
      entities:
        - entity: switch.skycoocker_auto_warm
          name: Автоподогрев
          icon: mdi:heat-wave
        - entity: sensor.skycoocker_status
          name: Статус
          icon: mdi:information
        - entity: sensor.skycoocker_temperature
          name: Температура
          icon: mdi:thermometer
        - entity: sensor.skycoocker_remaining_time
          name: Оставшееся время
          icon: mdi:timer

    # Быстрые кнопки управления
    - type: horizontal-stack
      cards:
        - type: button
          tap_action:
            action: call-service
            service: button.press
            target:
              entity_id: button.skycoocker_start
          name: Старт
          icon: mdi:play
          show_name: false
          show_icon: true

        - type: button
          tap_action:
            action: call-service
            service: button.press
            target:
              entity_id: button.skycoocker_stop
          name: Стоп
          icon: mdi:stop
          show_name: false
          show_icon: true

        - type: button
          tap_action:
            action: more-info
            target: {}
          entity: select.skycoocker_mode
          name: Режим
          icon: mdi:tune
          show_name: false
          show_icon: true
```

### Карточка с custom:button-card

![Карточка с custom:button-card](.images/image3.png)

```yaml
- type: custom:button-card
  entity: select.skycoocker_mode
  name: Мультиварка
  icon: mdi:pot-mix
  styles:
    card:
      - width: 300px
      - height: 200px
    grid:
      - grid-template-areas: '"i n" "i s"'
      - grid-template-columns: 1fr 1fr
  custom_fields:
    buttons:
      card:
        type: custom:button-card
        entity: script.start_multicooker_milk_porridge
        name: Молочная каша
        icon: mdi:bowl-mix
        styles:
          card:
            - width: 100px
            - height: 100px
```

### Минимальная карточка (без card-mod)

```yaml
- type: entities
  title: Мультиварка
  entities:
    - switch.skycoocker_auto_warm
    - sensor.skycoocker_status
    - sensor.skycoocker_temperature
    - sensor.skycoocker_remaining_time
    - select.skycoocker_mode
    - button.skycoocker_start
    - button.skycoocker_stop
```

### Советы по настройке

1. **Установите card-mod**:
   ```bash
   hacs install card-mod
   ```

2. **Добавьте ресурс**:
   ```yaml
   resources:
     - url: /hacsfiles/lovelace-card-mod/card-mod.js
       type: module
   ```

3. **Настройте тему**: Для лучшего отображения используйте темную тему или настройте цвета под ваш интерьер.

## 🤖 Примеры интеграции

### Скрипты для быстрого запуска

Создайте скрипты для часто используемых режимов:

```yaml
# configuration.yaml
script:
  # Запуск в режиме "Молочная каша"
  start_milk_porridge:
    alias: "Молочная каша"
    icon: mdi:bowl-mix
    sequence:
      - service: select.select_option
        target:
          entity_id: select.skycoocker_mode
        data:
          option: "Молочная каша"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycoocker_start

  # Запуск в режиме "Суп"
  start_soup:
    alias: "Суп"
    icon: mdi:pot-mix
    sequence:
      - service: select.select_option
        target:
          entity_id: select.skycoocker_mode
        data:
          option: "Суп"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycoocker_start

  # Запуск в режиме "Тушение"
  start_stew:
    alias: "Тушение"
    icon: mdi:pot-steam
    sequence:
      - service: select.select_option
        target:
          entity_id: select.skycoocker_mode
        data:
          option: "Тушение"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycoocker_start
```

### Автоматизации

Примеры автоматизаций для удобного управления:

```yaml
# Автоматический запуск по расписанию
alias: "Утренняя каша в будни"
trigger:
  - platform: time
    at: "07:00:00"
  - platform: state
    entity_id: binary_sensor.workday_sensor
    to: "on"
action:
  - service: script.start_milk_porridge
  - service: notify.mobile_app
    data:
      message: "Мультиварка запущена в режиме Молочная каша 🍲"

# Уведомление о завершении готовки
alias: "Готовка завершена"
trigger:
  - platform: state
    entity_id: sensor.skycoocker_status
    to: "Автоподогрев"
action:
  - service: notify.mobile_app
    data:
      message: "Готовка завершена! Вкусной каши! 🍲"
      title: "Мультиварка"

# Автоматическое выключение при отсутствии дома
alias: "Выключить мультиварку если никого нет дома"
trigger:
  - platform: state
    entity_id: person.all
    to: "not_home"
    for: "00:30:00"
condition:
  - condition: state
    entity_id: sensor.skycoocker_status
    state: "Готовка"
action:
  - service: button.press
    target:
      entity_id: button.skycoocker_stop
  - service: notify.mobile_app
    data:
      message: "Мультиварка выключена, так как никого нет дома"
      title: "Безопасность"
```

### Шаблонные сенсоры

Создайте объединенный сенсор для отображения полного статуса:

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Мультиварка - Полный статус"
        state: >-
          {% if is_state('sensor.skycoocker_status', 'Готовка') or
                is_state('sensor.skycoocker_status', 'Автоподогрев') or
                is_state('sensor.skycoocker_status', 'Разогрев') %}
            Работает: {{ states('sensor.skycoocker_status') }},
            Температура: {{ states('sensor.skycoocker_temperature') }}°C,
            Осталось: {{ states('sensor.skycoocker_remaining_time') }} мин
          {% else %}
            Ожидает
          {% endif %}
        icon: mdi:pot-mix
```

### Быстрый выбор режима с input_select

```yaml
# configuration.yaml
input_select:
  multicooker_preset:
    name: "Быстрый выбор режима"
    options:
      - "Молочная каша"
      - "Суп"
      - "Тушение"
      - "Выпечка"
    initial: "Молочная каша"

automation:
  - alias: "Запуск мультиварки по выбору"
    trigger:
      platform: state
      entity_id: input_select.multicooker_preset
    action:
      - service: select.select_option
        target:
          entity_id: select.skycoocker_mode
        data:
          option: "{{ trigger.to_state.state }}"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycoocker_start
```

### Автоматическое обновление времени приготовления

Пример автоматизации, демонстрирующий новое поведение автоматического обновления времени:

```yaml
# Автоматическое обновление времени при смене режима
alias: "Уведомление о времени приготовления"
trigger:
  platform: state
  entity_id: select.skycoocker_mode
action:
  - service: notify.mobile_app
    data:
      message: >
        Режим изменен на {{ states('select.skycoocker_mode') }}.
        Время приготовления: {{ states('sensor.skycoocker_total_time') }} минут.
        Температура: {{ states('sensor.skycoocker_temperature') }}°C.
      title: "Мультиварка - режим изменен"
```

### Сохранение пользовательских настроек

Пример, показывающий как сохранить пользовательские настройки времени:

```yaml
# Сохранение пользовательских настроек времени
alias: "Сохранить пользовательское время приготовления"
trigger:
  - platform: state
    entity_id: select.skycoocker_cooking_time_hours
  - platform: state
    entity_id: select.skycoocker_cooking_time_minutes
action:
  - service: notify.mobile_app
    data:
      message: >
        Пользователь установил время:
        {{ states('select.skycoocker_cooking_time_hours') }} часов
        {{ states('select.skycoocker_cooking_time_minutes') }} минут
      title: "Пользовательские настройки"
```

### Интеграция с Yandex.Intents

Для голосового управления через Яндекс Станцию:

```yaml
# configuration.yaml
yandex_intents:
  - intent: "Запустить мультиварку в режиме {режим}"
    action:
      - service: select.select_option
        target:
          entity_id: select.skycoocker_mode
        data:
          option: "{{ режим }}"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycoocker_start
      - service: notify.mobile_app
        data:
          message: "Мультиварка запущена в режиме {{ режим }}"
          title: "Мультиварка"

  - intent: "Выключить мультиварку"
    action:
      - service: button.press
        target:
          entity_id: button.skycoocker_stop
      - service: notify.mobile_app
        data:
          message: "Мультиварка выключена"
          title: "Мультиварка"

  - intent: "Какой статус мультиварки"
    action:
      - service: notify.mobile_app
        data:
          message: >
            {% if is_state('sensor.skycoocker_status', 'Готовка') or
                  is_state('sensor.skycoocker_status', 'Автоподогрев') or
                  is_state('sensor.skycoocker_status', 'Разогрев') %}
              Мультиварка работает. Статус: {{ states('sensor.skycoocker_status') }}.
              Температура: {{ states('sensor.skycoocker_temperature') }}°C.
              Осталось: {{ states('sensor.skycoocker_remaining_time') }} минут.
            {% else %}
              Мультиварка ожидает.
            {% endif %}
          title: "Статус мультиварки"
```

**Примечание**: Для работы Yandex.Intents требуется установленная интеграция [ha-yandex-station-intents](https://github.com/dext0r/ha-yandex-station-intents).



## 🤝 Поддержка

Если у вас есть вопросы или проблемы:

1. **Проверьте логи**: `journalctl -u home-assistant -f`
2. **Создайте issue**: [GitHub Issues](https://github.com/kai-zer-ru/skycooker-ha/issues)
3. **Предоставьте информацию**:
   - Версия Home Assistant
   - Модель мультиварки
   - Логи с ошибками
   - Шаги для воспроизведения

## 💰 Пожертвования

Если вам нравится эта интеграция и вы хотите поддержать разработку:

[![Donate](https://img.shields.io/badge/Donate-❤️-ff69b4.svg)](https://dzen.ru/kai_zer_ru?donate=true)

**Спасибо за поддержку!** ❤️

## 🙏 Благодарности

- [ESPHome-Ready4Sky](https://github.com/KomX/ESPHome-Ready4Sky) - за протокол R4S
- [ha_kettler](https://github.com/mavrikkk/ha_kettler) - за архитектуру интеграции
- [skykettle-ha](https://github.com/ClusterM/skykettle-ha) - за вдохновение
- [Bleak](https://github.com/hbldh/bleak) - за кросс-платформенный Bluetooth



## 📋 История изменений

### Последнее обновление (2026-01-11)

**Исправления:**
- ✅ Исправлено автоматическое обновление времени приготовления при смене режима
- ✅ Добавлена логика сохранения пользовательских значений времени приготовления
- ✅ Улучшена обработка стандартных значений (0 часов, 10 минут)

**Новые возможности:**
- ✅ Автоматическое обновление времени приготовления из MODE_DATA при выборе режима
- ✅ Сохранение пользовательских значений при смене режима
- ✅ Улучшенная логика определения стандартных vs пользовательских значений

### Предыдущие обновления

- ✅ Полная поддержка RMC-M40S и RMC-M42S
- ✅ Стабильное Bluetooth соединение
- ✅ Подробное логирование с иконками
- ✅ Интеграция с Lovelace карточками
- ✅ Голосовое управление через Yandex.Intents

## 🔮 Планы на будущее

- 🔜 Поддержка других моделей Redmond (RMC-M92S, RMC-M222S и др.)
- 🔜 Улучшенная обработка ошибок и восстановление соединения
- 🔜 Дополнительные режимы и настройки (подпрограммы, расширенные параметры)
- 🔜 Интеграция с рецептами и кулинарными сервисами
- 🔜 Улучшенный интерфейс управления с визуализацией процессов

**Следите за обновлениями!** 🚀

## 📜 Лицензия

Этот проект лицензирован по лицензии MIT. См. файл [LICENSE](LICENSE) для подробностей.