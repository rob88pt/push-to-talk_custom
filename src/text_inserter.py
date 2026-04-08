import subprocess
import time
from loguru import logger
import sys
from typing import Optional

import pyperclip
from pynput import keyboard

from src.config.constants import (
    TEXT_INSERTION_DELAY_AFTER_COPY_SECONDS,
    TEXT_INSERTION_DELAY_AFTER_PASTE_SECONDS,
)
from src.exceptions import TextInsertionError

TERMINAL_WM_CLASSES = {
    "Gnome-terminal", "mate-terminal", "xfce4-terminal", "terminator", "tilix",
    "kitty", "Alacritty", "st-256color", "URxvt", "XTerm", "konsole",
    "lxterminal", "sakura", "guake", "Tilda", "cool-retro-term", "wezterm-gui",
    "foot", "rio", "ghostty", "dev.warp.Warp",
}


class TextInserter:
    # Default insertion delay in seconds
    DEFAULT_INSERTION_DELAY = 0.005

    def __init__(self):
        """Initialize the text inserter."""
        self.insertion_delay = self.DEFAULT_INSERTION_DELAY
        self.keyboard = keyboard.Controller()

    def insert_text(self, text: str) -> bool:
        """
        Insert text into the currently active window using clipboard method.

        Args:
            text: Text to insert

        Returns:
            True if insertion was successful, False otherwise
        """
        if not text:
            logger.warning("Empty text provided for insertion")
            return False

        try:
            return self._insert_via_clipboard(text)
        except TextInsertionError:
            # Re-raise TextInsertionError as-is
            raise
        except Exception as e:
            logger.error(f"Text insertion failed: {e}")
            raise TextInsertionError(f"Failed to insert text: {e}") from e

    def _insert_via_clipboard(self, text: str) -> bool:
        """Insert text by copying to clipboard and pasting."""
        original_clipboard = None
        try:
            original_clipboard = pyperclip.paste()
            pyperclip.copy(text)

            time.sleep(TEXT_INSERTION_DELAY_AFTER_COPY_SECONDS)

            if sys.platform == "darwin":
                # macOS: use pynput with Cmd+V
                with self.keyboard.pressed(keyboard.Key.cmd):
                    self.keyboard.press("v")
                    self.keyboard.release("v")
            elif sys.platform == "linux":
                # Linux: use xdotool (more reliable across terminals)
                paste_key = "ctrl+shift+v" if self._is_active_window_terminal() else "ctrl+v"
                subprocess.Popen(
                    ["xdotool", "key", "--delay", "50", paste_key],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Windows: use pynput with Ctrl+V
                with self.keyboard.pressed(keyboard.Key.ctrl):
                    self.keyboard.press("v")
                    self.keyboard.release("v")

            time.sleep(TEXT_INSERTION_DELAY_AFTER_PASTE_SECONDS)

            logger.info(f"Text inserted via clipboard: {len(text)} characters")
            return True

        except Exception as e:
            logger.error(f"Clipboard insertion failed: {e}")
            raise TextInsertionError(f"Clipboard insertion failed: {e}") from e
        finally:
            if original_clipboard is not None:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass

    def _get_clipboard_text(self) -> Optional[str]:
        """Get current clipboard text content."""
        try:
            return pyperclip.paste()
        except Exception:
            return None

    def _set_clipboard_text(self, text: str) -> None:
        """Set clipboard text content."""
        pyperclip.copy(text)

    @staticmethod
    def _is_active_window_terminal() -> bool:
        """Detect if the active window is a terminal using xprop WM_CLASS."""
        try:
            window_id = subprocess.check_output(
                ["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL, timeout=1
            ).strip()
            wm_class_output = subprocess.check_output(
                ["xprop", "-id", window_id, "WM_CLASS"], stderr=subprocess.DEVNULL, timeout=1
            ).decode()
            # Extract all WM_CLASS values
            for part in wm_class_output.split('"'):
                if part.strip() and part.strip() not in (",", "WM_CLASS(STRING) ="):
                    if part in TERMINAL_WM_CLASSES:
                        return True
        except Exception:
            pass
        return False

    def get_active_window_title(self) -> Optional[str]:
        """
        Get the title of the currently active window.

        Note: This functionality is not available without pyautogui.
        Returns None for logging purposes.

        Returns:
            None (window title detection not implemented)
        """
        # Window title detection was removed to eliminate pyautogui dependency
        # This is only used for logging, so returning None is acceptable
        return None
