# HA Governance Policy Examples

## House mode policies

```yaml
policies:
  - name: house_mode_day_to_night
    priority: 90
    when:
      input_select.house_mode: "Home Day"
      input_boolean.nachtmodus: "on"
      binary_sensor.everyone_away: "off"
    enforce:
      service: input_select.select_option
      target:
        entity_id: input_select.house_mode
      data:
        option: "Home Night"

  - name: house_mode_night_to_day
    priority: 90
    when:
      input_select.house_mode: "Home Night"
      input_boolean.nachtmodus: "off"
      binary_sensor.everyone_away: "off"
    enforce:
      service: input_select.select_option
      target:
        entity_id: input_select.house_mode
      data:
        option: "Home Day"

  - name: house_mode_home_to_away
    priority: 95
    when:
      input_select.house_mode: "Home Day"
      binary_sensor.everyone_away: "on"
      input_boolean.haus_modus_manuell: "off"
    enforce:
      service: input_select.select_option
      target:
        entity_id: input_select.house_mode
      data:
        option: "Away"

  - name: house_mode_away_to_home
    priority: 95
    when:
      input_select.house_mode: "Away"
      binary_sensor.anyone_home: "on"
    enforce:
      service: input_select.select_option
      target:
        entity_id: input_select.house_mode
      data:
        option: "Home Day"

  - name: house_mode_away_to_vacation
    priority: 98
    when:
      input_select.house_mode: "Away"
      sensor.house_away_duration: ">=24"
    enforce:
      service: input_select.select_option
      target:
        entity_id: input_select.house_mode
      data:
        option: "Vacation"

  - name: house_mode_manual_reset
    priority: 99
    when:
      input_boolean.haus_modus_manuell: "on"
    enforce:
      service: input_select.select_option
      target:
        entity_id: input_select.house_mode
      data:
        option: "Home Day"
```

## Safety examples

```yaml
policies:
  - name: safety_heating_off_when_window_open
    priority: 100
    when:
      binary_sensor.window_living_room: "on"
      climate.living_room: "heat"
    enforce:
      service: climate.set_hvac_mode
      target:
        entity_id: climate.living_room
      data:
        hvac_mode: "off"

  - name: safety_block_garage_when_alarm_armed
    priority: 110
    when:
      alarm_control_panel.house_alarm: "armed_away"
      cover.garage_door: "opening"
    enforce:
      service: cover.close_cover
      target:
        entity_id: cover.garage_door

  - name: safety_turn_off_oven_when_away
    priority: 105
    when:
      input_select.house_mode: "Away"
      switch.oven: "on"
    enforce:
      service: switch.turn_off
      target:
        entity_id: switch.oven
```

## Energy management examples

```yaml
policies:
  - name: energy_cut_peak_load
    priority: 80
    when:
      sensor.house_power: ">4500"
    enforce:
      service: switch.turn_off
      target:
        entity_id:
          - switch.washer
          - switch.dryer

  - name: energy_restore_after_peak
    priority: 70
    when:
      sensor.house_power: "<3500"
    enforce:
      service: switch.turn_on
      target:
        entity_id:
          - switch.washer
          - switch.dryer

  - name: energy_turn_off_media_idle
    priority: 75
    when:
      sensor.steckdose_media_power: "<15"
      switch.steckdose_media: "on"
      input_select.house_mode: "Home Night"
    enforce:
      service: switch.turn_off
      target:
        entity_id: switch.steckdose_media
```

## Comfort and lighting examples

```yaml
policies:
  - name: comfort_night_dim_lights
    priority: 60
    when:
      input_select.house_mode: "Home Night"
      light.living_room: "on"
    enforce:
      service: light.turn_on
      target:
        entity_id: light.living_room
      data:
        brightness_pct: 20

  - name: comfort_day_lights_off_when_bright
    priority: 55
    when:
      input_select.house_mode: "Home Day"
      light.living_room: "on"
      sensor.living_room_lux: ">250"
    enforce:
      service: light.turn_off
      target:
        entity_id: light.living_room

  - name: comfort_bathroom_fan_on
    priority: 70
    when:
      sensor.bathroom_humidity: ">65"
      binary_sensor.bathroom_occupied: "on"
    enforce:
      service: fan.turn_on
      target:
        entity_id: fan.bathroom

  - name: comfort_bathroom_fan_off
    priority: 69
    when:
      sensor.bathroom_humidity: "<60"
      binary_sensor.bathroom_occupied: "off"
    enforce:
      service: fan.turn_off
      target:
        entity_id: fan.bathroom
```

## Explainability and logging examples

```yaml
policies:
  - name: log_high_power_while_away
    priority: 50
    when:
      input_select.house_mode: "Away"
      sensor.house_power: ">1000"
    enforce:
      service: logbook.log
      data:
        name: "HA Governance"
        message: "High power usage while house mode is Away"

  - name: log_night_motion_outside
    priority: 45
    when:
      input_select.house_mode: "Home Night"
      binary_sensor.outdoor_motion: "on"
    enforce:
      service: logbook.log
      data:
        name: "HA Governance"
        message: "Outdoor motion detected during Home Night"

  - name: notify_door_open_in_vacation
    priority: 90
    when:
      input_select.house_mode: "Vacation"
      binary_sensor.front_door: "on"
    enforce:
      service: notify.mobile_app_phone
      data:
        title: "HA Governance"
        message: "Front door opened while House Mode is Vacation"
```

## Structural governance examples

```yaml
policies:
  - name: invariant_no_heating_in_vacation
    priority: 120
    when:
      input_select.house_mode: "Vacation"
      climate.living_room: "heat"
    enforce:
      service: climate.set_hvac_mode
      target:
        entity_id: climate.living_room
      data:
        hvac_mode: "off"

  - name: invariant_no_windows_open_in_away
    priority: 115
    when:
      input_select.house_mode: "Away"
      binary_sensor.window_living_room: "on"
    enforce:
      service: notify.mobile_app_phone
      data:
        title: "HA Governance"
        message: "Window open while House Mode is Away"

  - name: invariant_stop_all_media_in_night
    priority: 85
    when:
      input_select.house_mode: "Home Night"
      media_player.living_room: "playing"
    enforce:
      service: media_player.media_stop
      target:
        entity_id: media_player.living_room
```
