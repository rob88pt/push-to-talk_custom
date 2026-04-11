# Changelog

## [2026-04-09] - WezTerm Paste Fix

### Fixed
- `src/text_inserter.py`: Replaced `"wezterm-gui"` with `"org.wezfurlong.wezterm"` in `TERMINAL_WM_CLASSES`. WezTerm was not being detected as a terminal, so Ctrl+V was sent instead of Ctrl+Shift+V — WezTerm ignores Ctrl+V for paste.

### Problems & Solutions
- **Problem**: WezTerm paste silently failed — text was transcribed and refined correctly but never appeared.
- **Solution**: Ran `xdotool search --class "wezterm"` + `xprop -id <id> WM_CLASS` to discover the real WM_CLASS (`org.wezfurlong.wezterm`), then updated the lookup table.
- **Problem**: `uv run pyinstaller` and `.venv/bin/pyinstaller` both fail because venv was created at old path `/home/robert/Dev/push-to-talk_custom/` and shebang lines are stale.
- **Solution**: Use `python3 -m PyInstaller` to bypass the broken shebang: `.venv/bin/python3 -m PyInstaller PushToTalk.spec`

### Files Affected
- `src/text_inserter.py` — WM_CLASS correction
- `dist/PushToTalk` — rebuilt binary (not tracked in git)
