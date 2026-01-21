#!/usr/bin/env python3
"""
Tests for the agent action.

These tests focus on workspace discovery, fuzzy matching, session management,
and argument parsing. AppleScript execution is mocked.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lsimons_auto.actions import agent


class TestWorkspaceDiscovery(unittest.TestCase):
    """Test workspace discovery functionality."""

    def test_discover_workspaces_finds_orgs(self) -> None:
        """Test workspace discovery finds org directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_root = Path(tmpdir)
            (git_root / "org1" / "repo1").mkdir(parents=True)
            (git_root / "org1" / "repo2").mkdir(parents=True)
            (git_root / "org2" / "repo3").mkdir(parents=True)

            workspaces = agent.discover_workspaces(git_root)

            self.assertIn("org1", workspaces)
            self.assertIn("org2", workspaces)
            self.assertEqual(len(workspaces["org1"]), 2)
            self.assertEqual(len(workspaces["org2"]), 1)

    def test_discover_workspaces_ignores_hidden(self) -> None:
        """Test workspace discovery ignores hidden directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_root = Path(tmpdir)
            (git_root / "org1" / "repo1").mkdir(parents=True)
            (git_root / ".hidden" / "repo2").mkdir(parents=True)
            (git_root / "org1" / ".hidden-repo").mkdir(parents=True)

            workspaces = agent.discover_workspaces(git_root)

            self.assertIn("org1", workspaces)
            self.assertNotIn(".hidden", workspaces)
            self.assertNotIn(".hidden-repo", workspaces.get("org1", {}))

    def test_discover_workspaces_empty_dir(self) -> None:
        """Test workspace discovery handles empty directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_root = Path(tmpdir)

            workspaces = agent.discover_workspaces(git_root)

            self.assertEqual(workspaces, {})

    def test_discover_workspaces_nonexistent_dir(self) -> None:
        """Test workspace discovery handles nonexistent directory."""
        workspaces = agent.discover_workspaces(Path("/nonexistent/path"))
        self.assertEqual(workspaces, {})


