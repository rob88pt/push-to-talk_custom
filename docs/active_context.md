# Active Context

## Current Focus
- Adding Groq as a Speech-to-Text transcription provider.

## Recent Changes (2026-04-16)
- OpenAI transcription: 5 retries with 3s delay, skip 4xx immediately.
- Text refinement: 5s timeout, falls back to raw transcription.
- Both failures trigger desktop notifications.
- Fixed `build_linux.sh` to use `.venv/bin/python -m PyInstaller`.

## Next Steps
- [ ] Implement `src/transcription_groq.py` using the `groq` Python SDK.
- [ ] Update transcription factory to register Groq provider.
- [ ] Add `groq_api_key` config field and GUI section (API key input + model dropdown).
- [ ] Wire up Groq model list (default: `whisper-large-v3`).

## Session Notes
- Successfully recovered configuration after build-related loss.
- Implemented transcription language hints to improve Whisper accuracy.
- Branded the build as v1.1.0 to reflect significant feature additions.
