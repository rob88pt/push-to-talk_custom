# Changelog

## [2026-04-16] - Resilience: Transcription Retry + Refinement Timeout

### Added
- `src/transcription_openai.py`: Retry loop (5 attempts, 3s delay). 4xx HTTP errors skip retries immediately. After all attempts exhausted, raises last error.
- `src/push_to_talk.py`: `notify-send` critical notification when transcription fails after all retries.
- `src/push_to_talk.py`: Text refinement 5s timeout using `_RealThread.join(timeout=5)`. Falls back to raw transcription on timeout.
- `src/push_to_talk.py`: `notify-send` normal notification (auto-dismiss 4s) when refinement times out.
- `src/config/constants.py`: `TEXT_REFINEMENT_TIMEOUT_SECONDS = 5.0`
- `tests/test_push_to_talk.py`: `TestRefinementTimeout` class with 2 tests (happy path + timeout path).
- `docs/superpowers/plans/2026-04-16-refinement-timeout.md`: Implementation plan.

### Fixed
- `build_script/build_linux.sh`: Changed `uv run pyinstaller` to `.venv/bin/python -m PyInstaller` to work around stale venv shebang.

### Decisions
- Used `_RealThread` (captured at module import time before test monkeypatching) instead of `ThreadPoolExecutor` — the executor uses `threading.Thread` internally, which conflicts with the test suite's `immediate_thread` fixture that patches `threading.Thread` globally.
- Refinement timeout notification uses `urgency=normal` + `-t 4000` (auto-dismiss). Transcription failure uses `urgency=critical` (persistent) since it's a harder failure.

### Problems & Solutions
- **Problem**: `uv run pyinstaller` fails with "No such file or directory" — venv shebang points to old relocated path.
- **Solution**: Use `python -m PyInstaller` directly; fixed `build_linux.sh`.
- **Problem**: App started without config after rebuild — launched from wrong directory.
- **Solution**: Config path is relative; must `cd dist/` before launching `./PushToTalk`.
- **Problem**: `ThreadPoolExecutor` caused test suite hangs when `immediate_thread` fixture was active.
- **Solution**: Capture real `Thread` class at import time as `_RealThread`, use `.join(timeout=)` directly.

### Files Affected
- `src/transcription_openai.py` — retry logic
- `src/push_to_talk.py` — timeout + notifications
- `src/config/constants.py` — new constant
- `tests/test_push_to_talk.py` — timeout tests
- `build_script/build_linux.sh` — PyInstaller fix

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
