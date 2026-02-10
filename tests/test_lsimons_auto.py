#!/usr/bin/env python3
"""
Tests for the main lsimons_auto dispatcher.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from lsimons_auto.lsimons_auto import discover_actions, normalize_action_name


class TestDispatcher(unittest.TestCase):
    """Test cases for the main dispatcher functionality."""

    def test_discover_actions(self) -> None:
        """Test that action discovery finds all available actions."""
        actions = discover_actions()

        # Should find at least some actions
        self.assertGreater(len(actions), 0)

        # Check that expected actions are found
        expected_actions = {"echo", "organize-desktop", "update-desktop-background", "git-sync"}

        for action in expected_actions:
            self.assertIn(action, actions)
            self.assertTrue(actions[action].exists())

    def test_normalize_action_name(self) -> None:
        """Test action name normalization."""
        # Test underscore to dash conversion
        self.assertEqual(normalize_action_name("git_sync"), "git-sync")
        self.assertEqual(
            normalize_action_name("update_desktop_background"), "update-desktop-background"
        )

        # Test that dashes remain unchanged
        self.assertEqual(normalize_action_name("git-sync"), "git-sync")
        self.assertEqual(normalize_action_name("organize-desktop"), "organize-desktop")

    def test_setup_logging(self) -> None:
        """Test that logging setup works correctly."""
        from lsimons_auto.logging_utils import setup_logging

        logger = setup_logging()
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "lsimons_auto")
        self.assertEqual(logger.level, 20)  # INFO level

    def test_discover_actions_empty_directory(self) -> None:
        """Test action discovery with non-existent directory."""
        # Mock the actions directory to not exist
        with patch("lsimons_auto.lsimons_auto.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            actions = discover_actions()
            self.assertEqual(len(actions), 0)

    def test_main_help_output(self) -> None:
        """Test that main help output works."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.lsimons_auto", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("lsimons-auto command dispatcher", result.stdout)
        self.assertIn("Available actions:", result.stdout)

    def test_main_unknown_action(self) -> None:
        """Test handling of unknown actions."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.lsimons_auto", "unknown-action"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown action", result.stdout)


if __name__ == "__main__":
    unittest.main()
