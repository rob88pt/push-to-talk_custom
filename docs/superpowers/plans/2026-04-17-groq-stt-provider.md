# Groq STT Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Groq as a first-class Speech-to-Text provider alongside OpenAI and Deepgram, using the `groq` Python SDK.

**Architecture:** New `GroqTranscriber` class mirrors `OpenAITranscriber` (same retry logic, same base class), registered in `TranscriberFactory`. Config, GUI, and validator all extended with one new `groq_api_key` field and `"groq"` provider string following the exact same patterns as the existing providers.

**Tech Stack:** `groq` Python SDK (new dep), existing Pydantic model, tkinter GUI, pytest + pytest-mock.

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `pyproject.toml` | Modify | Add `groq>=0.30.0` dependency |
| `src/transcription_groq.py` | **Create** | `GroqTranscriber` class |
| `src/transcriber_factory.py` | Modify | Import + `elif provider == "groq"` |
| `src/push_to_talk.py` | Modify | `groq_api_key` field, validator, 3 dispatch points |
| `src/gui/validators.py` | Modify | `validate_groq_api_key()`, update `validate_configuration()` |
| `src/gui/api_section.py` | Modify | Groq API key row, dropdown, model list, get/set/test |
| `src/gui/configuration_window.py` | Modify | Pass `groq_api_key` in `_get_config_from_sections()` and `_update_sections_from_config()` |
| `tests/test_transcription_groq.py` | **Create** | `TestGroqTranscriber` unit tests |
| `tests/test_transcriber_factory.py` | Modify | Add Groq factory tests |

---

## Task 1: Add `groq` dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the dependency**

Edit `pyproject.toml`, add `groq>=0.30.0` to the `dependencies` list (after `openai`):

```toml
dependencies = [
    "deepgram-sdk>=3.9.0",
    "loguru>=0.7.2",
    "openai>=1.97.1",
    "groq>=0.30.0",
    "pyaudio>=0.2.14",
    "pydantic>=2.0.0",
    "pyperclip>=1.9.0",
    "playsound3>=3.2.4",
    "pynput>=1.7.7",
    "cerebras-cloud-sdk>=1.59.0",
    "google-genai>=1.0.0",
]
```

- [ ] **Step 2: Install the dependency**

```bash
uv sync
```

Expected: output shows `groq` package resolved and installed, no errors.

- [ ] **Step 3: Verify import works**

```bash
.venv/bin/python -c "import groq; print(groq.__version__)"
```

Expected: prints a version string like `0.30.0` with no errors.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add groq Python SDK"
```

---

## Task 2: Create `GroqTranscriber`

**Files:**
- Create: `src/transcription_groq.py`
- Create: `tests/test_transcription_groq.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_transcription_groq.py`:

```python
import pytest
import os
from unittest.mock import MagicMock
from loguru import logger

from src.transcription_groq import GroqTranscriber
from src.exceptions import ConfigurationError, TranscriptionError, APIError


