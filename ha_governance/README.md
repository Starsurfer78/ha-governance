# HA Governance v0.1.46 - Simplified Build

## What's Different from v0.1.45

### Removed Bashio Dependency
v0.1.45 used `bashio::log` which might not be available in all base images.
v0.1.46 uses plain `echo` - more portable.

### Simplified Paths
- Before: `exec python3 -u /app/main.py`
- Now: `cd /app && exec python3 -u main.py`

More explicit about working directory.

### Minimal Service Structure
Removed optional `finish` script - only essential `run` and `type`.

---

## Installation

Same as before:
```bash
cd /path/to/your/repo
cp -r /path/to/ha_governance_v2/* .
git add .
git commit -m "Simplified s6-overlay structure (v0.1.46)"
git push
```

Then reload in HA Add-on Store.

---

## If It Still Doesn't Start

**SEE DEBUG.md FOR CRITICAL DEBUGGING STEPS!**

The key is getting the ACTUAL container logs, not just supervisor logs.

### Quick Check
```bash
# In HA Terminal or SSH
docker logs addon_d2c4c7bf_ha_governance
```

This will show the REAL error.

---

## Files Included

```
ha_governance_v2/
├── Dockerfile            ← Simplified
├── config.yaml           ← v0.1.46
├── requirements.txt
├── policies.yaml
├── app/
│   └── *.py             ← Your code (unchanged)
├── rootfs/
│   └── etc/s6-overlay/s6-rc.d/
│       ├── ha_governance/
│       │   ├── run      ← Simplified, no bashio
│       │   └── type
│       └── user/contents.d/
│           └── ha_governance
└── DEBUG.md             ← READ THIS IF STILL FAILING
```

---

## Expected Logs (Success)

```
[HA Governance] Starting service...
{"timestamp": "...", "level": "INFO", "message": "Starting HA Governance Add-on v0.1"}
{"timestamp": "...", "level": "INFO", "message": "Connecting to ws://supervisor/core/websocket"}
{"timestamp": "...", "level": "INFO", "message": "WebSocket connected"}
{"timestamp": "...", "level": "INFO", "message": "Authentication successful"}
```

If you don't see this → check actual container logs (see DEBUG.md).
