# Task List

## Done
- [x] Fix WezTerm paste (WM_CLASS mismatch) — 2026-04-09
- [x] Add terminal Ctrl+Shift+V detection — prior session
- [x] Migrate paste from pynput to xdotool — prior session
- [x] Add Warp terminal support — prior session
- [x] Add Windows platform support to text insertion — prior session
- [x] Language selector for transcription — v1.1.0

## Backlog
- [ ] **Groq STT provider** — Architecture fully mapped in claude-mem observations. Requires: new `transcription_groq.py`, factory update, config field `groq_api_key`, GUI combobox + API key input, model list. Use `groq` Python SDK. Default model: `whisper-large-v3`.
- [ ] Fix venv shebang stale paths — rebuild venv at `/home/robert/Dev/My_Setup/push-to-talk_custom/` so `.venv/bin/pyinstaller` works directly again.