class TestFuzzyMatching(unittest.TestCase):
    """Test fuzzy matching functionality."""

    def test_fuzzy_match_exact(self) -> None:
        """Test exact match returns correct workspace."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/test/path")}}
        result = agent.fuzzy_match_workspace("lsimons", "lsimons-auto", workspaces)
        self.assertEqual(result[0], "lsimons")
        self.assertEqual(result[1], "lsimons-auto")
        self.assertEqual(result[2], Path("/test/path"))

    def test_fuzzy_match_partial_org(self) -> None:
        """Test partial org match works."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/test/path")}}
        result = agent.fuzzy_match_workspace("lsim", "auto", workspaces)
        self.assertEqual(result[0], "lsimons")
        self.assertEqual(result[1], "lsimons-auto")

    def test_fuzzy_match_case_insensitive(self) -> None:
        """Test case insensitive matching."""
        workspaces = {"Lsimons": {"Lsimons-Auto": Path("/test/path")}}
        result = agent.fuzzy_match_workspace("lsim", "auto", workspaces)
        self.assertEqual(result[0], "Lsimons")
        self.assertEqual(result[1], "Lsimons-Auto")

    def test_fuzzy_match_ambiguous_org_raises(self) -> None:
        """Test ambiguous org match raises ValueError."""
        workspaces = {
            "lsimons": {"lsimons-auto": Path("/a")},
            "lsimons-bot": {"bot-repo": Path("/b")},
        }
        with self.assertRaises(ValueError) as cm:
            agent.fuzzy_match_workspace("lsimons", "auto", workspaces)
        self.assertIn("Ambiguous", str(cm.exception))

    def test_fuzzy_match_ambiguous_repo_raises(self) -> None:
        """Test ambiguous repo match raises ValueError."""
        workspaces = {
            "lsimons": {
                "lsimons-auto": Path("/a"),
                "lsimons-tools": Path("/b"),
            }
        }
        with self.assertRaises(ValueError) as cm:
            agent.fuzzy_match_workspace("lsimons", "lsimons", workspaces)
        self.assertIn("Ambiguous", str(cm.exception))

    def test_fuzzy_match_no_org_raises(self) -> None:
        """Test no org match raises ValueError."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/a")}}
        with self.assertRaises(ValueError) as cm:
            agent.fuzzy_match_workspace("nonexistent", "auto", workspaces)
        self.assertIn("No org found", str(cm.exception))

    def test_fuzzy_match_no_repo_raises(self) -> None:
        """Test no repo match raises ValueError."""
        workspaces = {"lsimons": {"lsimons-auto": Path("/a")}}
        with self.assertRaises(ValueError) as cm:
            agent.fuzzy_match_workspace("lsimons", "nonexistent", workspaces)
        self.assertIn("No repo found", str(cm.exception))


class TestSessionManagement(unittest.TestCase):
    """Test session state persistence."""

    def test_session_save_and_load(self) -> None:
        """Test session round-trip through disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                session = agent.AgentSession(
                    session_id="test-session",
                    workspace_path="/test/path",
                    repo_name="test-repo",
                    org_name="test-org",
                    created_at="2026-01-21T00:00:00Z",
                    panes=[
                        agent.AgentPane(
                            id="M-test",
                            pane_index=0,
                            command="claude",
                            is_main=True,
                        )
                    ],
                )
                session.save()

                loaded = agent.AgentSession.load("test-session")

                self.assertEqual(loaded.session_id, session.session_id)
                self.assertEqual(loaded.workspace_path, session.workspace_path)
                self.assertEqual(len(loaded.panes), 1)
                self.assertEqual(loaded.panes[0].id, "M-test")

    def test_session_delete(self) -> None:
        """Test session deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                session = agent.AgentSession(
                    session_id="test-session",
                    workspace_path="/test/path",
                    repo_name="test-repo",
                    org_name="test-org",
                    created_at="2026-01-21T00:00:00Z",
                )
                session.save()

                session_file = sessions_dir / "test-session.json"
                self.assertTrue(session_file.exists())

                session.delete()

                self.assertFalse(session_file.exists())

    def test_session_load_not_found(self) -> None:
        """Test loading nonexistent session raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)
            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                with self.assertRaises(FileNotFoundError):
                    agent.AgentSession.load("nonexistent")


class TestListSessions(unittest.TestCase):
    """Test session listing functionality."""

    def test_list_sessions_empty(self) -> None:
        """Test listing sessions when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                sessions = agent.list_sessions()
                self.assertEqual(sessions, [])

    def test_list_sessions_finds_all(self) -> None:
        """Test listing sessions finds all valid sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)

            # Create test sessions
            for i in range(3):
                session_data: dict[str, object] = {
                    "session_id": f"test-session-{i}",
                    "workspace_path": "/test/path",
                    "repo_name": "test-repo",
                    "org_name": "test-org",
                    "created_at": f"2026-01-21T0{i}:00:00Z",
                    "panes": [],
                }
                with open(sessions_dir / f"test-session-{i}.json", "w") as f:
                    json.dump(session_data, f)

            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                sessions = agent.list_sessions()
                self.assertEqual(len(sessions), 3)

    def test_get_most_recent_session(self) -> None:
        """Test getting most recent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)

            # Create test sessions
            for i in range(3):
                session_data: dict[str, object] = {
                    "session_id": f"test-session-{i}",
                    "workspace_path": "/test/path",
                    "repo_name": "test-repo",
                    "org_name": "test-org",
                    "created_at": f"2026-01-21T0{i}:00:00Z",
                    "panes": [],
                }
                with open(sessions_dir / f"test-session-{i}.json", "w") as f:
                    json.dump(session_data, f)

            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                session = agent.get_most_recent_session()
                self.assertIsNotNone(session)

    def test_get_most_recent_session_none(self) -> None:
        """Test getting most recent session when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                session = agent.get_most_recent_session()
                self.assertIsNone(session)


