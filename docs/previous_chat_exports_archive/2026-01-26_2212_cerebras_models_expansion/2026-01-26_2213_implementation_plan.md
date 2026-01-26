# Implementation Plan - Cerebras Model Expansion

Add the GPT OSS model and other current Cerebras models to the refinement provider selection.

## Proposed Changes

### Cerebras Model Expansion

#### [MODIFY] [api_section.py](file:///d:/Push_to_talk/src/gui/api_section.py)
- Update the `cerebras_models` list in `_update_refinement_model_options` to include:
  - `gpt-oss-120b` (The "GPT OSS" model)
  - `llama-3.1-8b`
  - `qwen-3-235b-instruct`
  - `z-ai-glm-4.7`
- Keep existing models (`llama-3.3-70b`, etc.) as they are still functional for now.

#### [MODIFY] [push_to_talk.py](file:///d:/Push_to_talk/src/push_to_talk.py)
- Update default `refinement_model` if necessary (optional).

## Verification Plan

### Automated Tests
- Run refinement tests:
  ```powershell
  uv run pytest tests/test_text_refiner.py
  ```
- Verify `TranscriberFactory` or relevant factory handles new model names correctly if applicable.

### Manual Verification
1. Launch the application.
2. Open Configuration.
3. Select "Cerebras" as the refinement provider.
4. Verify `gpt-oss-120b` and others appear in the "Refinement Model" dropdown.
