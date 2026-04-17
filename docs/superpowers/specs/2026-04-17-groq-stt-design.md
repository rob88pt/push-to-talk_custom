# Groq STT Provider — Design Spec

**Date**: 2026-04-17
**Status**: Approved

---

## Overview

Add Groq as a first-class Speech-to-Text provider alongside OpenAI and Deepgram. Groq runs Whisper models at extremely high speed (216x real-time for `whisper-large-v3-turbo`) via its own Python SDK (`groq` package), which uses a familiar OpenAI-compatible API shape.

---

## Approach

Dedicated `GroqTranscriber` class using the `groq` SDK. This is the canonical integration method and produces correct error types and log messages. The `groq` package is a lightweight dependency.

Alternatives considered and rejected:
- **Use `openai` SDK with Groq base URL**: error messages would say "OpenAI" in logs, confusing.
- **Extend the custom endpoint mechanism**: no named "groq" in dropdown, no model guidance, poor UX.

---

## Models

Two models exposed in the GUI:

| Model | Notes |
|-------|-------|
| `whisper-large-v3-turbo` | **Default.** 216x real-time, multilingual, $0.04/hr. Groq's recommended choice. |
| `whisper-large-v3` | Highest accuracy, slightly slower. |

`distil-whisper-large-v3-en` is officially deprecated by Groq — not included.

---

## Architecture

### Files Changed (Fork Delta)

This section documents every change made to support Groq, so the delta can be re-applied when merging upstream changes.

| File | Type | Summary of change |
|------|------|-------------------|
| `src/transcription_groq.py` | **New** | `GroqTranscriber` class |
| `src/transcriber_factory.py` | Modified | Import + `elif provider == "groq"` branch |
| `src/push_to_talk.py` | Modified | `groq_api_key` field, validator update, 3 provider dispatch points |
| `src/gui/api_section.py` | Modified | Groq API key row, dropdown entry, model list, get/set/test |
| `src/gui/validators.py` | Modified | `validate_groq_api_key()`, update `validate_configuration()` |

`src/gui/config_persistence.py` requires no changes (uses `model_dump()` which auto-includes new fields).

---

## Component Design

### `src/transcription_groq.py` (new)

```
GroqTranscriber(TranscriberBase)
  __init__(api_key, model="whisper-large-v3-turbo")
    - api_key: from arg or GROQ_API_KEY env var
    - client = groq.Groq(api_key=api_key)

  transcribe_audio(audio_file_path, language=None) -> Optional[str]
    - validate_audio_file_exists()
    - validate_audio_duration()
    - 5-attempt retry loop, 3s delay between attempts
    - skip retry on groq.APIStatusError with 4xx status_code
    - API call: client.audio.transcriptions.create(
        model=self.model,
        file=audio_file,
        language=language,
        prompt=prompt,   # glossary terms joined by ", "
      )
    - Response: response.text (always a string attribute)
    - raise last error after all retries exhausted
```

