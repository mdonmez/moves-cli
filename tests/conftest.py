"""Pytest configuration and shared fixtures."""

import sys
from unittest.mock import MagicMock

# Mock system dependencies to avoid hardware/display requirements
# This ensures tests can run in CI/CD environments without audio devices or X servers

# Mock sounddevice (requires PortAudio)
sys.modules["sounddevice"] = MagicMock()

# Mock pynput (requires display server)
pynput_mock = MagicMock()
pynput_mock.keyboard = MagicMock()
sys.modules["pynput"] = pynput_mock
sys.modules["pynput.keyboard"] = pynput_mock.keyboard
