# Refinement Timeout Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** If text refinement takes longer than 5 seconds, fall back to the raw transcription output instead of waiting indefinitely.

**Architecture:** Wrap the `refine_text()` call in `_process_audio_background()` with a `concurrent.futures.ThreadPoolExecutor` future that has a 5-second timeout. On `TimeoutError`, log a warning and use the transcribed text directly. The refiner thread is abandoned (not killed — Python threads can't be killed mid-execution) but the main pipeline proceeds immediately.

**Tech Stack:** Python `concurrent.futures` (stdlib), existing `loguru` logger, existing `constants.py` pattern.

---

### Task 1: Add timeout constant

**Files:**
- Modify: `src/config/constants.py`

- [ ] **Step 1: Add the constant**

Open `src/config/constants.py` and add after the `TEXT_REFINEMENT_MIN_LENGTH` block (around line 104):

```python
TEXT_REFINEMENT_TIMEOUT_SECONDS = 5.0
"""Maximum time (in seconds) to wait for text refinement before falling back to raw transcription.

Rationale: LLM refinement occasionally stalls or takes 30+ seconds due to slow API responses.
Rather than blocking insertion, we fall back to the unrefined transcription after this timeout.
"""
```

- [ ] **Step 2: Commit**

```bash
git add src/config/constants.py
git commit -m "feat: add TEXT_REFINEMENT_TIMEOUT_SECONDS constant (5s)"
```

---

### Task 2: Write failing tests for timeout behaviour

**Files:**
- Modify: `tests/test_push_to_talk.py`

- [ ] **Step 1: Write the failing tests**

Add these two tests to `tests/test_push_to_talk.py`. Find an existing test class or add at the bottom of the file:

```python
import time
import concurrent.futures
from unittest.mock import MagicMock, patch


class TestRefinementTimeout:
    """Tests for text refinement timeout fallback."""

    def _make_app(self, mocker):
        """Build a minimal PushToTalk instance with mocked dependencies."""
        from src.push_to_talk import PushToTalk
        from src.config.push_to_talk_config import PushToTalkConfig

        mocker.patch("src.push_to_talk.HotkeyService")
        mocker.patch("src.push_to_talk.AudioRecorder")
        mocker.patch("src.push_to_talk.TextInserter")
        mocker.patch("src.push_to_talk.TranscriberFactory")
        mocker.patch("src.push_to_talk.TextRefinerFactory")

        app = PushToTalk.__new__(PushToTalk)
        app.config = PushToTalkConfig()
        app.config.enable_text_refinement = True
        app.processing_threads = []

        mock_inserter = MagicMock()
        mock_inserter.insert_text.return_value = True
        app.text_inserter = mock_inserter

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe_audio.return_value = "raw transcription"
        app.transcriber = mock_transcriber

        return app

    def test_refinement_within_timeout_uses_refined_text(self, mocker, tmp_path):
        """When refinement completes within 5s, use the refined result."""
        app = self._make_app(mocker)

        mock_refiner = MagicMock()
        mock_refiner.refine_text.return_value = "refined text"
        app.text_refiner = mock_refiner

        # Create a real dummy wav file so validation passes
        audio_file = str(tmp_path / "test.wav")
        import wave, struct
        with wave.open(audio_file, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))  # 1s silence

        app._process_audio_background(audio_file)

        app.text_inserter.insert_text.assert_called_once_with("refined text")

    def test_refinement_exceeding_timeout_uses_raw_transcription(self, mocker, tmp_path):
        """When refinement exceeds 5s, fall back to raw transcription without waiting."""
        app = self._make_app(mocker)

        def slow_refine(text):
            time.sleep(10)  # way beyond the 5s timeout
            return "should never be used"

        mock_refiner = MagicMock()
        mock_refiner.refine_text.side_effect = slow_refine
        app.text_refiner = mock_refiner

        audio_file = str(tmp_path / "test.wav")
        import wave, struct
        with wave.open(audio_file, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))

        start = time.time()
        app._process_audio_background(audio_file)
        elapsed = time.time() - start

        # Should complete well under 10s (the slow_refine duration)
        assert elapsed < 8, f"Expected early exit, took {elapsed:.1f}s"
        app.text_inserter.insert_text.assert_called_once_with("raw transcription")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/robert/Dev/My_Setup/push-to-talk_custom
.venv/bin/pytest tests/test_push_to_talk.py::TestRefinementTimeout -v
```

Expected: both tests FAIL (timeout logic does not exist yet).

---

### Task 3: Implement the timeout in `_process_audio_background`

**Files:**
- Modify: `src/push_to_talk.py`

- [ ] **Step 1: Add the import**

At the top of `src/push_to_talk.py`, add `concurrent.futures` to the stdlib imports:

```python
import concurrent.futures
```

Also add `TEXT_REFINEMENT_TIMEOUT_SECONDS` to the constants import. Find the line:

```python
from src.config.constants import (
```

and add `TEXT_REFINEMENT_TIMEOUT_SECONDS` to that block (exact list of names already imported will vary — just append it).

- [ ] **Step 2: Replace the refinement block**

In `_process_audio_background`, find the refinement block (around line 695-708):

```python
            # Refine text if enabled (1-2 seconds, runs in background)
            final_text = transcribed_text
            if self.text_refiner and self.config.enable_text_refinement:
                logger.info("Refining transcribed text...")
                try:
                    refined_text = self.text_refiner.refine_text(transcribed_text)
                    if refined_text:
                        final_text = refined_text
                        logger.info(f"Refined: {final_text}")
                except (TextRefinementError, APIError) as e:
                    logger.error(
                        f"Text refinement failed, using original transcription: {e}"
                    )
                    final_text = transcribed_text
```

Replace it with:

```python
            # Refine text if enabled, with a timeout fallback
            final_text = transcribed_text
            if self.text_refiner and self.config.enable_text_refinement:
                logger.info("Refining transcribed text...")
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(self.text_refiner.refine_text, transcribed_text)
                try:
                    refined_text = future.result(timeout=TEXT_REFINEMENT_TIMEOUT_SECONDS)
                    if refined_text:
                        final_text = refined_text
                        logger.info(f"Refined: {final_text}")
                except concurrent.futures.TimeoutError:
                    logger.warning(
                        f"Text refinement timed out after {TEXT_REFINEMENT_TIMEOUT_SECONDS}s, "
                        "using original transcription"
                    )
                except (TextRefinementError, APIError) as e:
                    logger.error(
                        f"Text refinement failed, using original transcription: {e}"
                    )
                finally:
                    executor.shutdown(wait=False)
```

- [ ] **Step 3: Run the tests**

```bash
.venv/bin/pytest tests/test_push_to_talk.py::TestRefinementTimeout -v
```

Expected: both tests PASS.

- [ ] **Step 4: Run the full test suite to check for regressions**

```bash
.venv/bin/pytest --tb=short -q
```

Expected: all previously passing tests still pass.

- [ ] **Step 5: Commit**

```bash
git add src/push_to_talk.py src/config/constants.py tests/test_push_to_talk.py
git commit -m "feat: fall back to raw transcription if refinement exceeds 5s"
```

---

### Task 4: Rebuild and restart

**Files:** none (build artefact)

- [ ] **Step 1: Build**

```bash
cd /home/robert/Dev/My_Setup/push-to-talk_custom
.venv/bin/python -m PyInstaller --name PushToTalk --onefile --noconsole --clean \
  --add-data "src:src" --add-data "icon.ico:." main.py
```

Expected last line: `Build complete! The results are available in: .../dist`

- [ ] **Step 2: Restart the app**

```bash
pkill -f dist/PushToTalk || true
sleep 1
DISPLAY=:0 nohup bash -c 'cd /home/robert/Dev/My_Setup/push-to-talk_custom/dist && ./PushToTalk' </dev/null >/dev/null 2>&1 &
```

- [ ] **Step 3: Verify running**

```bash
sleep 2 && ps aux | grep PushToTalk | grep -v grep
```

Expected: process running from `dist/` directory.
