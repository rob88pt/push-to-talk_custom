# Implementation Plan - Version 1.2 Release and Transcription Fixes

This plan covers the fix for transcription failures (Deepgram API and OpenAI error handling) and the official release of version 1.2.

## Proposed Changes

### [Component] Transcription Service

#### [MODIFY] [transcription_deepgram.py](file:///d:/Push_to_talk/src/transcription_deepgram.py)
Update the `transcribe_audio` method to use the correct Deepgram SDK v5 structure and consistent "return None on error" pattern.

```diff
-            # Call Deepgram API
-            response = self.client.listen.rest.v("1").transcribe_file(
-                request=audio_data, **options_dict
-            )
+            # Call Deepgram API (v5.x SDK structure)
+            response = self.client.listen.v1.media.transcribe_file(
+                request=audio_data, **options_dict
+            )
```

#### [MODIFY] [transcription_openai.py](file:///d:/Push_to_talk/src/transcription_openai.py)
Fix the `transcribe_audio` method to return `None` on exception or empty response, matching the base class contract.

```diff
-            if not response:
-                logger.error("OpenAI transcription API returned empty response")
-                return ""
+            if not response or not str(response).strip():
+                logger.error("OpenAI transcription API returned empty response")
+                return None

...

-        except Exception as e:
-            logger.error(f"OpenAI transcription error: {str(e)}")
-            raise
+        except Exception as e:
+            logger.error(f"OpenAI transcription error: {str(e)}")
+            return None
```

#### [MODIFY] [tests/test_push_to_talk.py](file:///d:/Push_to_talk/tests/test_push_to_talk.py)
Update `StubTranscriber` to accept the `language` argument.

```diff
-        def transcribe_audio(self, audio_path):
+        def transcribe_audio(self, audio_path, language=None):
```

### [Component] Versioning and Branding

#### [MODIFY] [pyproject.toml](file:///d:/Push_to_talk/pyproject.toml)
Update version to `1.2.0`.

#### [MODIFY] [README.md](file:///d:/Push_to_talk/README.md)
Update version badges and demo mentions to `1.2.0`.

#### [MODIFY] [docs/changelog.md](file:///d:/Push_to_talk/docs/changelog.md)
Add release notes for `v1.2.0`.

#### [MODIFY] [src/gui/configuration_window.py](file:///d:/Push_to_talk/src/gui/configuration_window.py)
Update welcome message to `v1.2`.

## Verification Plan

### Automated Tests
Run all transcription and integration tests:
```bash
uv run pytest tests/test_transcription_deepgram.py
uv run pytest tests/test_transcription_openai.py
uv run pytest tests/test_push_to_talk.py
```

### Build and Package
Run the build script to generate the versioned executable:
```bash
.\build_script\build.bat
```

### Manual Verification
1. Launch the application: `uv run python main.py`
2. Configure Deepgram as the transcription provider and select the "Nova-3" model.
3. Record a short audio snippet.
4. Verify that transcription completes successfully and logs show "Transcription successful".
5. Verify that the transcribed text is correctly inserted into the active window.
