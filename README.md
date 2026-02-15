# HA Governance (HACS Custom Integration)

[![Open your Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Starsurfer78&repository=ha-governance&category=integration)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Starsurfer78&repository=ha-governance&category=integration)
[![Start Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_governance)

## Worum geht es?
- HA Governance ist eine schlanke Governance‑Schicht über deinen Automationen. Sie erzwingt „harte Regeln“ (Policies), die quer durch dein Smart Home gelten sollen – deterministisch, zentral und nachvollziehbar.
- Typisch für Governance‑Regeln sind Sicherheits‑, Energie‑ und Konsistenzregeln, z. B. „Heizung aus, wenn Fenster offen“, „Kein Garagentor auf, wenn Alarm scharf“, „Schalte energieintensive Geräte in der Spitze ab“.
- Statt Logik über viele Automationen zu verteilen, definierst du diese Regeln einmalig in YAML (Policies). Die Integration prüft bei Zustandsänderungen, ob eine Policy greift, und führt dann genau einen Service‑Call aus – mit klarer Priorität und Schutz vor Loops.

## Warum nicht einfach Automationen?
- Zentrale Regeln: Policies liegen an einem Ort und sind leicht auditierbar.
- Deterministische Konfliktauflösung: Höchste Priority gewinnt, erste passende Policy wird ausgeführt.
- Robustheit: Schutz gegen Endlos‑Schleifen (Cooldown), Ereignisse werden seriell verarbeitet.
- Transparenz: Einheitliche Logging‑Tags, klare Ausführungspfade.

## Was macht die Integration genau?
- Lauscht HA‑Events (`state_changed`, `homeassistant_started`) und lädt/prüft deine Policies.
- Bewertet Bedingungen (`when`) gegen aktuelle Entity‑States.
- Führt den definierten Enforcement‑Service aus (z. B. `climate.set_hvac_mode`) für die erste passende Policy mit der höchsten Priority.
- Verhindert Schleifen (Cooldown, Default 10 s) und parallele Ausführungen (Event‑Lock).

## Features
- HA‑native async, kein eigener Scheduler, keine Neben‑Threads
- YAML‑Policies in `/config/policies.yaml` (Default, update‑sicher)
- Prioritätsbasierte, deterministische Evaluation
- Enforcement via `hass.services.async_call`
- Cooldown‑Loop‑Protection (Default 10 s), konfigurierbar
- Transparente Logs: `[ha_governance] POLICY_TRIGGERED`, `ENFORCEMENT_EXECUTED`, `LOOP_PREVENTED`

## Installation
- Über HACS (empfohlen): Repository hinzufügen, Integration installieren, in HA hinzufügen
- Manuell: Ordner `custom_components/ha_governance` nach `/config/custom_components/` kopieren, HA neu starten

## Konfiguration (UI)
- `cooldown_seconds` (Default: 10)
- `mode_entity` (optional; reserviert für zukünftige Modi/Schalter)
- `policy_path` (Default: `/config/policies.yaml`)
- Änderungen im UI triggern automatisches Reload der Policies

## Policy‑Format (YAML)
```yaml
policies:
  - name: <eindeutiger_name>
    priority: <integer>         # höher = wichtiger
    when:                       # Map: entity_id -> erwarteter State (String)
      binary_sensor.window: "on"
      climate.living_room: "heat"
    enforce:                    # auszuführender Service‑Call
      service: climate.set_hvac_mode
      target:
        entity_id: climate.living_room
      data:
        hvac_mode: "off"
```

## Beispiele
- Heizung aus bei offenem Fenster  
  Siehe oben – verhindert Energieverschwendung
- Nachtmodus dimmt Licht
```yaml
policies:
  - name: night_mode_dim_lights
    priority: 50
    when:
      sensor.local_time_period: "night"
      light.living_room: "on"
    enforce:
      service: light.turn_on
      target:
        entity_id: light.living_room
      data:
        brightness_pct: 20
```

## Betrieb und Verhalten
- Beim HA‑Start werden Policies geladen, bei State‑Änderungen evaluiert.
- Ersttreffer‑Prinzip: höchste Priorität gewinnt, es wird nur eine Policy ausgeführt.
- Cooldown schützt pro Policy vor wiederholter Ausführung in kurzer Zeit.
- Event‑Verarbeitung ist serialisiert, um parallele Enforcements zu vermeiden.
 - Loop‑Prevention per Context:
   - Jeder Enforcement‑Call erhält einen eigenen Context; selbstverursachte Events werden erkannt und ignoriert.
   - Kontext‑Cleanup nach 10 s verhindert Speicheraufbau.
   - Periodischer Sicherheits‑Cleanup leert den Kontext‑Cache etwa stündlich.

## Troubleshooting
- „Policy file not found“ im Log:  
-  Datei unter `/config/policies.yaml` anlegen oder im UI `policy_path` setzen.
- UI‑Flow fehlt: Version ≥ v0.1.3 installieren, HA neu starten.
- Änderungen wirken nicht: Nach Policy‑Anpassungen HA neu starten oder kurz warten; bei Pfad‑Änderung im UI erfolgt Reload.

## Changelog (kurz)
- v0.1.8: Schema‑Check und SHA256‑Hash‑Logging für policies.yaml, update‑sicherer Pfad
- v0.1.7: Periodischer Context‑Cleanup über async_track_time_interval (HA‑konform)
- v0.1.6: Neuer when‑Matcher mit Operatoren und Attribut‑Support
- v0.1.4: Default‑Pfad unter `custom_components`, Fallback und README‑Update
- v0.1.3: UI‑Config repariert (ConfigFlow), manifest config_flow aktiv
- v0.1.2: manifest ergänzt (config_flow), HACS‑Kompatibilität
- v0.1.1: HACS‑Metadaten hinzugefügt
- v0.1.0: Initiale Version

## Dokumentation
- Dokumentations‑Index: [INDEX.md](file:///e:/TRAE/ha-governance/docs/INDEX.md)
- Governance‑Grundlagen: [README_GOVERNANCE.md](file:///e:/TRAE/ha-governance/docs/README_GOVERNANCE.md)
- Architektur‑Anleitung: [README_Anleitung.md](file:///e:/TRAE/ha-governance/docs/README_Anleitung.md)

## Lizenz
MIT
