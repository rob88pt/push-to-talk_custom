# Changelog

## [2026-01-26] - Cerebras Model Expansion & Build

### Added
- Added `gpt-oss-120b` (GPT OSS), `llama-3.1-8b`, `qwen-3-235b-instruct`, and `z-ai-glm-4.7` to the Cerebras refinement provider model list.
- Standalone Windows executable and zip archive built in `dist/`.

### Changed
- Updated `src/gui/api_section.py` to expose the new models in the configuration GUI.

### Verified
- Ran `pytest tests/test_text_refiner_factory.py tests/test_config_gui.py` - All tests passed.
- Successfully executed `.\build_script\build.bat` to generate the production executable.

### Decisions
- Included both production and preview models for Cerebras to provide users with more options before upcoming deprecations.

### Files Affected
- `src/gui/api_section.py` - Updated `cerebras_models` list in multiple methods.
- `dist/PushToTalk.exe` - New standalone executable.
- `dist/PushToTalk.zip` - New zip archive.
