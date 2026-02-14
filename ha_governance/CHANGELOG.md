# CHANGELOG

## [0.1.47] - 2026-02-14 - THE FIX

### Changed
- **BREAKING ARCHITECTURE CHANGE**: Simplified to standard HA Add-on pattern
- Removed complex `rootfs/etc/s6-overlay/s6-rc.d/` structure
- Added simple `/run.sh` script (standard HA pattern)
- This is how it SHOULD have been done from the start

### Why This Version Will Work
Previous versions (0.1.45, 0.1.46) used an over-engineered s6-rc.d service structure that was:
- Unnecessary for simple add-ons
- Error-prone
- Not the HA standard pattern

v0.1.47 uses the **exact same pattern as official HA add-ons**:
- `/run.sh` in root
- s6-overlay calls it automatically
- Simple, proven, works

### Python Code
- ✅ Kept the fixed absolute imports from v0.1.46
- ✅ No code changes needed

---

## [0.1.46] - 2026-02-14 - Import Fix (But Wrong Architecture)

### Fixed
- Python relative imports → absolute imports
- `from .module` → `from module`

### Still Broken
- s6-rc.d structure (too complex)

---

## [0.1.45] - 2026-02-14 - s6-overlay Attempt (Wrong Architecture)

### Added
- s6-overlay service structure (overly complex)

### Still Broken
- Relative imports
- Wrong s6 pattern

---

## [0.1.44] - 2026-02-14 - Initial v0.1

### Issues
- Direct CMD in Dockerfile (bypassed s6)

---

## Summary

**The Journey:**
- 0.1.44: Wrong (CMD bypasses s6)
- 0.1.45: Wrong architecture (s6-rc.d overkill)
- 0.1.46: Fixed imports, still wrong architecture
- **0.1.47: CORRECT** (standard /run.sh pattern)

**Lesson Learned:** 
Keep It Simple. Use the standard pattern. Don't over-engineer.
