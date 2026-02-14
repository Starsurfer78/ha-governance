# ⚡ QUICK FIX - v0.1.47

## Das Problem (endlich verstanden!)

Ich hatte das HA Add-on Pattern **massiv überkompliziert** mit s6-rc.d Strukturen.

**Die Wahrheit:** HA Add-ons brauchen nur `/run.sh` im Root. Fertig.

---

## 3-Schritt-Fix

### 1. Alte Struktur löschen
```bash
cd /path/to/your/ha-governance-repo

# Lösche die komplexe rootfs/ Struktur
rm -rf rootfs/
```

### 2. Neue simple Struktur kopieren
```bash
# Kopiere alle Dateien aus ha_governance_simple/
cp /path/to/ha_governance_simple/* .

# WICHTIG: Stelle sicher dass run.sh existiert und executable ist
ls -la run.sh
# Sollte zeigen: -rwxr-xr-x ... run.sh
```

### 3. Deploy
```bash
git add .
git commit -m "Fix: Simplified to standard HA Add-on pattern (v0.1.47)"
git push
```

**In HA:**
- Add-on Store → Reload → Update zu 0.1.47 → Start

---

## Datei-Checkliste

Nach dem Kopieren solltest du haben:

```
your-repo/
├── Dockerfile       ✅
├── run.sh          ✅ (WICHTIG!)
├── config.yaml      ✅ (Version 0.1.47)
├── requirements.txt ✅
├── policies.yaml    ✅
└── app/            ✅
    ├── __init__.py
    ├── main.py
    ├── (... andere .py Dateien)
```

**KEIN rootfs/ Verzeichnis!**

---

## Erwartetes Ergebnis

### Vorher:
```
s6-overlay-suexec: fatal: can only run as pid 1
[Crash Loop]
```

### Nachher:
```
[11:30:00] INFO: Starting HA Governance v0.1.47...
{"level": "INFO", "message": "Starting HA Governance Add-on v0.1"}
{"level": "INFO", "message": "WebSocket connected"}
{"level": "INFO", "message": "Authentication successful"}
[Läuft stabil]
```

---

## Warum das jetzt funktioniert

**HA Base Image:**
1. Startet s6-overlay als PID 1 ✅
2. s6-overlay sucht nach `/run.sh` ✅
3. Findet es → führt aus ✅
4. `/run.sh` startet Python ✅

**Vorher (falsch):**
1. s6-overlay startet ✅
2. Sucht nach komplexer s6-rc.d Struktur ❌
3. Findet sie nicht korrekt ❌
4. Crash ❌

---

## Verify

```bash
# Health Check
curl http://homeassistant.local:8099/health

# Expected:
{"status": "ok", "websocket_connected": true, "uptime_seconds": 123}
```

---

## If It STILL Doesn't Work

Das wäre sehr überraschend, weil das jetzt 1:1 das Standard-Pattern ist.

**Debug:**
```bash
# Check if run.sh exists in container
docker exec addon_d2c4c7bf_ha_governance ls -la /run.sh

# Check logs
docker logs addon_d2c4c7bf_ha_governance
```

---

## Die Essenz

v0.1.44-0.1.46: **Überkompliziert**
v0.1.47: **Keep It Simple** ← Richtig!

**Das hätte die erste Version sein sollen!** 🎯
