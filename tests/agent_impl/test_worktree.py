#!/usr/bin/env python3
"""
Tests for git worktree management.

Tests the worktree.py module functionality.
"""

import tempfile
import unittest
from pathlib import Path

from lsimons_auto.actions.agent_impl import worktree


class TestWorktreeFunctions(unittest.TestCase):
    """Test git worktree helper functions."""

    def test_ensure_worktrees_dir_creates_directory(self) -> None:
        """Test that ensure_worktrees_dir creates the correct directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir) / "my-repo"
            workspace_path.mkdir()

            worktrees_dir = worktree.ensure_worktrees_dir(workspace_path)

            expected_dir = Path(tmpdir) / "my-repo-worktrees"
            self.assertEqual(worktrees_dir, expected_dir)
            self.assertTrue(worktrees_dir.exists())

    def test_ensure_worktrees_dir_idempotent(self) -> None:
        """Test that ensure_worktrees_dir can be called multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir) / "my-repo"
            workspace_path.mkdir()

            # Call twice
            worktrees_dir1 = worktree.ensure_worktrees_dir(workspace_path)
            worktrees_dir2 = worktree.ensure_worktrees_dir(workspace_path)

            self.assertEqual(worktrees_dir1, worktrees_dir2)
            self.assertTrue(worktrees_dir2.exists())


if __name__ == "__main__":
    unittest.main()
