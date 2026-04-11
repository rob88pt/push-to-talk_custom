# push-to-talk_custom - Session Handoff

**Date**: 2026-04-09
**Location**: `/home/robert/Dev/My_Setup/push-to-talk_custom`
**Session Goal**: Diagnose why transcription text was not being pasted into WezTerm, fix the root cause, and rebuild the binary.

---

## Chronological Narrative

### 1. Investigation

- **The Challenge**: User reported push-to-talk transcription not pasting in WezTerm.
- **First look**: `src/text_inserter.py` — Linux paste path uses `_is_active_window_terminal()` to choose between `Ctrl+Shift+V` (terminals) and `Ctrl+V` (GUI apps). WezTerm was already listed in `TERMINAL_WM_CLASSES` as `"wezterm-gui"`.
- **Discovery**: Ran `xdotool search --class "wezterm"` and `xprop -id <id> WM_CLASS` on the live WezTerm window. Actual WM_CLASS: `"org.wezfurlong.wezterm"` — not `"wezterm-gui"`. The lookup was silently failing, falling back to `Ctrl+V`, which WezTerm ignores for paste.

### 2. Fix

- Changed `"wezterm-gui"` → `"org.wezfurlong.wezterm"` in `TERMINAL_WM_CLASSES` (`src/text_inserter.py:19`).
- One-line fix, no logic changes needed.

### 3. Rebuild

- Build system calls `uv run pyinstaller` / `.venv/bin/pyinstaller`, both fail.
- **Root cause**: The venv was installed when project was at `/home/robert/Dev/push-to-talk_custom/`. It was later moved to `/home/robert/Dev/My_Setup/push-to-talk_custom/`. All `~/.venv/bin/` scripts have stale shebangs pointing to the old path.
- **Workaround**: `build_linux.sh` also didn't exist. Ran PyInstaller directly as a module:
  ```bash
  .venv/bin/python3 -m PyInstaller PushToTalk.spec
  ```
- Build succeeded. `dist/PushToTalk` updated.

---

## Current Technical State

- **Terminal detection** (`src/text_inserter.py`): Uses `xdotool getactivewindow` + `xprop WM_CLASS` to check against `TERMINAL_WM_CLASSES`. WezTerm now correctly identified.
- **Paste paths**: Ctrl+Shift+V for terminals, Ctrl+V for GUI apps, Cmd+V for macOS.
- **Binary**: `dist/PushToTalk` is up to date with the fix.
- **Build**: Use `.venv/bin/python3 -m PyInstaller PushToTalk.spec` — do not use `uv run pyinstaller` or `.venv/bin/pyinstaller` directly until the venv is rebuilt at the new path.

---

## Files Changed

### Modified
| File | What Changed |
|------|-------------|
| `src/text_inserter.py` | `"wezterm-gui"` → `"org.wezfurlong.wezterm"` in `TERMINAL_WM_CLASSES` |
| `build_script/build_linux.sh` | chmod +x only (mode change, no content change) |

---

## Problems Faced & Solutions

| Problem | Solution |
|---------|----------|
| WezTerm paste silently failed | WM_CLASS was `"org.wezfurlong.wezterm"`, not `"wezterm-gui"` — corrected lookup table |
| `uv run pyinstaller` fails | Stale venv shebang from old project path — use `python3 -m PyInstaller` instead |
| `build_linux.sh` missing | Ran PyInstaller directly rather than via build script |

---

## Next Session Action Plan

1. **Test WezTerm paste** with the new binary — confirm fix works end-to-end.
2. **Add Groq STT provider** — fully mapped in claude-mem (see observations 2272–2281). Key steps: `transcription_groq.py`, factory `if/elif`, `groq_api_key` in config + GUI.
3. **Fix venv shebangs** (optional, low priority) — rebuild venv at current path so build tooling works cleanly: `rm -rf .venv && uv sync --dev`.

---

## Roadmap

### Completed (This Session)
- [x] Fix WezTerm paste (WM_CLASS mismatch in terminal detection)
- [x] Rebuild binary with fix

### Unchanged Backlog
- [ ] Groq STT provider integration
- [ ] Fix stale venv shebangs (rebuild venv at new path)

---

## Quick Commands
```bash
cd /home/robert/Dev/My_Setup/push-to-talk_custom

# Run the app
./dist/PushToTalk

# Build (correct method)
.venv/bin/python3 -m PyInstaller PushToTalk.spec

# Verify WezTerm WM_CLASS on any window
xprop -id $(xdotool getactivewindow) WM_CLASS
```
