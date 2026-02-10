#!/usr/bin/env python3
"""
Tests for the git_sync action.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from lsimons_auto.actions.git_sync import OWNER_CONFIGS, OwnerConfig, main


class TestGitSyncAction(unittest.TestCase):
    """Test cases for the git_sync action."""

    def test_owner_configs_structure(self) -> None:
        """Test that OWNER_CONFIGS has the expected structure."""
        self.assertIsInstance(OWNER_CONFIGS, list)
        self.assertGreater(len(OWNER_CONFIGS), 0)

        for config in OWNER_CONFIGS:
            self.assertIsInstance(config, OwnerConfig)
            self.assertIsInstance(config.name, str)
            self.assertGreater(len(config.name), 0)

    def test_owner_configs_content(self) -> None:
        """Test that OWNER_CONFIGS contains expected owners."""
        owner_names = [config.name for config in OWNER_CONFIGS]

        expected_owners = ["lsimons", "lsimons-bot", "typelinkmodel", "LAB271"]

        for expected in expected_owners:
            self.assertIn(expected, owner_names)

    @patch("lsimons_auto.actions.git_sync.get_command_output")
    @patch("lsimons_auto.actions.git_sync.build_fork_context")
    @patch("lsimons_auto.actions.git_sync.build_bot_remote_context")
    @patch("lsimons_auto.actions.git_sync.socket.gethostname")
    def test_main_help_output(
        self,
        mock_hostname: Any,
        mock_bot_context: Any,
        mock_fork_context: Any,
        mock_get_output: Any,
    ) -> None:
        """Test that main help output works."""
        # Mock the GitHub CLI responses to avoid actual API calls
        mock_get_output.return_value = None
        mock_fork_context.return_value = MagicMock()
        mock_bot_context.return_value = MagicMock()
        mock_hostname.return_value = "test-machine"

        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.git_sync", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Synchronize GitHub repositories", result.stdout)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--owner", result.stdout)

    @patch("lsimons_auto.actions.git_sync.get_command_output")
    @patch("lsimons_auto.actions.git_sync.build_fork_context")
    @patch("lsimons_auto.actions.git_sync.build_bot_remote_context")
    @patch("lsimons_auto.actions.git_sync.socket.gethostname")
    def test_main_dry_run_flag(
        self,
        mock_hostname: Any,
        mock_bot_context: Any,
        mock_fork_context: Any,
        mock_get_output: Any,
    ) -> None:
        """Test that dry-run flag is accepted."""
        # Mock the GitHub CLI responses
        mock_get_output.return_value = json.dumps([
            {"name": "test-repo", "isFork": False, "isArchived": False}
        ])
        mock_fork_context.return_value = MagicMock()
        mock_bot_context.return_value = MagicMock()
        mock_hostname.return_value = "test-machine"

        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.git_sync", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should succeed and show dry-run output
        self.assertEqual(result.returncode, 0)
        self.assertIn("Would sync active repo:", result.stdout)
        # The --dry-run flag itself won't appear in output, but "Would" indicates dry-run mode
        self.assertIn("Would", result.stdout)

    @patch("lsimons_auto.actions.git_sync.get_command_output")
    @patch("lsimons_auto.actions.git_sync.build_fork_context")
    @patch("lsimons_auto.actions.git_sync.build_bot_remote_context")
    @patch("lsimons_auto.actions.git_sync.socket.gethostname")
    def test_main_owner_flag(
        self,
        mock_hostname: Any,
        mock_bot_context: Any,
        mock_fork_context: Any,
        mock_get_output: Any,
    ) -> None:
        """Test that owner flag is accepted."""
        # Mock the GitHub CLI responses
        mock_get_output.return_value = json.dumps([
            {"name": "test-repo", "isFork": False, "isArchived": False}
        ])
        mock_fork_context.return_value = MagicMock()
        mock_bot_context.return_value = MagicMock()
        mock_hostname.return_value = "test-machine"

        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.git_sync", "--owner", "lsimons"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should succeed and show output for specific owner
        self.assertEqual(result.returncode, 0)
        self.assertIn("Fetching active repository list for lsimons", result.stdout)

    def test_main_invalid_owner(self) -> None:
        """Test that invalid owner is rejected."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.git_sync", "--owner", "invalid-owner"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    @patch("lsimons_auto.actions.git_sync.get_command_output")
    @patch("lsimons_auto.actions.git_sync.build_fork_context")
    @patch("lsimons_auto.actions.git_sync.build_bot_remote_context")
    @patch("lsimons_auto.actions.git_sync.socket.gethostname")
    def test_main_include_archive_flag(
        self,
        mock_hostname: Any,
        mock_bot_context: Any,
        mock_fork_context: Any,
        mock_get_output: Any,
    ) -> None:
        """Test that include-archive flag is accepted."""
        # Mock the GitHub CLI responses
        mock_get_output.return_value = json.dumps([
            {"name": "test-archived-repo", "isFork": False, "isArchived": True}
        ])
        mock_fork_context.return_value = MagicMock()
        mock_bot_context.return_value = MagicMock()
        mock_hostname.return_value = "test-machine"

        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.git_sync", "--include-archive"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should succeed and show archive processing
        self.assertEqual(result.returncode, 0)
        self.assertIn("Fetching archived repository list", result.stdout)

    @patch("lsimons_auto.actions.git_sync.get_command_output")
    @patch("lsimons_auto.actions.git_sync.build_fork_context")
    @patch("lsimons_auto.actions.git_sync.build_bot_remote_context")
    @patch("lsimons_auto.actions.git_sync.socket.gethostname")
    def test_main_programmatic_dry_run(
        self,
        mock_hostname: Any,
        mock_bot_context: Any,
        mock_fork_context: Any,
        mock_get_output: Any,
    ) -> None:
        """Test main function called programmatically with dry-run."""
        import contextlib
        import io

        # Mock subprocess calls to avoid actual git operations
        mock_get_output.return_value = json.dumps([
            {"name": "test-repo", "isFork": False, "isArchived": False}
        ])
        mock_fork_context.return_value = MagicMock()
        mock_bot_context.return_value = MagicMock()
        mock_hostname.return_value = "test-machine"

        # Capture stdout
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            main(["--dry-run"])

        # Should not raise exceptions and should call the mocked functions
        self.assertTrue(mock_get_output.called)
        self.assertTrue(mock_fork_context.called)
        self.assertTrue(mock_bot_context.called)


if __name__ == "__main__":
    unittest.main()
