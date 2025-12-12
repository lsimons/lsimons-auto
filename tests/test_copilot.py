#!/usr/bin/env python3
"""
Tests for the copilot action.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lsimons_auto.actions import copilot


class TestCopilotAction(unittest.TestCase):
    """Unit tests for the copilot action."""

    def test_main_script_not_found(self) -> None:
        """Test behavior when AppleScript file is not found."""
        with mock.patch.object(Path, "exists", return_value=False):
            exit_code = copilot.main([])
            self.assertEqual(exit_code, 1)

    def test_main_osascript_not_found(self) -> None:
        """Test behavior when osascript command is not found."""
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch(
                "subprocess.run",
                side_effect=FileNotFoundError("osascript not found"),
            ):
                exit_code = copilot.main([])
                self.assertEqual(exit_code, 1)

    def test_main_subprocess_error(self) -> None:
        """Test behavior when AppleScript execution fails."""
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "osascript"),
            ):
                exit_code = copilot.main([])
                self.assertEqual(exit_code, 1)

    def test_main_success(self) -> None:
        """Test successful AppleScript execution."""
        with mock.patch.object(Path, "exists", return_value=True):
            mock_result = mock.Mock()
            mock_result.stdout = "Success\n"
            with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
                exit_code = copilot.main([])
                self.assertEqual(exit_code, 0)
                # Verify osascript was called with correct arguments
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                self.assertEqual(call_args[0][0][0], "osascript")
                self.assertTrue(
                    str(call_args[0][0][1]).endswith("ask_m365_copilot.scpt")
                )


@unittest.skipIf(
    sys.platform != "darwin",
    "Integration tests require macOS",
)
class TestCopilotActionIntegration(unittest.TestCase):
    """Integration tests for the copilot action."""

    @unittest.skip("Requires Microsoft 365 Copilot to be installed and running")
    def test_copilot_integration(self) -> None:
        """
        Test actual execution of the copilot action.

        This test is skipped by default as it requires:
        - macOS
        - Microsoft 365 Copilot installed
        - Copilot app running
        - Accessibility permissions granted
        """
        exit_code = copilot.main([])
        # Should succeed if all requirements are met
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
