#!/usr/bin/env python3
"""
Tests for the launch_apps action.

These tests focus on the launch_apps functionality including command line
interface and command execution logic.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lsimons_auto.actions import launch_apps


class TestLaunchApps(unittest.TestCase):
    """Test cases for launch_apps action."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.project_root = Path.home() / "dev" / "lsimons-auto"
        cls.launch_apps_script = (
            cls.project_root / "lsimons_auto" / "actions" / "launch_apps.py"
        )

        # Verify test environment
        if not cls.project_root.exists():
            raise unittest.SkipTest(f"Project root not found: {cls.project_root}")
        if not cls.launch_apps_script.exists():
            raise unittest.SkipTest(
                f"Launch apps script not found: {cls.launch_apps_script}"
            )

    def test_launch_apps_cli_help(self):
        """Test command line interface help output."""
        result = subprocess.run(
            [sys.executable, str(self.launch_apps_script), "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Launch predefined applications and commands", result.stdout)
        self.assertIn("--list", result.stdout)

    def test_launch_apps_cli_list(self):
        """Test --list flag shows configured commands."""
        result = subprocess.run(
            [sys.executable, str(self.launch_apps_script), "--list"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Configured launch commands:", result.stdout)
        self.assertIn(
            "open /System/Applications/TextEdit.app ~/scratch.txt", result.stdout
        )

    @patch("lsimons_auto.actions.launch_apps.subprocess.Popen")
    def test_launch_command_success(self, mock_popen):
        """Test successful command launch."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        result = launch_apps.launch_command("test command")

        self.assertTrue(result)
        mock_popen.assert_called_once_with(
            "test command",
            shell=True,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("lsimons_auto.actions.launch_apps.subprocess.Popen")
    def test_launch_command_failure(self, mock_popen):
        """Test command launch failure handling."""
        mock_popen.side_effect = Exception("Command failed")

        result = launch_apps.launch_command("failing command")

        self.assertFalse(result)

    @patch("lsimons_auto.actions.launch_apps.launch_command")
    def test_launch_all_apps_success(self, mock_launch_command):
        """Test launching all configured apps successfully."""
        mock_launch_command.return_value = True

        # Redirect stdout to capture output
        with patch("sys.stdout") as mock_stdout:
            launch_apps.launch_all_apps()

        # Verify launch_command was called for each configured command
        self.assertEqual(
            mock_launch_command.call_count, len(launch_apps.LAUNCH_COMMANDS)
        )

    @patch("lsimons_auto.actions.launch_apps.launch_command")
    def test_launch_all_apps_partial_failure(self, mock_launch_command):
        """Test launching apps with some failures."""
        mock_launch_command.side_effect = [True, False]  # First succeeds, second fails

        # Redirect stdout to capture output
        with patch("sys.stdout") as mock_stdout:
            launch_apps.launch_all_apps()

        # Verify launch_command was called for each configured command
        self.assertEqual(
            mock_launch_command.call_count, len(launch_apps.LAUNCH_COMMANDS)
        )

    def test_main_with_list_argument(self):
        """Test main function with --list argument."""
        with patch("sys.stdout") as mock_stdout:
            launch_apps.main(["--list"])

        # Verify output was printed (we can't easily check exact content due to mocking)
        mock_stdout.write.assert_called()

    @patch("lsimons_auto.actions.launch_apps.launch_all_apps")
    def test_main_launches_apps(self, mock_launch_all_apps):
        """Test main function launches apps by default."""
        launch_apps.main([])

        mock_launch_all_apps.assert_called_once()

    def test_launch_commands_configured(self):
        """Test that at least one command is configured."""
        self.assertGreater(len(launch_apps.LAUNCH_COMMANDS), 0)
        self.assertIn(
            "open /System/Applications/TextEdit.app ~/scratch.txt",
            launch_apps.LAUNCH_COMMANDS[0],
        )


if __name__ == "__main__":
    unittest.main()
