Jarvis House Architecture – Room & Policy Model

Version 0.1

🧠 Purpose

This document describes the structural architecture of the smart home system built on HA Governance as deterministic control layer.

Goals:

- deterministic safety logic
- clear separation between automations and policies
- room-based structure
- scalability for a Jarvis-style orchestrator
- debuggability and maintainability

🏗 System layers

- Automation layer  → triggers and flows
- Policy layer      → global state rules (HA Governance)
- Home Assistant    → state machine
- Jarvis (optional) → orchestrator / intent / goals


Important:

- automations trigger actions
- policies enforce global safety and energy boundaries
- policies contain no trigger logic
- automations must not contain global protection rules

🏠 Room model

Each room is treated as a logical unit.

A room consists of:

Component                 Purpose  
`window_<room>_any_open`  at least one window open  
`presence_<room>`         occupancy in the room  
`climate.<room>`          heating / climate entity  
`light.<room>_main`       main light group  
`sensor.temperature_<room>`  temperature  
`sensor.co2_<room>` (optional) air quality  

🪟 Window aggregation

If a room has multiple windows, they are combined via a template binary sensor.

Example:

template:
  - binary_sensor:
      - name: window_wohnzimmer_any_open
        state: >
          {{
            is_state('binary_sensor.window_wz_links', 'on')
            or
            is_state('binary_sensor.window_wz_rechts', 'on')
          }}

Why?

- no wildcards in policies
- clear 1:1 mapping between room and heating circuit
- debuggable in HA state
- orchestrator compatible

🔥 Heating protection rule

Global safety rule:

- name: heating_window_protection_wohnzimmer
  priority: 95
  when:
    binary_sensor.window_wohnzimmer_any_open: "on"
    climate.wohnzimmer: "heat"
  enforce:
    service: climate.turn_off
    target: climate.wohnzimmer

Rule:

If a window is open, heating must not be active.  
This logic belongs exclusively in the policy layer.

💡 Lighting logic

Lighting automations contain only:

- triggers (motion, lux, TV)
- flow / sequence

Global limits (for example night mode) belong into policies.  
Adaptive lighting remains a comfort engine and must not be forced permanently.

⚡ Media socket logic

Shutdown happens only in a confirmed idle state.

- automation detects idle
- policy enforces shutdown

Separation:

- automation = state detection
- policy = physical constraint

📛 Naming conventions

All room-based entities follow this pattern:

- `window_<room>_any_open`
- `presence_<room>`
- `climate.<room>`
- `light.<room>_main`

No wildcards in policies.  
No global window aggregates.

🔐 Safety principles

- safety has highest priority
- energy comes before comfort
- policies contain no triggers
- automations contain no global protection rules
- LLMs (if used) are never final decision makers

🚦 Migration rule

When refactoring automations:

- if a condition describes a global physical boundary,  
  move it into `policies.yaml`
- keep the rest of the automation unchanged

🎯 Target state

The system should:

- be deterministic
- be scalable
- be debuggable
- be orchestrator-ready
- not depend on implicit logic chains

📌 Note

This document describes the structure.  
It does not replace automations, it defines their boundaries.
