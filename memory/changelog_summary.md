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

## Pending Backlog
- Groq STT provider integration (architecture fully mapped, not yet implemented)