class TestFindPaneByTarget(unittest.TestCase):
    """Test pane finding functionality."""

    def setUp(self) -> None:
        """Set up test session."""
        self.session = agent.AgentSession(
            session_id="test",
            workspace_path="/test",
            repo_name="repo",
            org_name="org",
            created_at="2026-01-21T00:00:00Z",
            panes=[
                agent.AgentPane("M-repo", 0, "claude", True),
                agent.AgentPane("001-repo", 1, "claude", False),
                agent.AgentPane("002-repo", 2, "claude", False),
            ],
        )

    def test_find_by_main_keyword(self) -> None:
        """Test finding main pane by 'main' keyword."""
        result = agent.find_pane_by_target(self.session, "main")
        assert result is not None
        pane, idx = result
        self.assertEqual(pane.id, "M-repo")
        self.assertEqual(idx, 0)

    def test_find_by_index(self) -> None:
        """Test finding pane by numeric index."""
        result = agent.find_pane_by_target(self.session, "1")
        assert result is not None
        pane, idx = result
        self.assertEqual(pane.id, "001-repo")
        self.assertEqual(idx, 1)

    def test_find_by_id_partial(self) -> None:
        """Test finding pane by partial ID."""
        result = agent.find_pane_by_target(self.session, "002")
        assert result is not None
        pane, _ = result
        self.assertEqual(pane.id, "002-repo")

    def test_find_not_found(self) -> None:
        """Test finding nonexistent pane returns None."""
        result = agent.find_pane_by_target(self.session, "999")
        self.assertIsNone(result)


class TestArgparseSubcommands(unittest.TestCase):
    """Test argument parsing for subcommands."""

    def test_spawn_default_args(self) -> None:
        """Test spawn with minimal arguments."""
        parser = agent.create_parser()
        args = parser.parse_args(["spawn", "lsimons", "auto"])
        self.assertEqual(args.subcommand, "spawn")
        self.assertEqual(args.org, "lsimons")
        self.assertEqual(args.repo, "auto")
        self.assertEqual(args.subagents, 1)
        self.assertEqual(args.command, "claude")
        self.assertFalse(args.no_zed)

    def test_spawn_with_all_options(self) -> None:
        """Test spawn with all options."""
        parser = agent.create_parser()
        args = parser.parse_args(
            ["spawn", "lsimons", "auto", "-n", "3", "-c", "pi", "--no-zed"]
        )
        self.assertEqual(args.subagents, 3)
        self.assertEqual(args.command, "pi")
        self.assertTrue(args.no_zed)

    def test_send_subcommand(self) -> None:
        """Test send subcommand parsing."""
        parser = agent.create_parser()
        args = parser.parse_args(["send", "main", "hello", "world"])
        self.assertEqual(args.subcommand, "send")
        self.assertEqual(args.target, "main")
        self.assertEqual(args.text, ["hello", "world"])

    def test_broadcast_subcommand(self) -> None:
        """Test broadcast subcommand parsing."""
        parser = agent.create_parser()
        args = parser.parse_args(["broadcast", "test", "message", "--exclude-main"])
        self.assertEqual(args.subcommand, "broadcast")
        self.assertEqual(args.text, ["test", "message"])
        self.assertTrue(args.exclude_main)

    def test_focus_subcommand(self) -> None:
        """Test focus subcommand parsing."""
        parser = agent.create_parser()
        args = parser.parse_args(["focus", "left"])
        self.assertEqual(args.subcommand, "focus")
        self.assertEqual(args.target, "left")

    def test_list_subcommand(self) -> None:
        """Test list subcommand parsing."""
        parser = agent.create_parser()
        args = parser.parse_args(["list", "-v"])
        self.assertEqual(args.subcommand, "list")
        self.assertTrue(args.verbose)

    def test_close_subcommand(self) -> None:
        """Test close subcommand parsing."""
        parser = agent.create_parser()
        args = parser.parse_args(["close", "001", "-s", "test-session"])
        self.assertEqual(args.subcommand, "close")
        self.assertEqual(args.target, "001")
        self.assertEqual(args.session, "test-session")

    def test_kill_subcommand(self) -> None:
        """Test kill subcommand parsing."""
        parser = agent.create_parser()
        args = parser.parse_args(["kill", "test-session", "-f"])
        self.assertEqual(args.subcommand, "kill")
        self.assertEqual(args.session, "test-session")
        self.assertTrue(args.force)

    def test_subcommand_required(self) -> None:
        """Test that subcommand is required."""
        parser = agent.create_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])


