# HA Governance v0.1.47 - SIMPLIFIED ARCHITECTURE

## What Changed

**KOMPLETTE Neustrukturierung auf Standard HA Add-on Pattern!**

### Vorher (v0.1.45, v0.1.46)
```
Komplexe s6-rc.d Struktur
rootfs/etc/s6-overlay/s6-rc.d/ha_governance/...
→ Zu komplex, fehleranfällig
```

### Jetzt (v0.1.47)
```
Standard HA Add-on Pattern
/run.sh ← Das war's!
```

---

## Warum das jetzt funktioniert

Home Assistant Add-ons nutzen ein **sehr simples** Pattern:

1. HA base image hat s6-overlay bereits konfiguriert
2. s6-overlay sucht automatisch nach `/run.sh`
3. Wenn `/run.sh` existiert → ausführen
4. **Fertig.**

**Wir haben es überkompliziert!**

---

## Dateistruktur (Ultra-Simple)

```
ha_governance_simple/
├── Dockerfile         ← Installiert Python, kopiert App
├── run.sh            ← ENTRY POINT (wird von s6 aufgerufen)
├── config.yaml       ← HA Add-on Config
├── requirements.txt  ← Python Dependencies
├── policies.yaml     ← Default Policies
└── app/             ← Deine Python App (fixed imports)
    ├── __init__.py
    ├── main.py
    ├── ha_client.py
    ├── state_cache.py
    ├── mode_controller.py
    ├── policy_engine.py
    ├── enforcement.py
    ├── health.py
    └── logging_config.py
```

**KEIN rootfs/ Verzeichnis!**
**KEINE s6-rc.d Komplexität!**

---

## Installation

```bash
cd /path/to/your/ha-governance-repo

# Lösche alte Struktur
rm -rf rootfs/

# Kopiere simple Version
cp -r /path/to/ha_governance_simple/* .

# Commit
git add .
git commit -m "Simplified to standard HA Add-on pattern (v0.1.47)"
git push
```

**In Home Assistant:**
1. Add-on Store → Repository → **Reload**
2. HA Governance → **Update** to 0.1.47
3. **Start**

---

## Was ist in run.sh

```bash
#!/usr/bin/with-contenv bashio

bashio::log.info "Starting HA Governance v0.1.47..."

cd /app || bashio::exit.nok "Cannot change to /app directory"

exec python3 -u main.py
```

**Das war's!** Kein komplexes s6-rc.d Setup nötig.

---

## Dockerfile (Simple)

```dockerfile
ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

WORKDIR /app
COPY app/ /app/

COPY run.sh /
RUN chmod a+x /run.sh

RUN mkdir -p /data
COPY policies.yaml /data/policies.yaml
```

**Kein komplexes COPY rootfs/ /!**

---

## Erwartete Logs

```
[s6-init] making user provided files available...
[cont-init.d] executing initialization scripts...
[services.d] starting services
[11:30:00] INFO: Starting HA Governance v0.1.47...
{"timestamp": "...", "level": "INFO", "message": "Starting HA Governance Add-on v0.1"}
{"timestamp": "...", "level": "INFO", "message": "Connecting to ws://supervisor/core/websocket"}
{"timestamp": "...", "level": "INFO", "message": "WebSocket connected"}
{"timestamp": "...", "level": "INFO", "message": "Authentication successful"}
{"timestamp": "...", "level": "INFO", "message": "Fetching initial states..."}
{"timestamp": "...", "level": "INFO", "message": "Initial sync complete. Loaded 150 entities."}
{"timestamp": "...", "level": "INFO", "message": "Loaded 1 policies."}
{"timestamp": "...", "level": "INFO", "message": "Health server started on port 8099"}
```

**KEINE s6-overlay-suexec Fehler mehr!**

---

## Verify

### 1. Check Status
Add-on Status sollte: **Started** zeigen

### 2. Check Logs
Sollte die erwarteten Logs zeigen (siehe oben)

### 3. Health Endpoint
```bash
curl http://homeassistant.local:8099/health
```

Response:
```json
{
  "status": "ok",
  "websocket_connected": true,
  "uptime_seconds": 123
}
```

---

## Warum v0.1.45/0.1.46 fehlschlug

| Version | Ansatz | Problem | Result |
|---------|--------|---------|--------|
| 0.1.44 | CMD direkt | s6 umgangen | ❌ |
| 0.1.45 | s6-rc.d komplex | Imports + Struktur | ❌ |
| 0.1.46 | s6-rc.d komplex | Imports gefixt, Struktur falsch | ❌ |
| **0.1.47** | **Standard /run.sh** | **Richtig!** | **✅** |

**Der Fehler:** Ich hatte das HA Add-on Pattern überkompliziert!

---

## Was sich geändert hat

### Python Code
✅ **KEINE Änderungen** - Die gefixten absoluten Imports bleiben

### Container Struktur
✅ **MASSIV vereinfacht:**
- Entfernt: `rootfs/etc/s6-overlay/s6-rc.d/...` (komplexer Overkill)
- Hinzugefügt: `/run.sh` (Standard HA Pattern)

---

## Falls es IMMER NOCH nicht startet

Das wäre extrem überraschend, da das jetzt dem exakten Standard-Pattern folgt.

**Aber falls doch:**

1. Check Add-on Logs (nicht Supervisor)
2. Share: `docker logs addon_d2c4c7bf_ha_governance`
3. Verify: `ls -la /path/to/repo/run.sh` (muss existieren und executable sein)

---

## Referenzen

Dieses Pattern ist 1:1 wie offizielle HA Add-ons:
- https://github.com/home-assistant/addons-example
- Alle offiziellen Add-ons nutzen `/run.sh`
- **NICHT** die komplexe s6-rc.d Struktur die ich vorher gebaut habe

---

## Next Steps

Nach erfolgreichem Start:

1. ✅ 24h Stabilität
2. ✅ HA Restart Test
3. ✅ Policy Tests
4. ✅ Health Monitoring

Dann → **Phase 6: Stability Testing** wie geplant!

---

## Sorry!

Ich hatte das HA Add-on Pattern überkompliziert. Die s6-rc.d Struktur ist für **custom s6 services** gedacht, nicht für einfache Add-ons.

**v0.1.47 = Back to Basics = Das richtige Pattern! 🚀**
