#!/usr/bin/env python3
"""
Tests for AppleScript helpers and Ghostty terminal control.

Tests the ghostty.py module functionality. AppleScript execution is mocked.
"""

import subprocess
import unittest
from unittest.mock import Mock, patch

from lsimons_auto.actions.agent_manager_impl import ghostty


class TestAppleScriptHelpers(unittest.TestCase):
    """Test AppleScript helper functions."""

    @patch.object(ghostty.subprocess, "run")
    def test_run_applescript_success(self, mock_run: Mock) -> None:
        """Test successful AppleScript execution."""
        mock_run.return_value = Mock(stdout="output\n", stderr="")

        result = ghostty.run_applescript('tell application "Finder" to activate')

        self.assertEqual(result, "output")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "osascript")
        self.assertEqual(args[1], "-e")

    @patch.object(ghostty.subprocess, "run")
    def test_run_applescript_failure(self, mock_run: Mock) -> None:
        """Test AppleScript failure handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["osascript"], stderr="Error message"
        )

        with self.assertRaises(RuntimeError) as cm:
            ghostty.run_applescript("invalid script")
        self.assertIn("AppleScript failed", str(cm.exception))

    @patch.object(ghostty.subprocess, "run")
    def test_run_applescript_not_found(self, mock_run: Mock) -> None:
        """Test handling when osascript is not found."""
        mock_run.side_effect = FileNotFoundError()

        with self.assertRaises(RuntimeError) as cm:
            ghostty.run_applescript("any script")
        self.assertIn("osascript not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
