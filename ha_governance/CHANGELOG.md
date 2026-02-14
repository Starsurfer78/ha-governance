# Changelog

## [0.1.45] - 2026-02-14

### Fixed
- **CRITICAL**: Fixed s6-overlay compatibility issue
  - Migrated from direct CMD to s6-service structure
  - Add-on now starts correctly in Home Assistant Supervisor
  - Proper process management via s6-overlay

### Changed
- Restructured Dockerfile for s6-overlay compliance
- Added proper service scripts in /etc/s6-overlay/s6-rc.d/
- Improved logging during startup

## [0.1.44] - 2026-02-14

### Added
- Initial v0.1 implementation
- Hybrid House Mode Controller
- Declarative Policy Engine
- Post-Action Enforcement with loop protection
- WebSocket connection to Home Assistant
- Health endpoint on port 8099
- Structured JSON logging
- Reconnect logic with exponential backoff
- Event processing lock (race condition fix)
- Token loading from options.json or environment

### Known Issues
- s6-overlay startup error (fixed in 0.1.45)

## [0.1.0] - 2026-02-12

### Added
- Project inception
- Architecture design
- PRD documentation
