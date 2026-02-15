# House Mode with HA Governance

## Required helpers

```yaml
input_select:
  house_mode:
    name: House Mode
    options:
      - Home Day
      - Home Night
      - Away
      - Vacation
    initial: Home Day

input_boolean:
  haus_modus_manuell:
    name: Manual House Mode Override
    initial: off

input_boolean:
  nachtmodus:
    name: Night Mode
    initial: off

input_datetime:
  abwesend_seit:
    name: Away Since
    has_date: true
    has_time: true

input_number:
  urlaub_schwelle:
    name: Vacation Threshold (hours)
    min: 1
    max: 240
    step: 1
    initial: 24
```

## Template sensors

```yaml
template:
  - sensor:
      - name: house_away_duration
        unit_of_measurement: "h"
        state: >
          {% if states('input_datetime.abwesend_seit') not in ['unknown', 'unavailable'] %}
            {{ ((as_timestamp(now()) - as_timestamp(states('input_datetime.abwesend_seit'))) / 3600) | round(1) }}
          {% else %}
            0
          {% endif %}

  - sensor:
      - name: house_occupancy_count
        state: >
          {{ states.person
             | selectattr('state','eq','home')
             | list
             | count }}
```

## Presence aggregation

```yaml
template:
  - binary_sensor:
      - name: anyone_home
        state: >
          {{ states('sensor.house_occupancy_count') | int(0) > 0 }}

  - binary_sensor:
      - name: everyone_away
        state: >
          {{ states('sensor.house_occupancy_count') | int(0) == 0 }}
```

## Optional presence status sensors

```text
sensor.person_sascha_presence_status
sensor.person_lena_presence_status
```

with states such as:

```text
home
just_arrived
just_left
away
```

## Example dashboard

```yaml
type: entities
title: 🏠 House Status
entities:
  - input_select.house_mode
  - binary_sensor.anyone_home
  - sensor.house_occupancy_count
  - sensor.house_away_duration
```

## Migration notes

If you previously used automations for House Mode:

- Remove or disable them
- Let Governance handle transitions
- Avoid mixed logic

Governance should be the single source of truth for House Mode.
