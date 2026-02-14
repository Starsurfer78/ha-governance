# HA Governance (HACS Custom Integration)

[![Open your Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Starsurfer78&repository=ha-governance&category=integration)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Starsurfer78&repository=ha-governance&category=integration)
[![Start Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_governance)

Deterministischer Policy-Governor für Home Assistant. Evaluierte Zustände führen zu klar definierten Service-Calls mit Cooldown‑Loop‑Protection und transparentem Logging – komplett HA‑native, ohne Docker.

## Features
- HA‑native async, keine eigenen Threads/Loops
- Policies aus `/config/ha_governance/policies.yaml`
- Prioritätsbasierte, deterministische Evaluation (höchste Priority gewinnt)
- Enforcement via `hass.services.async_call`
- Cooldown‑Loop‑Protection (Default 10 s), konfigurierbar
- Logging‑Tags: `[ha_governance] POLICY_TRIGGERED`, `ENFORCEMENT_EXECUTED`, `LOOP_PREVENTED`

## Anforderungen
- Home Assistant (aktueller Stable)
- HACS (für Installation als Custom Integration) oder manuell als `custom_components`

## Installation
### Über HACS (empfohlen)
1. Repository in HACS als Custom Repository hinzufügen
2. Integration „HA Governance“ installieren
3. In Home Assistant die Integration hinzufügen und konfigurieren

### Manuell
1. Ordner `custom_components/ha_governance` in dein HA‑Config‑Verzeichnis kopieren  
   Pfad: `/config/custom_components/ha_governance/`
2. Home Assistant neu starten
3. Integration über UI hinzufügen

## Konfiguration
Über den Config‑Flow:
- `cooldown_seconds` (Default: 10)
- `mode_entity` (optional)
- `policy_path` (Default: `/config/ha_governance/policies.yaml`)

## Policies
Pfad: `/config/ha_governance/policies.yaml`

Beispiel:
```yaml
policies:
  - name: no_heating_with_window_open
    priority: 100
    when:
      binary_sensor.window: "on"
      climate.living_room: "heat"
    enforce:
      service: climate.set_hvac_mode
      target:
        entity_id: climate.living_room
      data:
        hvac_mode: "off"
```

## Funktionsweise
- Beim Start lädt die Integration die `policies.yaml`
- Listener reagieren auf `homeassistant_started` und `state_changed`
- Bei State‑Änderungen wird die höchste passende Policy ermittelt und ausgeführt
- Cooldown verhindert Enforcement‑Schleifen pro Policy

## Hinweise
- Keine WebSocket‑Clients, kein eigener Scheduler, kein Polling
- Rein HA‑native Nutzung von `hass.states.get()` und Events
- `homemanager.txt` wird nicht committed (siehe `.gitignore`)

## Lizenz
MIT (siehe GitHub‑Repository)
