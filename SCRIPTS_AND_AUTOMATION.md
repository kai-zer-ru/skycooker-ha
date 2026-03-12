# 🤖 Примеры интеграции

Этот документ содержит примеры скриптов, автоматизаций и других интеграций для работы с мультиваркой Redmond RMC-M40S через SkyCooker.

## 🔗 Содержание

- [📱 Пример автоматизации (новые сервисы)](#-пример-автоматизации-новые-сервисы)
- [🤖 Примеры интеграции](#-примеры-интеграции)
- [Шаблонные сенсоры](#-шаблонные-сенсоры)
- [Быстрый выбор программы с input_select](#-быстрый-выбор-программы-с-input_select)
- [Автоматическое обновление времени приготовления](#-автоматическое-обновление-времени-приготовления)
- [Сохранение пользовательских настроек](#-сохранение-пользовательских-настроек)
- [Интеграция с Yandex.Intents](#-интеграция-с-yandexintents)
- [Передача мультиварки в Умный дом Яндекса](#-передача-мультиварки-в-умный-дом-яндекса)

## 📱 Пример автоматизации (новые сервисы)

```yaml
# Автоматический запуск утром (режим "Молочная каша")
alias: "Утренняя каша"
mode: single

trigger:
  - platform: time
    at: "07:00:00"

action:
  - service: skycooker.set_program
    data:
      # Укажи свой config_entry_id из настроек интеграции SkyCooker
      config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
      program_name: "Молочная каша"
  - service: skycooker.start_cooking
    data:
      config_entry_id: YOUR_SKYCOOKER_ENTRY_ID

# Уведомление о завершении готовки
alias: "Готовка завершена"
mode: single

trigger:
  - platform: state
    entity_id: sensor.skycooker_status
    to: "Автоподогрев"

action:
  - service: notify.mobile_app
    data:
      message: "Готовка завершена! Вкусной каши! 🍲"
```

## 🤖 Примеры интеграции

### Скрипты для быстрого запуска

Создайте скрипты для часто используемых программ:

```yaml
# configuration.yaml
script:
  # Запуск в программе "Молочная каша"
  start_milk_porridge:
    alias: "Молочная каша"
    icon: mdi:bowl-mix
    sequence:
      - service: skycooker.set_program
        data:
          config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
          program_name: "Молочная каша"
      - service: skycooker.start_cooking
        data:
          config_entry_id: YOUR_SKYCOOKER_ENTRY_ID

  # Запуск в программе "Суп"
  start_soup:
    alias: "Суп"
    icon: mdi:pot-mix
    sequence:
      - service: skycooker.set_program
        data:
          config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
          program_name: "Суп"
      - service: skycooker.start_cooking
        data:
          config_entry_id: YOUR_SKYCOOKER_ENTRY_ID

  # Запуск в программе "Тушение"
  start_stew:
    alias: "Тушение"
    icon: mdi:pot-steam
    sequence:
      - service: skycooker.set_program
        data:
          config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
          program_name: "Тушение"
      - service: skycooker.start_cooking
        data:
          config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
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
      message: "Мультиварка запущена в программе Молочная каша 🍲"

# Уведомление о завершении готовки
alias: "Готовка завершена"
trigger:
  - platform: state
    entity_id: sensor.skycooker_status
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
    entity_id: sensor.skycooker_status
    state: "Готовка"
action:
  - service: button.press
    target:
      entity_id: button.skycooker_stop
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
          {% if is_state('sensor.skycooker_status', 'Готовка') or
                is_state('sensor.skycooker_status', 'Автоподогрев') or
                is_state('sensor.skycooker_status', 'Разогрев') %}
            Работает: {{ states('sensor.skycooker_status') }},
            Температура: {{ states('sensor.skycooker_temperature') }}°C,
            Осталось: {{ states('sensor.skycooker_remaining_time') }} мин
          {% else %}
            Ожидает
          {% endif %}
        icon: mdi:pot-mix
```

### Быстрый выбор программы с input_select

```yaml
# configuration.yaml
input_select:
  multicooker_preset:
    name: "Быстрый выбор программы"
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
          entity_id: select.skycooker_mode
        data:
          option: "{{ trigger.to_state.state }}"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycooker_start
```

### Автоматическое обновление времени приготовления

Пример автоматизации, демонстрирующий новое поведение автоматического обновления времени:

```yaml
# Автоматическое обновление времени при смене программы
alias: "Уведомление о времени приготовления"
trigger:
  platform: state
  entity_id: select.skycooker_mode
action:
  - service: notify.mobile_app
    data:
      message: >
        Программа изменена на {{ states('select.skycooker_mode') }}.
        Время приготовления: {{ states('sensor.skycooker_cooking_time') }} минут.
        Температура: {{ states('sensor.skycooker_temperature') }}°C.
      title: "Мультиварка - программа изменена"
```

### Сохранение пользовательских настроек

Пример, показывающий как сохранить пользовательские настройки времени:

```yaml
# Сохранение пользовательских настроек времени
alias: "Сохранить пользовательское время приготовления"
trigger:
  - platform: state
    entity_id: select.skycooker_cooking_time_hours
  - platform: state
    entity_id: select.skycooker_cooking_time_minutes
action:
  - service: notify.mobile_app
    data:
      message: >
        Пользователь установил время:
        {{ states('select.skycooker_cooking_time_hours') }} часов
        {{ states('select.skycooker_cooking_time_minutes') }} минут
      title: "Пользовательские настройки"
```

### Интеграция с Yandex.Intents

Для голосового управления через Яндекс Станцию удобнее использовать **автоматизации с триггером события `yandex_intent`**.

Ниже несколько примеров.

#### Запуск мультиварки в нужной программе по фразе

```yaml
alias: "Запусти мультиварку в программе На пару"
mode: single

trigger:
  - platform: event
    event_type: yandex_intent
    event_data: Запусти мультиварку на пару

condition: []

action:
  - service: skycooker.set_program
    data:
      config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
      program_name: "На пару"
  - service: skycooker.start_cooking
    data:
      config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
```

#### Пример «Свари позы» (пароварка с кастомным временем)

```yaml
alias: "Свари позы (Пароварка)"
mode: single

trigger:
  - platform: event
    event_type: yandex_intent
    event_data: Свари позы

condition: []

action:
  - service: skycooker.set_program
    data:
      config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
      program_name: "На пару"
      temperature: 100
      main_hours: 0
      main_minutes: 35

  - service: skycooker.start_cooking
    data:
      config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
```

#### Выключить мультиварку голосом

```yaml
alias: "Выключить мультиварку (Яндекс)"
mode: single

trigger:
  - platform: event
    event_type: yandex_intent
    event_data: Выключи мультиварку

condition: []

action:
  - service: skycooker.stop_cooking
    data:
      config_entry_id: YOUR_SKYCOOKER_ENTRY_ID
```

#### Узнать статус мультиварки голосом

```yaml
alias: "Статус мультиварки (Яндекс)"
mode: single

trigger:
  - platform: event
    event_type: yandex_intent
    event_data: Какой статус мультиварки

condition: []

action:
  - service: notify.mobile_app
    data:
      title: "Статус мультиварки"
      message: >
        {% if is_state('sensor.skycooker_status', 'Готовка') or
              is_state('sensor.skycooker_status', 'Автоподогрев') or
              is_state('sensor.skycooker_status', 'Разогрев') %}
          Мультиварка работает. Статус: {{ states('sensor.skycooker_status') }}.
          Температура: {{ states('sensor.skycooker_temperature') }}°C.
          Осталось: {{ states('sensor.skycooker_remaining_time') }} минут.
        {% else %}
          Мультиварка ожидает.
        {% endif %}
```

**Примечание**: Для работы Yandex.Intents требуется установленная интеграция [ha-yandex-station-intents](https://github.com/dext0r/ha-yandex-station-intents).

### Передача мультиварки в Умный дом Яндекса

Для экспорта мультиварки в платформу «Умный дом Яндекса» можно использовать интеграцию [`yandex_smart_home`](https://github.com/dext0r/yandex_smart_home).
Ниже пример конфигурации, которая отдаёт мультиварку как `cooking.multicooker` с управлением программой, температурой и автоподогревом:

```yaml
yandex_smart_home:
  entity_config:
    switch.skycooker_rmc_m40s_auto_warm:
      name: Мультиварка
      room: Кухня
      type: cooking.multicooker
      state_template: >
        {{ 'on' if is_state('binary_sensor.skycooker_rmc_m40s_cooking_active', 'on') else 'off' }}
      turn_on:
        action: script.zapusk_multivarki
      turn_off:
        action: script.otkliuchenie_multivarki
      properties:
        - type: temperature
          entity: sensor.skycooker_rmc_m40s_temperature
      custom_toggles:
        keep_warm:
          state_entity_id: switch.skycooker_rmc_m40s_auto_warm
          turn_on:
            service: switch.turn_on
            entity_id: switch.skycooker_rmc_m40s_auto_warm
          turn_off:
            service: switch.turn_off
            entity_id: switch.skycooker_rmc_m40s_auto_warm
      modes:
        program:
          multicooker: "Мультиповар"
          milk_porridge: "Молочная каша"
          stewing: "Тушение"
          frying: "Жарка"
          soup: "Суп"
          steam: "На пару"
          pasta: "Паста/Макароны"
          slow_cook: "Томление"
          boiling: "Варка"
          baking: "Выпечка"
          cereals: "Рис/Крупы"
          pilaf: "Плов"
          yogurt: "Йогурт"
          pizza: "Пицца"
          bread: "Хлеб"
          vacuum: "Вакуум"
      custom_modes:
        program:
          state_entity_id: select.skycooker_rmc_m40s_program
          set_mode:
            service: select.select_option
            entity_id: select.skycooker_rmc_m40s_program
            data:
              option: "{{ mode }}"
      custom_ranges:
        temperature:
          state_entity_id: select.skycooker_rmc_m40s_temperature
          set_value:
            service: select.select_option
            entity_id: select.skycooker_rmc_m40s_temperature
            data:
              option: "{{ value | int }}"
          range:
            min: 40
            max: 200
            precision: 5
```

⚠️ Важно: на данный момент платформа «Умный дом Яндекса» **не поддерживает управление временем приготовления мультиварки** (часы/минуты) через тип `cooking.multicooker`. Как только такая поддержка появится со стороны УДЯ, конфигурация будет расширена примерами `custom_ranges` для времени.