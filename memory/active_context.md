# Active Context

## Current Focus
WezTerm paste fix shipped and binary rebuilt. Project is in a working state.

## Last Completed
- Fixed WezTerm terminal detection: `TERMINAL_WM_CLASSES` had `"wezterm-gui"` but WezTerm's actual WM_CLASS is `"org.wezfurlong.wezterm"`. This caused silent fallback to Ctrl+V instead of Ctrl+Shift+V, which WezTerm ignores.
- Rebuilt binary: `dist/PushToTalk` updated.

## Build Note
PyInstaller venv scripts have a stale shebang pointing to the old project path (`/home/robert/Dev/push-to-talk_custom/`). Always build with:
```bash
.venv/bin/python3 -m PyInstaller PushToTalk.spec
```
Do NOT use `.venv/bin/pyinstaller` directly or `uv run pyinstaller`.

## Immediate Next Steps
- (From prior sessions) Add Groq as an STT provider — architecture is fully mapped, see memory notes.

## Open Questions / Blockers
- None currently.
