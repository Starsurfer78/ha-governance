# What Changed: v0.1.44 → v0.1.45

## The Core Problem

Your original Dockerfile:
```dockerfile
CMD ["/bin/sh", "-c", "python3 /app/main.py"]
```

This tries to run Python **directly as the container's main process**, but Home Assistant's base images use **s6-overlay** for process supervision. s6-overlay must run as PID 1, not Python.

## The Solution: s6-Service Structure

Home Assistant Add-ons follow a specific pattern:

### Old Way (Broken)
```
Container starts
  ↓
s6-overlay initializes
  ↓
CMD tries to run Python directly ← CONFLICT!
  ↓
"can only run as pid 1" error
```

### New Way (Fixed)
```
Container starts
  ↓
s6-overlay initializes as PID 1 ✅
  ↓
s6-overlay reads /etc/s6-overlay/s6-rc.d/
  ↓
Finds our "ha_governance" service
  ↓
Runs /etc/s6-overlay/s6-rc.d/ha_governance/run
  ↓
Python starts under s6 supervision ✅
```

## File Changes

### 1. NEW: Service Definition Files

#### `/rootfs/etc/s6-overlay/s6-rc.d/ha_governance/type`
```
longrun
```
Tells s6 this is a long-running service (not one-shot).

#### `/rootfs/etc/s6-overlay/s6-rc.d/ha_governance/run`
```bash
#!/command/with-contenv bashio

bashio::log.info "Starting HA Governance v0.1..."
cd /app || bashio::exit.nok "Could not change to /app directory"
exec python3 -u /app/main.py
```
This is the **actual entrypoint** now.

- `#!/command/with-contenv bashio` - Uses HA's bashio environment
- `exec python3 -u /app/main.py` - Replaces shell with Python process

#### `/rootfs/etc/s6-overlay/s6-rc.d/ha_governance/finish`
```bash
#!/command/with-contenv bashio

bashio::log.info "HA Governance service stopped"
```
Called when service exits (cleanup handler).

#### `/rootfs/etc/s6-overlay/s6-rc.d/user/contents.d/ha_governance`
```
ha_governance
```
Registers our service in the user bundle (makes s6 aware of it).

### 2. CHANGED: Dockerfile

#### Old (Broken)
```dockerfile
CMD ["/bin/sh", "-c", "python3 /app/main.py"]
```

#### New (Fixed)
```dockerfile
# Copy s6-overlay service definitions
COPY rootfs/ /

# ... (rest of file)

# Make scripts executable
RUN chmod a+x /etc/s6-overlay/s6-rc.d/ha_governance/run
RUN chmod a+x /etc/s6-overlay/s6-rc.d/ha_governance/finish
```

**NO CMD!** The base image's ENTRYPOINT (s6-overlay) handles everything.

### 3. CHANGED: config.yaml

```yaml
version: "0.1.44"  →  version: "0.1.45"
```

## Why This Matters

### With the Old Approach
- ❌ Container crashes immediately
- ❌ No s6-overlay supervision
- ❌ No proper logging integration
- ❌ No graceful shutdown handling

### With the New Approach
- ✅ Service starts correctly
- ✅ s6-overlay manages process lifecycle
- ✅ Automatic restart on crash
- ✅ Proper signal handling (SIGTERM)
- ✅ Integration with HA's logging system

## What You Don't Need to Change

These files are identical:
- ✅ All Python code in `app/`
- ✅ `requirements.txt`
- ✅ `policies.yaml`
- ✅ Your repository structure

## Visual Comparison

### Directory Structure Before
```
ha_governance/
├── Dockerfile          ← Broken CMD
├── config.yaml
├── app/
│   └── *.py
├── requirements.txt
└── policies.yaml
```

### Directory Structure After
```
ha_governance/
├── Dockerfile          ← Fixed (no CMD, copies rootfs)
├── config.yaml         ← Version bump
├── rootfs/             ← NEW! s6-overlay integration
│   └── etc/
│       └── s6-overlay/
│           └── s6-rc.d/
│               ├── ha_governance/
│               │   ├── run      ← Your actual entrypoint
│               │   ├── finish
│               │   └── type
│               └── user/
│                   └── contents.d/
│                       └── ha_governance
├── app/
│   └── *.py            ← Unchanged
├── requirements.txt    ← Unchanged
└── policies.yaml       ← Unchanged
```

## Testing the Fix

### Before (Error)
```
s6-overlay-suexec: fatal: can only run as pid 1
s6-overlay-suexec: fatal: can only run as pid 1
s6-overlay-suexec: fatal: can only run as pid 1
[Crash loop]
```

### After (Success)
```
[s6-init] making user provided files available...
[cont-init.d] executing initialization scripts...
[services.d] starting services
[services.d] done.
Starting HA Governance v0.1...
{"timestamp": "...", "level": "INFO", "message": "Starting HA Governance Add-on v0.1"}
{"timestamp": "...", "level": "INFO", "message": "WebSocket connected"}
{"timestamp": "...", "level": "INFO", "message": "Authentication successful"}
[Running successfully]
```

## Common Questions

**Q: Why not just change the base image?**
A: All official HA base images use s6-overlay. It's the standard.

**Q: Can I still run this locally without Docker?**
A: Yes! Just run `python3 -m app.main` directly. The s6 structure only matters in Docker.

**Q: Will this affect my policies or configuration?**
A: No. This is purely a container startup fix. Your application logic is unchanged.

**Q: Do I need to change anything in my Python code?**
A: No. The Python code remains exactly the same.

## Reference

- s6-overlay documentation: https://github.com/just-containers/s6-overlay
- HA Add-on development: https://developers.home-assistant.io/docs/add-ons/
- Typical s6 service structure: https://github.com/home-assistant/addons-example
