# HA Governance Add-on v0.1

Das **HA Governance Add-on** ist eine stabile Governance-Schicht für Home Assistant, die eine deklarative Policy Engine bereitstellt. Es überwacht Zustandsänderungen und korrigiert diese nachträglich (Post-Action Enforcement), falls sie gegen definierte Regeln verstoßen.

**Status**: Implementierungsbereit (v0.1)

## 🚀 Features

### 1. Hybrid House Mode
Verwaltet den globalen Hausmodus basierend auf einer hybriden Logik:
*   **Manuelle Übersteuerung**: Hat Vorrang, gesteuert über `input_select.house_mode_override`.
*   **Abgeleiteter Modus (Derived)**: Wenn keine manuelle Übersteuerung aktiv ist (`AUTO`), wird der Modus deterministisch berechnet:
    *   `NIGHT`: 23:00 - 06:00 Uhr.
    *   `AWAY`: Wenn keine Person (`person.*`) als `home` erkannt wird.
    *   `HOME`: Standardfall.

### 2. Deklarative Policy Engine
Regeln werden in einer `policies.yaml` Datei definiert.
*   **Priorisierung**: Policies werden nach Priorität abgearbeitet.
*   **Deterministisch**: Die erste zutreffende Policy mit Enforcement-Aktion gewinnt.
*   **Limitierung**: Maximal 5 Policies in v0.1.

### 3. Post-Action Enforcement
*   Reagiert auf `state_changed` Events via WebSocket.
*   Korrigiert unerwünschte Zustände durch direkte Service-Calls an Home Assistant.
*   **Loop-Schutz**: Aktionen des Governors werden erkannt und nicht erneut korrigiert.

### 4. Structured Logging
Alle Aktionen werden als strukturiertes JSON geloggt, ideal für spätere Analysen.
Beispiel:
```json
{
  "timestamp": "2026-02-12T10:00:00",
  "event_type": "policy_enforcement",
  "policy": "no_heating_when_window_open",
  "entity_id": "climate.heating",
  "previous_state": "heat",
  "new_state": "{'hvac_mode': 'off'}",
  "effective_mode": "HOME",
  "origin": "governor"
}
```

### 5. Health Endpoint
Ein HTTP-Endpunkt auf Port **8099** liefert den Gesundheitsstatus.
*   `GET /health`
*   Response: `{"status": "ok", "websocket_connected": true, "uptime_seconds": 120}`

## ⚙️ Konfiguration

### policies.yaml
Die Datei muss im Datenverzeichnis des Add-ons liegen (oder im Root für lokale Tests).

Beispiel:
```yaml
policies:
  - name: no_heating_when_window_open
    priority: 100
    when:
      window_open: true    # Erwartet Entity-State 'on'/'open'
      heating_active: true # Erwartet Entity-State 'heat'/'on'
    enforce:
      service: climate.set_hvac_mode
      target: climate.heating
      data:
        hvac_mode: "off"
```

## 🛠️ Entwicklung & Installation

### Voraussetzungen
*   Home Assistant Instanz (Supervisor Token für Auth)
*   Python 3.11+

### Lokal ausführen
```bash
# Environment Variables setzen
export HA_WS_URL="ws://homeassistant.local:8123/api/websocket"
export SUPERVISOR_TOKEN="dein_long_lived_access_token"

# Starten
python -m app.main
```

### Docker
Das Projekt enthält ein `Dockerfile` für die Integration als Home Assistant Add-on.

## ⚠️ Scope & Limitierungen (v0.1)
Folgende Funktionen sind **explizit nicht enthalten**:
*   Kein Multi-User Support.
*   Keine Simulation oder Goal Scoring.
*   Keine UI oder Sprachsteuerung.
*   Kein Machine Learning.
