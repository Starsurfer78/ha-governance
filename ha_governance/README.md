# HA Governance Add-on v0.1

**Deterministic Policy Governor for Home Assistant**

## 🚀 Installation

1. Add this repository to your Home Assistant Add-on Store
2. Install "HA Governance"
3. Configure your `ha_token` (Long-Lived Access Token) if not using Supervisor auto-auth
4. Start the add-on

## ⚙️ Configuration

### Options

- `ha_token` (optional): Long-Lived Access Token
  - Leave empty to use automatic Supervisor authentication
  - Required for manual/external deployments

### Policies

Create `/data/policies.yaml` or edit via File Editor:

```yaml
policies:
  - name: no_heating_when_window_open
    priority: 100
    when:
      binary_sensor.window_living_room: true
      climate.heating: "heat"
    enforce:
      service: climate.set_hvac_mode
      target: climate.heating
      data:
        hvac_mode: "off"
```

## 📊 Health Endpoint

Access health status at: `http://homeassistant.local:8099/health`

Response:
```json
{
  "status": "ok",
  "websocket_connected": true,
  "uptime_seconds": 3600
}
```

## 🔍 Logs

All actions are logged as structured JSON:

```json
{
  "timestamp": "2026-02-14T10:30:00",
  "event_type": "policy_enforcement",
  "policy": "no_heating_when_window_open",
  "entity_id": "climate.heating",
  "previous_state": "heat",
  "effective_mode": "HOME",
  "origin": "governor"
}
```

## 🛠️ Troubleshooting

### Add-on won't start

1. Check logs for authentication errors
2. Verify `ha_token` if configured
3. Ensure WebSocket URL is correct (`ws://supervisor/core/websocket`)

### Policies not triggering

1. Verify entity IDs exist in Home Assistant
2. Check policy conditions match actual states
3. Review structured logs for evaluation details

## 📚 Documentation

Full documentation: [GitHub Repository](https://github.com/Starsurfer78/ha-governance)

## ⚠️ v0.1 Scope

This is a **Governor** (enforcement layer), not yet a full Home Manager:

**Included:**
- ✅ Hybrid House Mode (AUTO/HOME/AWAY/NIGHT)
- ✅ Declarative Policy Engine
- ✅ Post-Action Enforcement
- ✅ Loop Protection
- ✅ Structured Logging

**Not Included (future v0.2+):**
- ❌ Goal-based optimization
- ❌ Simulation mode
- ❌ Multi-user support
- ❌ Learning capabilities

## 📝 License

MIT License - Copyright (c) 2026 Starsurfer78
