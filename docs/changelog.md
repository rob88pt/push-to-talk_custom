# Changelog

## [2026-01-27] - Release v1.2.0: Deepgram SDK Fix & OpenAI Consistency

### Fixed
- **Deepgram Transcription API**: Resolved `AttributeError: 'ListenClient' object has no attribute 'rest'` by updating to the Deepgram SDK v5.x asynchronous-compatible structure.
- **OpenAI Transcription Robustness**: Fixed a bug where transcription errors would re-raise exceptions instead of returning `None`, ensuring the app processing pipeline remains stable.
- **Transcriber Contract**: Standardized all transcription providers to return `None` on error, ensuring consistent behavior across services.
- **Integration Test Regressions**: Updated `StubTranscriber` in tests to correctly handle the new `language` argument.

### Changed
- **Branding**: Updated internal versioning to v1.2 across GUI and configuration.

### Verified
- Passed all 220 unit and integration tests.
- Verified Deepgram Nova-3 transcription with the new SDK structure.
- Verified OpenAI graceful failure handling.
- Confirmed build process for versioned executable.

## [2026-01-26] - Release v1.1.0: Language Selector & OpenAI Enhancements

### Fixed
- **Deepgram Transcription Error**: Fixed a critical syntax error in `src/transcription_deepgram.py` where `options` was being reassigned to `options_dict` incorrectly.

### Added
- **Enhanced Debug Logging**: Added verbose logging across the transcription pipeline to facilitate easier troubleshooting of API calls and audio processing steps.
- **Transcription Language Selector**: Users can now choose a specific transcription language in the GUI settings (supports English, Spanish, French, etc., and auto-detection).
- **OpenAI Transcription Hints**: Added language hints to the OpenAI transcription prompt to improve consistency and accuracy.
- **OpenAI Glossary Support**: Fixed missing glossary integration in the OpenAI transcription pipeline.
- **Versioned Executable Build**: The build process now generates versioned files: `PushToTalk_v1.1.exe` and `PushToTalk_v1.1.zip`.

### Changed
- **Branding**: Updated internal versioning in `pyproject.toml` and GUI welcome section to v1.1.
- **PyInstaller Spec**: Updated `push_to_talk.spec` to output versioned binary filenames.

### Verified
- Ran `pytest tests/test_transcription_openai.py` - 17 passed.
- Successfully verified the new versioned build in the `dist/` directory.

### Decisions
- Moving to versioned executable names (`_v1.1`) to help users manage multiple versions of the tool.

### Files Affected
- `src/push_to_talk.py` - Core config and processing logic.
- `src/transcription_openai.py` - OpenAI transcription enhancements.
- `src/gui/api_section.py` - Language selector GUI.
- `src/gui/configuration_window.py` - Branding and variable wiring.
- `pyproject.toml` - Version update.
- `README.md` - Documentation and badge updates.
- `build_script/push_to_talk.spec` - Build output naming.
- `build_script/build.bat` - Cleanup and compression updates.