class TestAppleScriptHelpers(unittest.TestCase):
    """Test AppleScript helper functions."""

    @patch("lsimons_auto.actions.agent.subprocess.run")
    def test_run_applescript_success(self, mock_run: Mock) -> None:
        """Test successful AppleScript execution."""
        mock_run.return_value = Mock(stdout="output\n", stderr="")

        result = agent.run_applescript('tell application "Finder" to activate')

        self.assertEqual(result, "output")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "osascript")
        self.assertEqual(args[1], "-e")

    @patch("lsimons_auto.actions.agent.subprocess.run")
    def test_run_applescript_failure(self, mock_run: Mock) -> None:
        """Test AppleScript failure handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["osascript"], stderr="Error message"
        )

        with self.assertRaises(RuntimeError) as cm:
            agent.run_applescript("invalid script")
        self.assertIn("AppleScript failed", str(cm.exception))

    @patch("lsimons_auto.actions.agent.subprocess.run")
    def test_run_applescript_not_found(self, mock_run: Mock) -> None:
        """Test handling when osascript is not found."""
        mock_run.side_effect = FileNotFoundError()

        with self.assertRaises(RuntimeError) as cm:
            agent.run_applescript("any script")
        self.assertIn("osascript not found", str(cm.exception))


class TestCLIHelp(unittest.TestCase):
    """Test CLI help output."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test environment."""
        cls.project_root = Path(__file__).parent.parent
        cls.agent_script = cls.project_root / "lsimons_auto" / "actions" / "agent.py"

        if not cls.agent_script.exists():
            raise unittest.SkipTest(f"Agent script not found: {cls.agent_script}")

    def test_cli_main_help(self) -> None:
        """Test main help output."""
        result = subprocess.run(
            [sys.executable, str(self.agent_script), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("spawn", result.stdout)
        self.assertIn("send", result.stdout)
        self.assertIn("broadcast", result.stdout)
        self.assertIn("focus", result.stdout)
        self.assertIn("list", result.stdout)
        self.assertIn("close", result.stdout)
        self.assertIn("kill", result.stdout)

    def test_cli_spawn_help(self) -> None:
        """Test spawn subcommand help."""
        result = subprocess.run(
            [sys.executable, str(self.agent_script), "spawn", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--subagents", result.stdout)
        self.assertIn("--command", result.stdout)
        self.assertIn("--no-zed", result.stdout)

    def test_cli_list_help(self) -> None:
        """Test list subcommand help."""
        result = subprocess.run(
            [sys.executable, str(self.agent_script), "list", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--verbose", result.stdout)


class TestCmdList(unittest.TestCase):
    """Test list command execution."""

    def test_cmd_list_empty(self) -> None:
        """Test list command with no sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                parser = agent.create_parser()
                args = parser.parse_args(["list"])
                # Should not raise
                agent.cmd_list(args)

    def test_cmd_list_with_sessions(self) -> None:
        """Test list command with sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True)

            session_data: dict[str, object] = {
                "session_id": "test-session",
                "workspace_path": "/test/path",
                "repo_name": "test-repo",
                "org_name": "test-org",
                "created_at": "2026-01-21T00:00:00Z",
                "panes": [],
            }
            with open(sessions_dir / "test-session.json", "w") as f:
                json.dump(session_data, f)

            with patch.object(agent, "SESSIONS_DIR", sessions_dir):
                parser = agent.create_parser()
                args = parser.parse_args(["list", "-v"])
                # Should not raise
                agent.cmd_list(args)


if __name__ == "__main__":
    unittest.main()
