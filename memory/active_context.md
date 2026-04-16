# Active Context

## Current Focus
Resilience improvements shipped: retry logic for transcription failures + 5s timeout for text refinement with desktop notifications. Binary rebuilt and running.

## Last Completed
- **OpenAI transcription retry**: 5 attempts with 3s delay. 4xx errors fail immediately (no retry). On exhaustion raises last error and fires a critical `notify-send` notification.
- **Refinement timeout fallback**: If `refine_text()` takes >5s, the raw transcription is inserted instead. Uses `_RealThread` (captured before test monkeypatching) + `.join(timeout=5)`. On timeout fires a normal `notify-send` auto-dismissed after 4s.
- **Build script fixed**: `build_script/build_linux.sh` now uses `.venv/bin/python -m PyInstaller` instead of broken `uv run pyinstaller`.
- **App restart procedure**: Must launch from `dist/` directory (config file is relative path there).

## Build Note
PyInstaller venv scripts have a stale shebang. Always build with:
```bash
.venv/bin/python -m PyInstaller --name PushToTalk --onefile --noconsole --clean \
  --add-data "src:src" --add-data "icon.ico:." main.py
```
`build_script/build_linux.sh` is now fixed to do this automatically.

## Launch Note
Config file lives in `dist/`. Must launch from there:
```bash
DISPLAY=:0 nohup bash -c 'cd .../dist && ./PushToTalk' </dev/null >/dev/null 2>&1 &
```

## Immediate Next Steps
- (From prior sessions) Add Groq as an STT provider — architecture is fully mapped, see memory notes.

## Open Questions / Blockers
- None currently.