Key differences from `OpenAITranscriber`:
- Error type: `groq.APIStatusError` (has `.status_code`) and `groq.APIError` as base
- Response always has `.text`; no need for `isinstance(response, str)` fallback
- Default model is `whisper-large-v3-turbo` (vs OpenAI's `whisper-1`)

### `src/transcriber_factory.py` (modified)

Fork delta — two additions:
1. Add import: `from src.transcription_groq import GroqTranscriber`
2. Add branch in `create_transcriber()`:
   ```python
   elif provider == "groq":
       transcriber = GroqTranscriber(api_key=api_key, model=model)
   ```

### `src/push_to_talk.py` (modified)

Fork delta — four additions:

1. **`PushToTalkConfig` model**: add field `groq_api_key: str = Field(default="", description="Groq API key")`

2. **`field_validator("stt_provider")`**: update accepted values to include `"groq"`:
   ```python
   if v not in ("openai", "deepgram", "groq"):
       raise ValueError(...)
   ```

3. **`_validate_and_setup_stt_provider()`**: add `elif self.config.stt_provider == "groq"` branch that checks/resolves `groq_api_key` from env var `GROQ_API_KEY`.

4. **`_create_transcriber()` / API key resolution**: add `elif self.config.stt_provider == "groq"` branch using `self.config.groq_api_key`.

### `src/gui/validators.py` (modified)

Fork delta — two additions:

1. **New function `validate_groq_api_key(api_key)`**: instantiates `groq.Groq(api_key=api_key)` and calls `.models.list()`. Catches exceptions and raises with descriptive messages matching the existing pattern (INVALID / TIMEOUT / ERROR prefix).

2. **`validate_configuration()`**: add `elif config.stt_provider == "groq"` branch checking `groq_api_key`.

### `src/gui/api_section.py` (modified)

Fork delta — changes to `APISection`:

1. **`__init__`**: add `self.groq_api_key_var = tk.StringVar()`, `self.groq_widgets = {}`, `self.groq_stt_model = "whisper-large-v3-turbo"`

2. **`_create_widgets()`**:
   - API Keys section: add Groq row (row 5) with masked entry + Show/Hide button; shift Custom to row 6
   - STT Provider combobox values: `["openai", "deepgram", "groq"]`

3. **`_update_stt_model_options()`** and **`_update_combobox_options_only()`**: add Groq model list `["whisper-large-v3-turbo", "whisper-large-v3"]` and restore `groq_stt_model` on provider switch.

4. **`_on_stt_model_changed()`**: save to `self.groq_stt_model` when provider is `"groq"`.

5. **`get_values()`**: include `"groq_api_key": self.groq_api_key_var.get().strip()`.

6. **`set_values()`**: accept `groq_api_key` param; set `self.groq_api_key_var`; store `stt_model` into `self.groq_stt_model` when `stt_provider == "groq"`.

7. **`test_api_keys()`**: add Groq validation block calling `validate_groq_api_key()`, same pattern as OpenAI/Deepgram blocks.

---

## Data Flow

```
User presses hotkey
  -> PushToTalk._process_audio_background()
  -> PushToTalk._create_transcriber()
       stt_provider == "groq"  ->  api_key = config.groq_api_key
       TranscriberFactory.create_transcriber("groq", api_key, model)
       -> GroqTranscriber(api_key, model)
  -> transcriber.transcribe_audio(path, language)
       -> groq.Groq.audio.transcriptions.create(...)
       -> response.text
  -> refine_text() / clipboard insert
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `groq.APIStatusError` with 4xx | Log error, raise immediately (no retry) |
| `groq.APIStatusError` with 5xx | Log warning, retry up to 5 times with 3s delay |
| Connection error / generic exception | Log warning, retry up to 5 times with 3s delay |
| All retries exhausted | Raise last error; caller sends critical desktop notification |
| Empty response | Return `None` |

---

## Testing

New test file `tests/test_transcription_groq.py` with `TestGroqTranscriber` class:

| Test | What it verifies |
|------|-----------------|
| `test_successful_transcription` | Happy path: mock client returns response, text extracted via `.text` |
| `test_retry_on_transient_error` | Fails once, succeeds on retry 2; asserts 2 API calls made |
| `test_no_retry_on_4xx` | `APIStatusError` with `status_code=401` raises immediately; only 1 API call |
| `test_empty_response_returns_none` | `response.text = ""` returns `None` |

Mock pattern: `unittest.mock.patch("src.transcription_groq.groq.Groq")`.

---

## Dependencies

Add `groq` to `pyproject.toml` (or equivalent deps file). The `groq` package is the official Groq Python SDK.

---

## Fork Maintenance Notes

When merging upstream changes, check these files for conflicts with this feature's additions:

- `src/push_to_talk.py` — field added to `PushToTalkConfig`, validator updated, 3 dispatch blocks updated
- `src/transcriber_factory.py` — 1 import, 1 elif branch
- `src/gui/api_section.py` — largest change; Groq row in API keys section, model list, get/set/test additions
- `src/gui/validators.py` — 1 new function, 1 elif in validate_configuration

All changes are additive (no existing logic modified, only extended). Merge conflicts will be straightforward elif/field additions.
