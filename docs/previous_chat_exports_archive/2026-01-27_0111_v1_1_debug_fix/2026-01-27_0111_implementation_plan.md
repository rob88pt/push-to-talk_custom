# Building PushToTalk v1.1

This plan covers the branding and building of PushToTalk version 1.1, including versioned executable naming.

## Proposed Changes

### Versioning & Branding (Internal)

#### [MODIFY] [pyproject.toml](file:///d:/Push_to_talk/pyproject.toml)
- Updated version to `1.1.0`. [DONE]

#### [MODIFY] [configuration_window.py](file:///d:/Push_to_talk/src/gui/configuration_window.py)
- Updated welcome section title to "PushToTalk v1.1". [DONE]

#### [MODIFY] [README.md](file:///d:/Push_to_talk/README.md)
- Updated version badges and release notes. [DONE]

### Build Process (External Branding)

#### [MODIFY] [push_to_talk.spec](file:///d:/Push_to_talk/build_script/push_to_talk.spec)
- Change executable name to `PushToTalk_v1.1`.

#### [MODIFY] [build.bat](file:///d:/Push_to_talk/build_script/build.bat)
- Update cleanup, output messages, and compression logic to use `PushToTalk_v1.1.exe` and `PushToTalk_v1.1.zip`.

## Verification Plan

### Automated Tests
- Run `build_script/build.bat` and verify `dist/PushToTalk_v1.1.exe` and `dist/PushToTalk_v1.1.zip` exist.

### Manual Verification
- Check the filename of the generated executable in the file explorer.
- Launch the app and verify the GUI title matches v1.1.
