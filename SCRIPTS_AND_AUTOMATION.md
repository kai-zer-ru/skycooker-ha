# 🤖 Примеры интеграции

Этот документ содержит примеры скриптов, автоматизаций и других интеграций для работы с мультиваркой Redmond RMC-M40S через SkyCooker.

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
      entity_id: select.skycooker_mode
    data:
      option: "Молочная каша"
  - service: button.press
    target:
      entity_id: button.skycooker_start

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
      - service: select.select_option
        target:
          entity_id: select.skycooker_mode
        data:
          option: "Молочная каша"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycooker_start

  # Запуск в программе "Суп"
  start_soup:
    alias: "Суп"
    icon: mdi:pot-mix
    sequence:
      - service: select.select_option
        target:
          entity_id: select.skycooker_mode
        data:
          option: "Суп"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycooker_start

  # Запуск в программе "Тушение"
  start_stew:
    alias: "Тушение"
    icon: mdi:pot-steam
    sequence:
      - service: select.select_option
        target:
          entity_id: select.skycooker_mode
        data:
          option: "Тушение"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycooker_start
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

Для голосового управления через Яндекс Станцию:

```yaml
# configuration.yaml
yandex_intents:
  - intent: "Запустить мультиварку в программе {программа}"
    action:
      - service: select.select_option
        target:
          entity_id: select.skycooker_mode
        data:
          option: "{{ программа }}"
      - delay: 1
      - service: button.press
        target:
          entity_id: button.skycooker_start
      - service: notify.mobile_app
        data:
          message: "Мультиварка запущена в программе {{ программа }}"
          title: "Мультиварка"

  - intent: "Выключить мультиварку"
    action:
      - service: button.press
        target:
          entity_id: button.skycooker_stop
      - service: notify.mobile_app
        data:
          message: "Мультиварка выключена"
          title: "Мультиварка"

  - intent: "Какой статус мультиварки"
    action:
      - service: notify.mobile_app
        data:
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
          title: "Статус мультиварки"
```

**Примечание**: Для работы Yandex.Intents требуется установленная интеграция [ha-yandex-station-intents](https://github.com/dext0r/ha-yandex-station-intents).