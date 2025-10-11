"""Pytest configuration and global fixtures."""

import sys
from unittest.mock import MagicMock

# Mock sounddevice at import time to avoid PortAudio dependency issues
# This ensures tests can run even if PortAudio is not installed
sys.modules["sounddevice"] = MagicMock()

# Mock pynput at import time to avoid X server/display dependency issues
# This ensures tests can run in headless environments like GitHub Actions
pynput_mock = MagicMock()
pynput_mock.keyboard = MagicMock()
sys.modules["pynput"] = pynput_mock
sys.modules["pynput.keyboard"] = pynput_mock.keyboard
