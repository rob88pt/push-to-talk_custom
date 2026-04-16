# Task List

## Done
- [x] Fix WezTerm paste (WM_CLASS mismatch) — 2026-04-09
- [x] Add terminal Ctrl+Shift+V detection — prior session
- [x] Migrate paste from pynput to xdotool — prior session
- [x] Add Warp terminal support — prior session
- [x] Add Windows platform support to text insertion — prior session
- [x] Language selector for transcription — v1.1.0
- [x] OpenAI transcription retry (5 attempts, 3s delay, skip 4xx) — 2026-04-16
- [x] Desktop notification on transcription failure — 2026-04-16
- [x] Text refinement 5s timeout with fallback to raw transcription — 2026-04-16
- [x] Desktop notification on refinement timeout (auto-dismiss 4s) — 2026-04-16
- [x] Fix `build_script/build_linux.sh` to use `python -m PyInstaller` — 2026-04-16

## Backlog
- [ ] **Groq STT provider** — Architecture fully mapped in claude-mem observations. Requires: new `transcription_groq.py`, factory update, config field `groq_api_key`, GUI combobox + API key input, model list. Use `groq` Python SDK. Default model: `whisper-large-v3`.
- [ ] Fix venv shebang stale paths — rebuild venv at `/home/robert/Dev/My_Setup/push-to-talk_custom/` so `.venv/bin/pyinstaller` works directly again.
