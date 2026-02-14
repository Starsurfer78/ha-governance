# Installation Guide - HA Governance v0.1.45

## Quick Fix for Your Issue

The `s6-overlay-suexec: fatal: can only run as pid 1` error has been fixed in this version.

### What Changed

**Problem:** The Dockerfile was using `CMD ["/bin/sh", "-c", "python3 /app/main.py"]` which bypassed the s6-overlay process supervisor.

**Solution:** 
- Added proper s6-service structure in `/rootfs/etc/s6-overlay/s6-rc.d/`
- Service runs via s6-overlay as intended by HA Add-on architecture
- Removed direct CMD execution

## Installation Steps

### 1. Replace Files in Your Repository

Copy these files from this fixed version to your repository:

```
ha_governance_fixed/
├── Dockerfile                    # ← UPDATED (critical fix)
├── config.yaml                   # ← Version bumped to 0.1.45
├── rootfs/                       # ← NEW (s6-overlay structure)
│   └── etc/
│       └── s6-overlay/
│           └── s6-rc.d/
│               ├── ha_governance/
│               │   ├── run       # ← Service entrypoint
│               │   ├── finish    # ← Cleanup handler
│               │   └── type      # ← Service type
│               └── user/
│                   └── contents.d/
│                       └── ha_governance
├── app/                          # Your existing app files
├── requirements.txt
├── policies.yaml
└── README.md
```

### 2. Update Your Repository

```bash
cd /path/to/your/ha-governance-repo

# Copy fixed structure
cp -r /path/to/ha_governance_fixed/* .

# Commit and push
git add .
git commit -m "Fix: s6-overlay compatibility (v0.1.45)"
git push
```

### 3. Update Add-on in Home Assistant

1. Go to **Settings → Add-ons → Add-on Store**
2. Click **⋮** (three dots) on your repository
3. Click **Reload**
4. Find "HA Governance"
5. Click **Update** (should show 0.1.45)
6. Click **Start**

## Verify It Works

### Check Logs

Should now show:
```
[s6-init] making user provided files available at /var/run/s6/etc...exited 0.
[s6-init] ensuring user provided files have correct perms...exited 0.
[fix-attrs.d] applying ownership & permissions fixes...
[fix-attrs.d] done.
[cont-init.d] executing container initialization scripts...
[cont-init.d] done.
[services.d] starting services
[services.d] done.
Starting HA Governance v0.1...
{"timestamp": "2026-02-14T...", "level": "INFO", "message": "Starting HA Governance Add-on v0.1", ...}
{"timestamp": "2026-02-14T...", "level": "INFO", "message": "Connecting to ws://supervisor/core/websocket", ...}
{"timestamp": "2026-02-14T...", "level": "INFO", "message": "WebSocket connected", ...}
{"timestamp": "2026-02-14T...", "level": "INFO", "message": "Authentication successful", ...}
```

### Test Health Endpoint

```bash
curl http://homeassistant.local:8099/health
```

Expected response:
```json
{
  "status": "ok",
  "websocket_connected": true,
  "uptime_seconds": 123
}
```

## Troubleshooting

### Still getting s6 errors?

1. Make sure you copied the **entire** `rootfs/` directory structure
2. Verify the `run` and `finish` scripts are executable:
   ```bash
   chmod +x rootfs/etc/s6-overlay/s6-rc.d/ha_governance/run
   chmod +x rootfs/etc/s6-overlay/s6-rc.d/ha_governance/finish
   ```
3. Check Dockerfile actually has the COPY lines for rootfs

### Authentication Failed?

1. If using manual token: Set `ha_token` in Add-on Configuration
2. If using Supervisor auto-auth: Leave `ha_token` empty
3. Check Home Assistant logs for auth errors

### WebSocket Won't Connect?

1. Verify `homeassistant_api: true` is in config.yaml
2. Check if other add-ons can connect
3. Try restarting Home Assistant Core

## Next Steps

Once running successfully:

1. Create your policies in `/data/policies.yaml`
2. Monitor structured logs
3. Set up `input_select.house_mode_override` entity if using hybrid mode
4. Let it run for 4-6 weeks to ensure stability (Phase 6)

## Support

- Issues: GitHub Issues on your repository
- Logs: Check Add-on Logs in Home Assistant
- Structured Logs: Available in `/var/log/` or via HA log viewer
