# 🐛 DEBUGGING GUIDE - v0.1.46

## Your Current Situation

Build succeeds ✅
Installation succeeds ✅
**But container exits immediately without logs** ❌

This is a **silent fail** - we need the actual container logs.

---

## CRITICAL: Get the Real Logs

### Method 1: Home Assistant UI
1. Go to **Settings → Add-ons**
2. Click on **HA Governance**
3. Click **Logs** tab
4. **Copy EVERYTHING you see there**

### Method 2: SSH/Terminal
```bash
docker logs addon_d2c4c7bf_ha_governance
```

### Method 3: Live Tail
```bash
docker logs -f addon_d2c4c7bf_ha_governance
```

**Send me those logs!** They will show:
- Python errors
- Import failures  
- Permission errors
- Actual crash reason

---

## What Changed in v0.1.46

### Simplified run script
```bash
#!/usr/bin/with-contenv bash
set -e

echo "[HA Governance] Starting service..."

cd /app
exec python3 -u main.py
```

**Changes:**
- ✅ Removed bashio dependency (might not be available)
- ✅ Simpler paths (`main.py` instead of `/app/main.py`)
- ✅ Plain echo instead of bashio::log
- ✅ Explicit `set -e` for error propagation

### Simplified Dockerfile
- ✅ Removed `finish` script (not essential)
- ✅ Explicit chmod in build
- ✅ Minimal dependencies

---

## Common Silent Fail Causes

### 1. Python Import Error
```python
# If this fails, container exits silently
from .logging_config import setup_logging
```

**Fix:** Make sure `app/__init__.py` exists

### 2. Missing Dependencies
```
ModuleNotFoundError: No module named 'aiohttp'
```

**Fix:** Verify requirements.txt is correct

### 3. Wrong Python Path
```
python3: can't open file '/app/main.py': [Errno 2] No such file or directory
```

**Fix:** Check COPY in Dockerfile

### 4. Import from Wrong Location
```python
# In main.py, if you have:
from app.logging_config import setup_logging  # ← WRONG in /app
```

Should be:
```python
from logging_config import setup_logging  # ← CORRECT
```

---

## Quick Test: Does Python Even Start?

Add this to the **run** script temporarily:
```bash
#!/usr/bin/with-contenv bash
set -e

echo "[DEBUG] Starting HA Governance..."
echo "[DEBUG] Python version:"
python3 --version

echo "[DEBUG] Current directory:"
pwd

echo "[DEBUG] Files in /app:"
ls -la /app

echo "[DEBUG] Attempting to start main.py..."
cd /app
python3 -u main.py
```

This will show us WHERE it fails.

---

## Temporary Workaround: Test Without s6

If you want to test if your Python code works at all:

### Test Dockerfile (Bypass s6)
```dockerfile
FROM python:3.11-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

CMD ["python3", "-u", "main.py"]
```

Build and run:
```bash
docker build -t ha-gov-test .
docker run --rm -e HA_WS_URL="ws://your-ha:8123/api/websocket" \
                 -e SUPERVISOR_TOKEN="your-token" \
                 ha-gov-test
```

If this works → s6 issue
If this fails → Python/app issue

---

## Next Steps

1. **Get the real container logs** (see methods above)
2. Share them with me
3. I'll tell you exactly what's failing
4. We'll fix it

The supervisor logs only show "starting..." but not WHY it stops.

**The container logs will show the actual error!**
