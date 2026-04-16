# Changelog Summary

## Milestones

### v1.1.0 (prior sessions)
- Transcription language selector added
- OpenAI pipeline improved
- Versioned executable build

### WezTerm Paste Fix (2026-04-09)
- Terminal detection corrected for WezTerm (`org.wezfurlong.wezterm`)
- All terminal paste now works correctly across: gnome-terminal, kitty, Alacritty, WezTerm, Warp, and others

## Key Architectural Decisions
- Terminal detection uses `xdotool getactivewindow` + `xprop WM_CLASS` on Linux
- Two paste paths: Ctrl+Shift+V for terminals, Ctrl+V for GUI apps
- Build: always use `.venv/bin/python3 -m PyInstaller PushToTalk.spec` (venv shebang stale)

### Resilience Update (2026-04-16)
- OpenAI transcription: 5 retries with 3s delay, skip 4xx immediately
- Text refinement: 5s timeout, falls back to raw transcription
- Both failures trigger desktop notifications (critical / normal+auto-dismiss)
- Build script fixed: uses `python -m PyInstaller` instead of broken `uv run pyinstaller`

## Key Architectural Decisions
- Terminal detection uses `xdotool getactivewindow` + `xprop WM_CLASS` on Linux
- Two paste paths: Ctrl+Shift+V for terminals, Ctrl+V for GUI apps
- Build: always use `.venv/bin/python -m PyInstaller ...` (venv shebang stale); `build_linux.sh` is now fixed
- Refinement timeout uses `_RealThread` (captured pre-import) not `ThreadPoolExecutor` — avoids test fixture conflicts
- App must be launched from `dist/` directory — config path is relative

## Pending Backlog
- Groq STT provider integration (architecture fully mapped, not yet implemented)