class TestGroqTranscriber:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        mocker.patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"})
        # Patch groq.Groq so no real client is created
        self.mock_groq_class = mocker.patch("src.transcription_groq.groq.Groq")
        self.mock_client = MagicMock()
        self.mock_groq_class.return_value = self.mock_client
        self.transcriber = GroqTranscriber()

    def test_initialization_with_env_var(self, mocker):
        mocker.patch.dict(os.environ, {"GROQ_API_KEY": "env-groq-key"})
        mock_class = mocker.patch("src.transcription_groq.groq.Groq")
        t = GroqTranscriber()
        assert t.api_key == "env-groq-key"
        assert t.model == "whisper-large-v3-turbo"
        mock_class.assert_called_once_with(api_key="env-groq-key")

    def test_initialization_with_explicit_key(self, mocker):
        mock_class = mocker.patch("src.transcription_groq.groq.Groq")
        t = GroqTranscriber(api_key="explicit-key", model="whisper-large-v3")
        assert t.api_key == "explicit-key"
        assert t.model == "whisper-large-v3"

    def test_initialization_no_api_key(self, mocker):
        mocker.patch.dict(os.environ, {}, clear=True)
        mocker.patch("src.transcription_groq.groq.Groq")
        with pytest.raises(ConfigurationError, match="Groq API key is required"):
            GroqTranscriber()

    def test_transcribe_audio_success(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "Hello world"
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav")
        assert result == "Hello world"
        self.mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = self.mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["model"] == "whisper-large-v3-turbo"

    def test_transcribe_audio_with_language(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "Bonjour"
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav", language="fr")
        assert result == "Bonjour"
        call_kwargs = self.mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["language"] == "fr"

    def test_transcribe_audio_file_not_found(self, mocker):
        mocker.patch("os.path.exists", return_value=False)
        result = self.transcriber.transcribe_audio("nonexistent.wav")
        assert result is None
        self.mock_client.audio.transcriptions.create.assert_not_called()

    def test_transcribe_audio_empty_response(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = ""
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav")
        assert result is None

    def test_transcribe_audio_whitespace_response(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "   \n  "
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.transcriber.transcribe_audio("test.wav")
        assert result is None

    def test_retry_on_transient_error_then_success(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("time.sleep")  # don't actually wait 3s in tests

        transient_error = Exception("Connection reset")
        mock_response = MagicMock()
        mock_response.text = "Retry succeeded"
        self.mock_client.audio.transcriptions.create.side_effect = [
            transient_error,
            mock_response,
        ]

        result = self.transcriber.transcribe_audio("test.wav")
        assert result == "Retry succeeded"
        assert self.mock_client.audio.transcriptions.create.call_count == 2

    def test_no_retry_on_4xx_error(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("time.sleep")

        import groq as groq_module
        err = groq_module.APIStatusError(
            "Unauthorized",
            response=MagicMock(status_code=401),
            body=None,
        )
        err.status_code = 401
        self.mock_client.audio.transcriptions.create.side_effect = err

        with pytest.raises(APIError):
            self.transcriber.transcribe_audio("test.wav")
        assert self.mock_client.audio.transcriptions.create.call_count == 1

    def test_raises_after_all_retries_exhausted(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("time.sleep")

        self.mock_client.audio.transcriptions.create.side_effect = Exception("Network down")

        with pytest.raises(TranscriptionError):
            self.transcriber.transcribe_audio("test.wav")
        assert self.mock_client.audio.transcriptions.create.call_count == 5

    def test_glossary_passed_as_prompt(self, mocker):
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"audio"))
        mocker.patch("os.path.exists", return_value=True)

        mock_response = MagicMock()
        mock_response.text = "Result"
        self.mock_client.audio.transcriptions.create.return_value = mock_response

        self.transcriber.set_glossary(["foo", "bar"])
        self.transcriber.transcribe_audio("test.wav")

        call_kwargs = self.mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["prompt"] == "foo, bar"
```

- [ ] **Step 2: Run the tests — verify they fail**

```bash
.venv/bin/python -m pytest tests/test_transcription_groq.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'src.transcription_groq'` or similar import error.

- [ ] **Step 3: Create `src/transcription_groq.py`**

```python
import os
from loguru import logger
import time
from typing import Optional
import groq

from src.transcription_base import TranscriberBase
from src.utils import validate_audio_file_exists, validate_audio_duration
from src.exceptions import TranscriptionError, APIError

_MAX_RETRIES = 5
_RETRY_DELAY = 3  # seconds


class GroqTranscriber(TranscriberBase):
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-large-v3-turbo"):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        super().__init__(api_key, "Groq")
        self.model = model
        self.client = groq.Groq(api_key=self.api_key)

    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        if not validate_audio_file_exists(audio_file_path):
            return None
        if not validate_audio_duration(audio_file_path):
            return None

        start_time = time.time()
        logger.debug(f"Starting transcription for: {audio_file_path}")
        prompt = ", ".join(self.glossary) if self.glossary else None

        last_error: Exception = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Calling Groq transcription API (model: {self.model}, language: {language})"
                    + (f", attempt {attempt}/{_MAX_RETRIES}" if attempt > 1 else "")
                )
                with open(audio_file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language,
                        prompt=prompt,
                    )

                if not response or not response.text.strip():
                    logger.error("Groq transcription API returned empty response")
                    return None

                transcribed_text = response.text.strip()
                transcription_time = time.time() - start_time
                logger.info(
                    f"Transcription successful: {len(transcribed_text)} characters in {transcription_time:.2f}s"
                )
                return transcribed_text

            except groq.APIStatusError as e:
                last_error = APIError(
                    f"Groq transcription API failed: {e}",
                    provider="Groq",
                    status_code=e.status_code,
                )
                if 400 <= e.status_code < 500:
                    logger.error(f"Groq API client error (not retrying): {e}")
                    raise last_error from e
                logger.warning(f"Groq API error (attempt {attempt}/{_MAX_RETRIES}): {e}")
            except Exception as e:
                last_error = TranscriptionError(f"Failed to transcribe audio: {e}")
                logger.warning(f"Transcription error (attempt {attempt}/{_MAX_RETRIES}): {e}")

            if attempt < _MAX_RETRIES:
                logger.info(f"Retrying in {_RETRY_DELAY}s...")
                time.sleep(_RETRY_DELAY)

        logger.error(f"Transcription failed after {_MAX_RETRIES} attempts")
        raise last_error
```

- [ ] **Step 4: Run the tests — verify they pass**

```bash
.venv/bin/python -m pytest tests/test_transcription_groq.py -v
```

Expected: all 11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/transcription_groq.py tests/test_transcription_groq.py
git commit -m "feat: add GroqTranscriber with retry logic"
```

---

## Task 3: Register Groq in `TranscriberFactory`

**Files:**
- Modify: `src/transcriber_factory.py`
- Modify: `tests/test_transcriber_factory.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_transcriber_factory.py` inside `TestTranscriberFactory`:

```python
    def test_create_groq_transcriber(self, mocker):
        mocker.patch("src.transcription_groq.groq.Groq")
        transcriber = TranscriberFactory.create_transcriber(
            provider="groq", api_key="test-groq-key", model="whisper-large-v3-turbo"
        )
        from src.transcription_groq import GroqTranscriber
        assert isinstance(transcriber, GroqTranscriber)
        assert isinstance(transcriber, TranscriberBase)
        assert transcriber.api_key == "test-groq-key"
        assert transcriber.model == "whisper-large-v3-turbo"

    def test_create_groq_transcriber_alternative_model(self, mocker):
        mocker.patch("src.transcription_groq.groq.Groq")
        transcriber = TranscriberFactory.create_transcriber(
            provider="groq", api_key="test-key", model="whisper-large-v3"
        )
        from src.transcription_groq import GroqTranscriber
        assert isinstance(transcriber, GroqTranscriber)
        assert transcriber.model == "whisper-large-v3"

    def test_all_transcribers_implement_base_interface_includes_groq(self, mocker):
        mocker.patch("src.transcription_groq.groq.Groq")
        groq_transcriber = TranscriberFactory.create_transcriber(
            provider="groq", api_key="test-key", model="whisper-large-v3-turbo"
        )
        assert isinstance(groq_transcriber, TranscriberBase)
        assert hasattr(groq_transcriber, "transcribe_audio")
        assert callable(groq_transcriber.transcribe_audio)
```

- [ ] **Step 2: Run the new tests — verify they fail**

```bash
.venv/bin/python -m pytest tests/test_transcriber_factory.py::TestTranscriberFactory::test_create_groq_transcriber -v
```

Expected: `ValueError: Unknown transcription provider: groq`

- [ ] **Step 3: Update `src/transcriber_factory.py`**

```python
from typing import List, Optional
from src.transcription_base import TranscriberBase
from src.transcription_openai import OpenAITranscriber
from src.transcription_deepgram import DeepgramTranscriber
from src.transcription_groq import GroqTranscriber


class TranscriberFactory:
    """Factory for creating transcriber instances based on provider."""

    @staticmethod
    def create_transcriber(
        provider: str,
        api_key: str,
        model: str,
        glossary: Optional[List[str]] = None,
    ) -> TranscriberBase:
        """
        Create and return a transcriber instance.

        Args:
            provider: The transcription provider ("openai", "deepgram", or "groq")
            api_key: API key for the selected provider
            model: Model name to use for transcription
            glossary: Optional list of custom terms for improved recognition

        Returns:
            TranscriberBase instance for the selected provider

        Raises:
            ValueError: If an unknown provider is specified
        """
        if provider == "openai":
            transcriber = OpenAITranscriber(api_key=api_key, model=model)
        elif provider == "deepgram":
            transcriber = DeepgramTranscriber(api_key=api_key, model=model)
        elif provider == "groq":
            transcriber = GroqTranscriber(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unknown transcription provider: {provider}")

        if glossary:
            transcriber.set_glossary(glossary)

        return transcriber
```

- [ ] **Step 4: Run all factory tests**

```bash
.venv/bin/python -m pytest tests/test_transcriber_factory.py -v
```

Expected: all tests pass (including the 3 new Groq tests).

- [ ] **Step 5: Commit**

```bash
git add src/transcriber_factory.py tests/test_transcriber_factory.py
git commit -m "feat: register GroqTranscriber in TranscriberFactory"
```

---

## Task 4: Update `PushToTalkConfig` and dispatch points in `push_to_talk.py`

**Files:**
- Modify: `src/push_to_talk.py`

The config model, field validator, and two dispatch points all live in this file.

- [ ] **Step 1: Add `groq_api_key` field to `PushToTalkConfig`**

In `src/push_to_talk.py`, find the `PushToTalkConfig` class (line ~42). After `deepgram_api_key` (line ~52), add:

```python
    groq_api_key: str = Field(default="", description="Groq API key")
```

So the block reads:

```python
    openai_api_key: str = Field(default="", description="OpenAI API key")
    deepgram_api_key: str = Field(default="", description="Deepgram API key")
    groq_api_key: str = Field(default="", description="Groq API key")
    stt_model: str = Field(default="nova-3", description="STT model name")
```

- [ ] **Step 2: Update the `field_validator` for `stt_provider`**

Find `validate_stt_provider` (line ~110). Change:

```python
        if v not in ["openai", "deepgram"]:
            raise ValueError(f"stt_provider must be 'openai' or 'deepgram', got '{v}'")
```

To:

```python
        if v not in ["openai", "deepgram", "groq"]:
            raise ValueError(f"stt_provider must be 'openai', 'deepgram', or 'groq', got '{v}'")
```

- [ ] **Step 3: Update the startup API key validation block**

Find the `__init__` dispatch block (line ~221). Change:

```python
        if self.config.stt_provider == "openai":
            if not self.config.openai_api_key:
                self.config.openai_api_key = os.getenv("OPENAI_API_KEY")
                if not self.config.openai_api_key:
                    raise ConfigurationError(
                        "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide in config."
                    )
        elif self.config.stt_provider == "deepgram":
            if not self.config.deepgram_api_key:
                self.config.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
                if not self.config.deepgram_api_key:
                    raise ConfigurationError(
                        "Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable or provide in config."
                    )
        else:
            raise ConfigurationError(
                f"Unknown STT provider: {self.config.stt_provider}"
            )
```

To:

```python
        if self.config.stt_provider == "openai":
            if not self.config.openai_api_key:
                self.config.openai_api_key = os.getenv("OPENAI_API_KEY")
                if not self.config.openai_api_key:
                    raise ConfigurationError(
                        "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide in config."
                    )
        elif self.config.stt_provider == "deepgram":
            if not self.config.deepgram_api_key:
                self.config.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
                if not self.config.deepgram_api_key:
                    raise ConfigurationError(
                        "Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable or provide in config."
                    )
        elif self.config.stt_provider == "groq":
            if not self.config.groq_api_key:
                self.config.groq_api_key = os.getenv("GROQ_API_KEY")
                if not self.config.groq_api_key:
                    raise ConfigurationError(
                        "Groq API key is required. Set GROQ_API_KEY environment variable or provide in config."
                    )
        else:
            raise ConfigurationError(
                f"Unknown STT provider: {self.config.stt_provider}"
            )
```

- [ ] **Step 4: Update `_create_default_transcriber()`**

Find the method (line ~363). Change:

```python
        if self.config.stt_provider == "openai":
            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
        elif self.config.stt_provider == "deepgram":
            api_key = self.config.deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
        else:
            raise ConfigurationError(
                f"Unknown STT provider: {self.config.stt_provider}"
            )
```

To:

```python
        if self.config.stt_provider == "openai":
            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
        elif self.config.stt_provider == "deepgram":
            api_key = self.config.deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
        elif self.config.stt_provider == "groq":
            api_key = self.config.groq_api_key or os.getenv("GROQ_API_KEY")
        else:
            raise ConfigurationError(
                f"Unknown STT provider: {self.config.stt_provider}"
            )
```

- [ ] **Step 5: Run the existing test suite to confirm nothing broke**

```bash
.venv/bin/python -m pytest tests/test_push_to_talk.py -v 2>&1 | tail -20
```

Expected: same pass/fail counts as before (244/245 with the 1 pre-existing failure in test_config_gui.py).

- [ ] **Step 6: Commit**

```bash
git add src/push_to_talk.py
git commit -m "feat: add groq_api_key to PushToTalkConfig and dispatch points"
```

---

## Task 5: Add `validate_groq_api_key` and update `validate_configuration`

**Files:**
- Modify: `src/gui/validators.py`

- [ ] **Step 1: Add `validate_groq_api_key` to `validators.py`**

Append after `validate_gemini_api_key` in `src/gui/validators.py`:

```python
def validate_groq_api_key(api_key: str) -> bool:
    """
    Validate Groq API key by making a test request.

    Args:
        api_key: Groq API key to validate

    Returns:
        True if valid, False otherwise

    Raises:
        Exception: With descriptive error message
    """
    try:
        import groq

        client = groq.Groq(api_key=api_key)
        _ = client.models.list()
        return True
    except Exception as e:
        error_msg = str(e)
        if (
            "401" in error_msg
            or "invalid_api_key" in error_msg
            or "Authentication" in error_msg
            or "Unauthorized" in error_msg
        ):
            raise Exception("INVALID - Incorrect API key")
        elif "403" in error_msg or "Forbidden" in error_msg:
            raise Exception("INVALID - Access forbidden")
        elif "timeout" in error_msg.lower():
            raise Exception("TIMEOUT - Network issue")
        else:
            raise Exception(f"ERROR - {error_msg[:60]}...")
```

- [ ] **Step 2: Update `validate_configuration` to handle `"groq"`**

Find `validate_configuration` (line ~8). Change the existing `else` branch:

```python
    if config.stt_provider == "openai":
        if not config.openai_api_key.strip():
            return (
                False,
                "OpenAI API key is required when using OpenAI provider!\n\n"
                "Please enter your OpenAI API key or switch to Deepgram provider.",
            )
    elif config.stt_provider == "deepgram":
        if not config.deepgram_api_key.strip():
            return (
                False,
                "Deepgram API key is required when using Deepgram provider!\n\n"
                "Please enter your Deepgram API key or switch to OpenAI provider.",
            )
    else:
        return False, f"Unknown provider: {config.stt_provider}"
```

To:

```python
    if config.stt_provider == "openai":
        if not config.openai_api_key.strip():
            return (
                False,
                "OpenAI API key is required when using OpenAI provider!\n\n"
                "Please enter your OpenAI API key or switch to another provider.",
            )
    elif config.stt_provider == "deepgram":
        if not config.deepgram_api_key.strip():
            return (
                False,
                "Deepgram API key is required when using Deepgram provider!\n\n"
                "Please enter your Deepgram API key or switch to another provider.",
            )
    elif config.stt_provider == "groq":
        if not config.groq_api_key.strip():
            return (
                False,
                "Groq API key is required when using Groq provider!\n\n"
                "Please enter your Groq API key or switch to another provider.",
            )
    else:
        return False, f"Unknown provider: {config.stt_provider}"
```

- [ ] **Step 3: Run the full test suite**

```bash
.venv/bin/python -m pytest tests/ -v --ignore=tests/test_config_gui.py 2>&1 | tail -20
```

Expected: all tests pass (no new failures).

- [ ] **Step 4: Commit**

```bash
git add src/gui/validators.py
git commit -m "feat: add validate_groq_api_key and handle groq in validate_configuration"
```

---

## Task 6: Update GUI — `api_section.py` and `configuration_window.py`

**Files:**
- Modify: `src/gui/api_section.py`
- Modify: `src/gui/configuration_window.py`

This task has no unit tests (tkinter GUI). Verify manually at the end.

- [ ] **Step 1: Add Groq state variables in `APISection.__init__`**

In `src/gui/api_section.py`, find `__init__` (line ~17). After `self.gemini_api_key_var = tk.StringVar()` add:

```python
        self.groq_api_key_var = tk.StringVar()
```

After `self.custom_widgets = {}` add:

```python
        self.groq_widgets = {}
```

After `self.deepgram_stt_model = "nova-3"` add:

```python
        self.groq_stt_model = "whisper-large-v3-turbo"
```

- [ ] **Step 2: Add Groq API key row in `_create_widgets`**

In `_create_widgets`, find the Custom API Key Frame block (the last one, row=4). After it (before the `# === Speech-to-Text Settings Section ===` comment), insert:

```python
        # Groq API Key Frame
        self.groq_widgets["frame"] = ttk.Frame(self.api_keys_frame)
        self.groq_widgets["frame"].grid(
            row=5, column=0, columnspan=4, sticky="ew", pady=5
        )

        ttk.Label(self.groq_widgets["frame"], text="Groq API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        groq_api_key_entry = ttk.Entry(
            self.groq_widgets["frame"],
            textvariable=self.groq_api_key_var,
            show="*",
            width=50,
        )
        groq_api_key_entry.grid(
            row=0, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=2
        )

        def toggle_groq_key_visibility():
            if groq_api_key_entry["show"] == "*":
                groq_api_key_entry["show"] = ""
                groq_show_hide_btn["text"] = "Hide"
            else:
                groq_api_key_entry["show"] = "*"
                groq_show_hide_btn["text"] = "Show"

        groq_show_hide_btn = ttk.Button(
            self.groq_widgets["frame"],
            text="Show",
            command=toggle_groq_key_visibility,
            width=8,
        )
        groq_show_hide_btn.grid(row=0, column=3, padx=(5, 0), pady=2)
        self.groq_widgets["frame"].columnconfigure(1, weight=1)
```

- [ ] **Step 3: Add `"groq"` to the STT provider combobox**

Find the STT provider combobox creation (line ~261):

```python
        stt_provider_combo = ttk.Combobox(
            self.frame,
            textvariable=self.stt_provider_var,
            values=["openai", "deepgram"],
            state="readonly",
            width=20,
        )
```

Change `values=["openai", "deepgram"]` to `values=["openai", "deepgram", "groq"]`.

- [ ] **Step 4: Add Groq model list to `_update_stt_model_options`**

Find `_update_stt_model_options` (line ~436). Add after the `openai_models` and `deepgram_models` definitions:

```python
        groq_models = ["whisper-large-v3-turbo", "whisper-large-v3"]
```

In the same method, add the `elif provider_value == "groq":` branch after the `elif provider_value == "deepgram":` block:

```python
        elif provider_value == "groq":
            models = groq_models
            if self.groq_stt_model in models:
                self.stt_model_var.set(self.groq_stt_model)
            else:
                self.stt_model_var.set(models[0])
```

Also update the model-saving logic at the top of the method. After:

```python
        if current_model in openai_models:
            self.openai_stt_model = current_model
        elif current_model in deepgram_models:
            self.deepgram_stt_model = current_model
```

Add:

```python
        elif current_model in groq_models:
            self.groq_stt_model = current_model
```

- [ ] **Step 5: Add Groq to `_on_stt_model_changed`**

Find `_on_stt_model_changed` (line ~395). After:

```python
        elif provider_value == "deepgram":
            self.deepgram_stt_model = current_model
```

Add:

```python
        elif provider_value == "groq":
            self.groq_stt_model = current_model
```

- [ ] **Step 6: Add Groq to `_update_combobox_options_only`**

Find `_update_combobox_options_only` (line ~657). In the STT model options block, after `elif provider == "deepgram":` block add:

```python
            elif provider == "groq":
                models = ["whisper-large-v3-turbo", "whisper-large-v3"]
```

- [ ] **Step 7: Update `get_values`**

Find `get_values` (line ~563). Add `"groq_api_key"` to the returned dict:

```python
        return {
            "stt_provider": self.stt_provider_var.get(),
            "openai_api_key": self.openai_api_key_var.get().strip(),
            "deepgram_api_key": self.deepgram_api_key_var.get().strip(),
            "groq_api_key": self.groq_api_key_var.get().strip(),
            "cerebras_api_key": self.cerebras_api_key_var.get().strip(),
            "gemini_api_key": self.gemini_api_key_var.get().strip(),
            "custom_api_key": self.custom_api_key_var.get().strip(),
            "stt_model": self.stt_model_var.get(),
            "refinement_provider": self.refinement_provider_var.get(),
            "refinement_model": self.refinement_model_var.get(),
            "language": self.language_var.get(),
            "custom_endpoint": self.custom_endpoint_var.get().strip(),
        }
```

- [ ] **Step 8: Update `set_values` signature and body**

Find `set_values` (line ~584). Add `groq_api_key: str = ""` parameter after `deepgram_api_key`:

```python
    def set_values(
        self,
        stt_provider: str,
        openai_api_key: str,
        deepgram_api_key: str,
        groq_api_key: str,
        cerebras_api_key: str,
        gemini_api_key: str,
        custom_api_key: str,
        stt_model: str,
        refinement_provider: str,
        refinement_model: str,
        language: str = "auto",
        custom_endpoint: str = "",
    ):
```

In the body, after `self.deepgram_api_key_var.set(deepgram_api_key)` add:

```python
        self.groq_api_key_var.set(groq_api_key)
```

In the provider-specific model saving block, add:

```python
        elif stt_provider == "groq":
            self.groq_stt_model = stt_model
```

- [ ] **Step 9: Add Groq to `test_api_keys`**

Find `test_api_keys` in `api_section.py` (line ~714). Add a Groq block after the Deepgram block, following the same pattern. Import `validate_groq_api_key` at the top of the file:

Add to the imports at line 6:

```python
from src.gui.validators import (
    validate_openai_api_key,
    validate_deepgram_api_key,
    validate_groq_api_key,
    validate_cerebras_api_key,
    validate_gemini_api_key,
)
```

In `test_api_keys`, after the Deepgram block add:

```python
        # Test Groq
        groq_status = "Not configured"
        groq_prefix = "[ ]"
        if values["groq_api_key"]:
            try:
                validate_groq_api_key(values["groq_api_key"])
                groq_status = "VALID"
                groq_prefix = "[OK]"
            except Exception as e:
                groq_status = str(e)
                groq_prefix = "[X]"

        selected_marker = (
            " (Selected STT Model)" if values["stt_provider"] == "groq" else ""
        )
        status_lines.append(f"\n{groq_prefix} Groq{selected_marker}:")
        status_lines.append(f"  Status: {groq_status}")
        if values["groq_api_key"]:
            status_lines.append(
                f"  Key: {'*' * min(len(values['groq_api_key']), 20)}"
            )
```

Also add the Groq warning at the bottom of `test_api_keys` after the Deepgram warning:

```python
        elif values["stt_provider"] == "groq" and groq_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected STT provider (Groq) has an invalid API key!"
            )
```

- [ ] **Step 10: Update `configuration_window.py`**

In `src/gui/configuration_window.py`, find `_get_config_from_sections` (line ~333).

Add `groq_api_key=api_values["groq_api_key"],` after `deepgram_api_key`:

```python
        return PushToTalkConfig(
            stt_provider=api_values["stt_provider"],
            openai_api_key=api_values["openai_api_key"],
            deepgram_api_key=api_values["deepgram_api_key"],
            groq_api_key=api_values["groq_api_key"],
            cerebras_api_key=api_values["cerebras_api_key"],
            gemini_api_key=api_values["gemini_api_key"],
            custom_api_key=api_values["custom_api_key"],
            stt_model=api_values["stt_model"],
            refinement_provider=api_values["refinement_provider"],
            refinement_model=api_values["refinement_model"],
            language=api_values["language"],
            custom_endpoint=api_values["custom_endpoint"],
            hotkey=hotkey_values["hotkey"],
            toggle_hotkey=hotkey_values["toggle_hotkey"],
            enable_text_refinement=feature_values["enable_text_refinement"],
            enable_logging=feature_values["enable_logging"],
            enable_audio_feedback=feature_values["enable_audio_feedback"],
            debug_mode=feature_values["debug_mode"],
            custom_glossary=self.glossary_section.get_terms(),
            custom_refinement_prompt=self.prompt_section.get_prompt(),
        )
```

Find `_update_sections_from_config` (line ~361). Add `config.groq_api_key` after `config.deepgram_api_key`:

```python
            self.api_section.set_values(
                config.stt_provider,
                config.openai_api_key,
                config.deepgram_api_key,
                config.groq_api_key,
                config.cerebras_api_key,
                config.gemini_api_key,
                config.custom_api_key,
                config.stt_model,
                config.refinement_provider,
                config.refinement_model,
                config.language,
                config.custom_endpoint,
            )
```

- [ ] **Step 11: Run the full test suite**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/test_config_gui.py -v 2>&1 | tail -20
```

Expected: all tests pass.

- [ ] **Step 12: Commit**

```bash
git add src/gui/api_section.py src/gui/configuration_window.py
git commit -m "feat: add Groq to GUI — API key row, provider dropdown, model list"
```

---

## Task 7: Smoke test and rebuild

**Files:** none — verification only

- [ ] **Step 1: Run the full test suite including test_config_gui.py**

```bash
.venv/bin/python -m pytest tests/ -v 2>&1 | tail -30
```

Expected: 245+ tests, only the 1 pre-existing failure in `test_config_gui.py`.

- [ ] **Step 2: Build the binary**

```bash
cd /home/robert/Dev/My_Setup/push-to-talk_custom
.venv/bin/python -m PyInstaller --name PushToTalk --onefile --noconsole --clean \
  --add-data "src:src" --add-data "icon.ico:." main.py
```

Expected: completes without error, `dist/PushToTalk` exists.

- [ ] **Step 3: Launch and open settings**

```bash
kill $(pgrep -f dist/PushToTalk) 2>/dev/null; sleep 1
DISPLAY=:0 nohup bash -c 'cd dist && ./PushToTalk' </dev/null >/dev/null 2>&1 &
sleep 3
tail -20 dist/push_to_talk.log
```

Expected: no startup errors in log.

Open the Settings window and verify:
- STT Provider dropdown shows `openai`, `deepgram`, `groq`
- Selecting `groq` switches model dropdown to `whisper-large-v3-turbo` / `whisper-large-v3`
- A "Groq API Key" row exists in the API Keys section
- "Test API Keys" button shows a Groq block in the output

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: Groq STT provider — full integration complete"
```
