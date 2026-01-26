# Active Context

## Current Focus
Expanding the available models for the Cerebras refinement provider and building the standalone executable.

## Recent Changes
- Updated `src/gui/api_section.py` to include new Cerebras models: `gpt-oss-120b`, `llama-3.1-8b`, `qwen-3-235b-instruct`, and `z-ai-glm-4.7`.
- Successfully built the standalone Windows executable using `build.bat`.
- Verified changes with existing tests (`tests/test_text_refiner_factory.py`, `tests/test_config_gui.py`).

## Next Steps
- [ ] User to verify the new models in the standalone executable.
- [ ] Deploy the updated executable if everything works as expected.
- [ ] Investigate additional refinement providers as per backlog.

## Session Notes
- User encountered config loss after EXE rebuild; recovered it manually.
- The root cause is that `push_to_talk_config.json` is stored in the CWD (where the EXE is run), not a global user data folder.
- User decided not to implement more robust storage for now.
