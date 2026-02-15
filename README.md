# HA Governance (HACS Custom Integration)

[![Open your Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Starsurfer78&repository=ha-governance&category=integration)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Starsurfer78&repository=ha-governance&category=integration)
[![Start Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_governance)

Deterministic Policy Engine for Home Assistant.

- Centralized rule enforcement
- Conflict resolution by priority
- Fully local, explainable and auditable

Replace fragile automation chains with deterministic, priority-based rule enforcement.

🧠 HA Governance

Deterministic Control Layer for Home Assistant  
Foundation for a Local “Jarvis”-Style System

## What is HA Governance?

HA Governance is a deterministic rule enforcement engine for Home Assistant.  
It is designed as the control layer beneath a future local AI / Orchestrator system.

Instead of:

- scattered automations
- race conditions
- hidden state logic
- event-order dependencies

Governance provides:

- Centralized rule evaluation
- Priority-based conflict resolution
- Snapshot-based determinism
- Loop protection
- Audit & explainability
- Fully local execution

## Why this exists

If you want to build something like Jarvis, you cannot rely on:

- fragile automation chains
- implicit event ordering
- non-deterministic behavior

You need:

- a stable policy layer
- a predictable system core
- a safety net below any AI logic

HA Governance is that layer.

AI (or any orchestrator) can suggest actions. Governance decides if they are allowed.

## System architecture

Voice Interface (future)  
        ↓  
Orchestrator (future)  
        ↓  
HA Governance ← this project  
        ↓  
Home Assistant Core

Governance acts as:

- Policy validator
- Enforcement engine
- Safety boundary
- Deterministic rule resolver

## Example policy

```yaml
policies:
  - name: heating_off_if_window_open
    priority: 100
    when:
      binary_sensor.window_livingroom: "on"
      climate.heating: "heat"
    enforce:
      service: climate.turn_off
      target:
        entity_id: climate.heating
```

Regardless of:

- automation order
- AI suggestions
- manual interaction

this invariant is always enforced.

## Deterministic by design

HA Governance guarantees:

- Immutable policy snapshots
- Priority → name stable sorting
- Serialized event processing
- Cooldown-based loop protection
- Context-aware self-event detection
- Deduplicated decisions
- Relevant-entity event filtering

Given identical system state and policy snapshot, the same rule will always win.

## Installation

### Option 1 – Manual installation

- Copy the `ha_governance` folder into:
  - `/config/custom_components/`
- Restart Home Assistant
- Go to:
  - Settings → Devices & Services → Add Integration
- Search for:
  - `HA Governance`
- Configure the policy file path (default: `/config/policies.yaml`)

### Option 2 – HACS (if published)

- Add custom repository (Integration type)
- Install HA Governance
- Restart Home Assistant
- Add integration via Settings → Devices & Services

## Policy file location

- Default path: `/config/policies.yaml`
- You can override this in the integration options
- On first setup, a default file is created automatically if missing

## Configuration (UI)

- `cooldown_seconds` (default: 10)
- `mode_entity` (reserved for future modes/switches)
- `policy_path` (default: `/config/policies.yaml`)
- Changes in the UI trigger an automatic reload of policies

## Example policy

```yaml
policies:
  - name: media_power_off_when_idle
    priority: 80
    when:
      sensor.steckdose_media_power: "<22"
      switch.steckdose_media: "on"
    enforce:
      service: switch.turn_off
      target:
        entity_id: switch.steckdose_media
```

If the media power drops below 22 W and the switch is on, Governance turns it off deterministically.

## House mode state machine (optional)

Governance can model a full house state machine:

- Home Day
- Home Night
- Away
- Vacation

Transitions become deterministic policies:

- No race conditions
- No mode ping-pong
- No hidden automations

For a full House Mode setup including helpers, template sensors and policies, see [HOUSE_MODE.md](docs/HOUSE_MODE.md).

## Observability & explainability

- `sensor.ha_governance_policy_count`: count of currently loaded policies
- `sensor.ha_governance_policy_stats`: per-policy statistics (`total`, `today`, `success_*`, `error_*`, `cooldown_skipped_*`, `last_executed`, `last_result`)
- `sensor.ha_governance_last_decision`: last decided policy with `timestamp`, `event_type`, `entity_id`, `policy_snapshot_hash`, `enforcement_result`, `context_id`

You can always see which rule fired, why it did so, and whether enforcement succeeded.

## Changelog (short)

- v0.1.13: Event filter on relevant entities and deduplication of identical decisions (LastDecision sensor much quieter)
- v0.1.12: Startup fix – register event listeners only after HA start; debug hints for missing entities; error handling in the event handler; unified logger
- v0.1.11: Hotfix – prevents event loop for LastDecision sensor (`sensor.ha_governance_*` no longer evaluated)
- v0.1.10: Decision audit layer (snapshot hash, DecisionRecords, LastDecision sensor), PolicyStats meta sensor
- v0.1.9: PolicyCount sensor, dynamic integration title, dispatcher-based architecture, reload lock and deterministic policy sorting
- v0.1.8: Schema check and SHA256 hash logging for `policies.yaml`, update-safe path
- v0.1.7: Periodic context cleanup via `async_track_time_interval` (HA-native)
- v0.1.6: New `when` matcher with operators and attribute support
- v0.1.4: Default path under `custom_components`, fallback and README update
- v0.1.3: UI config fixed (ConfigFlow), manifest `config_flow` enabled
- v0.1.2: Manifest extended (`config_flow`), HACS compatibility
- v0.1.1: HACS metadata added
- v0.1.0: Initial version

## Documentation

- Documentation index: [INDEX.md](docs/INDEX.md)
- Governance basics: [README_GOVERNANCE.md](docs/README_GOVERNANCE.md)
- Architecture guide: [README_Anleitung.md](docs/README_Anleitung.md)

## License

MIT
