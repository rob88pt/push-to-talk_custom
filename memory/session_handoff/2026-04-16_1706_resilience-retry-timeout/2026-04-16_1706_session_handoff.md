# push-to-talk_custom - Session Handoff

**Date**: 2026-04-16
**Location**: `/home/robert/Dev/My_Setup/push-to-talk_custom`
**Session Goal**: Improve resilience of the audio transcription pipeline — add retry logic for transient API failures and a timeout fallback for slow LLM refinement, both with desktop notifications.

---

## Chronological Narrative

### 1. Log Investigation

The session started with checking recent logs after a transcription failure. The log showed:

```
ERROR | src.transcription_openai: OpenAI API error during transcription: Connection error.
WARNING | src.push_to_talk: Transcribed text is None, skipping refinement
```

The user had briefly lost Wi-Fi. The failure was silent — no notification, no retry.

### 2. Transcription Retry Logic

Added 5-attempt retry loop with 3-second delays to `OpenAITranscriber.transcribe_audio()`. Key design choice: 4xx HTTP errors (auth/bad request) skip retries immediately — only transient errors (connection, server 5xx) retry. After all attempts exhausted, raises the last error to the caller.

Also added a `notify-send -u critical` desktop notification in `_process_audio_background` when transcription ultimately fails — so the user knows the audio was lost.

### 3. Build and Restart

Rebuilding was needed to test. Discovered `build_linux.sh` uses `uv run pyinstaller` which fails because the venv shebang points to the old relocated project path (`/home/robert/Dev/push-to-talk_custom/` instead of `.../My_Setup/push-to-talk_custom/`). Fixed the build script to use `.venv/bin/python -m PyInstaller` directly.

After rebuild, app started without configuration. Root cause: config file is `push_to_talk_config.json` at a relative path, and the binary was launched from the project root instead of `dist/`. Fixed by always `cd dist/ && ./PushToTalk`.

### 4. Refinement Timeout Discovery

After the retry fix, a separate issue appeared in the logs: Cerebras refinement occasionally taking 34 seconds (also seen previously with Gemini at 33.89s). During that 34s wait, the next recording had already been inserted, then the slow refiner completed and overwrote the clipboard with its result.

### 5. Refinement Timeout Implementation

Planned and implemented a 5-second timeout on `refine_text()`. Plan at `docs/superpowers/plans/2026-04-16-refinement-timeout.md`.

**Key discovery**: The plan specified `concurrent.futures.ThreadPoolExecutor`, but this caused the test suite to hang. Root cause: the test fixture `immediate_thread` patches `threading.Thread` globally to run synchronously, which also affects `ThreadPoolExecutor`'s internal worker thread — causing it to deadlock. The implementer subagent solved this by capturing the real `Thread` class at module import time (before any test patching):

```python
from threading import Thread as _RealThread
```

Then using `_RealThread.join(timeout=5)` directly. This is functionally equivalent and immune to test fixture interference.

Added a `notify-send -u normal -t 4000` (auto-dismiss after 4s) notification on timeout.

### 6. Subagent Model Note

During subagent-driven development, Task 1 was dispatched using the haiku model. User requested to never use haiku for subagents going forward.

---

## Current Technical State

- **Transcription**: OpenAI API with 5 retries, 3s delay, skip on 4xx. Critical notification on total failure.
- **Refinement**: LLM refinement with 5s hard timeout. Falls back to raw transcription. Normal auto-dismiss notification on timeout. Uses `_RealThread` (module-level capture) + `.join(timeout=5)`.
- **Build**: `build_linux.sh` fixed — uses `.venv/bin/python -m PyInstaller`. App must be launched from `dist/` directory.
- **Tests**: 244/245 passing. 1 pre-existing unrelated failure in `test_config_gui.py`. New `TestRefinementTimeout` class with 2 tests.

---

## Files Changed

### Created
| File | Purpose |
|------|---------|
| `docs/superpowers/plans/2026-04-16-refinement-timeout.md` | Implementation plan for refinement timeout |
| `tests/test_push_to_talk.py` (class added) | `TestRefinementTimeout` — 2 tests for timeout feature |

### Modified
| File | What Changed |
|------|-------------|
| `src/transcription_openai.py` | Added retry loop (5 attempts, 3s delay, skip 4xx) |
| `src/push_to_talk.py` | Transcription failure notification; refinement timeout with `_RealThread`; timeout notification; removed unused `concurrent.futures` import |
| `src/config/constants.py` | Added `TEXT_REFINEMENT_TIMEOUT_SECONDS = 5.0` |
| `build_script/build_linux.sh` | Changed `uv run pyinstaller` to `.venv/bin/python -m PyInstaller` |

### Key Reference Files
| File | Why It Matters |
|------|---------------|
| `src/push_to_talk.py:698-724` | Refinement timeout block |
| `src/transcription_openai.py:48-110` | Retry loop implementation |
| `src/config/constants.py` | `TEXT_REFINEMENT_TIMEOUT_SECONDS` |

---

## Problems Faced & Solutions

| Problem | Solution |
|---------|----------|
| `uv run pyinstaller` fails — stale shebang | Use `.venv/bin/python -m PyInstaller`; fixed `build_linux.sh` |
| App starts without config after rebuild | Must launch from `dist/` directory (relative config path) |
| `ThreadPoolExecutor` hangs in tests with `immediate_thread` fixture | Capture real Thread at import time as `_RealThread`; use `.join(timeout=)` |
| Slow refiner (34s) overwrites clipboard after next recording | 5s timeout now prevents this entirely |

---

## Next Session Action Plan

1. **Groq STT provider** — Architecture fully mapped in claude-mem (obs 2275-2281). Requires: `transcription_groq.py`, factory update, `groq_api_key` config field, GUI combobox + API key input, model dropdown entries.
2. **Fix venv shebang** — Rebuild venv in correct location so `.venv/bin/pyinstaller` works directly. Low priority since `build_linux.sh` is now fixed.

---

## Roadmap

### Completed (This Session)
- [x] OpenAI transcription retry (5 attempts, 3s delay, skip 4xx)
- [x] Desktop notification on transcription failure
- [x] Text refinement 5s timeout with raw transcription fallback
- [x] Desktop notification on refinement timeout (auto-dismiss 4s)
- [x] Fixed `build_linux.sh` PyInstaller invocation
- [x] Rebuilt and restarted app

### Unchanged Backlog (Pre-existing)
- [ ] Groq STT provider integration
- [ ] Fix venv shebang stale paths

---

## Quick Commands

```bash
cd /home/robert/Dev/My_Setup/push-to-talk_custom

# Run timeout tests
.venv/bin/python -m pytest tests/test_push_to_talk.py::TestRefinementTimeout -v

# Build
.venv/bin/python -m PyInstaller --name PushToTalk --onefile --noconsole --clean \
  --add-data "src:src" --add-data "icon.ico:." main.py

# Restart app (must cd to dist/)
kill $(pgrep -f dist/PushToTalk) 2>/dev/null; sleep 1
DISPLAY=:0 nohup bash -c 'cd dist && ./PushToTalk' </dev/null >/dev/null 2>&1 &

# Check logs
tail -50 dist/push_to_talk.log
```
