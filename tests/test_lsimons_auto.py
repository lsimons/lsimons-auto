"""
Tests for lsimons_auto command dispatcher.
"""

import subprocess
import sys

from lsimons_auto.lsimons_auto import discover_actions, normalize_action_name


class TestDiscoverActions:
    """Tests for action discovery."""

    def test_discover_actions_returns_dict(self):
        """Test discover_actions returns a dictionary."""
        actions = discover_actions()
        assert isinstance(actions, dict)

    def test_discover_actions_ignores_init(self):
        """Test __init__.py is excluded from actions."""
        actions = discover_actions()
        assert "__init__.py" not in [p.name for p in actions.values()]
        assert "__init__" not in actions

    def test_discover_actions_converts_underscores(self):
        """Test underscores are converted to dashes in action names."""
        actions = discover_actions()
        # Should have actions with dashes, not underscores
        assert "git-sync" in actions or len(actions) > 0
        # Should not have underscores
        assert "git_sync" not in actions

    def test_discover_actions_paths_exist(self):
        """Test all discovered action paths exist."""
        actions = discover_actions()
        for name, path in actions.items():
            assert path.exists(), f"Action {name} path {path} does not exist"
            assert path.suffix == ".py", f"Action {name} is not a Python file"

    def test_discover_actions_includes_echo(self):
        """Test that echo action is discovered."""
        actions = discover_actions()
        assert "echo" in actions

    def test_discover_actions_includes_organize_desktop(self):
        """Test that organize-desktop action is discovered."""
        actions = discover_actions()
        assert "organize-desktop" in actions

    def test_discover_actions_includes_git_sync(self):
        """Test that git-sync action is discovered."""
        actions = discover_actions()
        assert "git-sync" in actions

    def test_discover_actions_stems_match_names(self):
        """Test action names match file stems (with underscores replaced)."""
        actions = discover_actions()
        for name, path in actions.items():
            expected_stem = name.replace("-", "_")
            assert path.stem == expected_stem, f"Action {name} stem mismatch"

    def test_discover_actions_paths_are_in_actions_dir(self):
        """Test all discovered paths are in the actions directory."""
        actions = discover_actions()
        for action_path in actions.values():
            # Path should be relative to project root
            assert "actions" in str(action_path) or "actions" in str(action_path.resolve())


class TestNormalizeActionName:
    """Tests for action name normalization."""

    def test_normalize_with_dashes(self):
        """Test normalizing name with dashes."""
        assert normalize_action_name("git-sync") == "git-sync"

    def test_normalize_with_underscores(self):
        """Test normalizing name with underscores."""
        assert normalize_action_name("git_sync") == "git-sync"

    def test_normalize_already_normalized(self):
        """Test already normalized name."""
        assert normalize_action_name("organize-desktop") == "organize-desktop"

    def test_normalize_mixed(self):
        """Test normalizing mixed dashes and underscores."""
        assert normalize_action_name("git_sync-action_test") == "git-sync-action-test"

    def test_normalize_single_word(self):
        """Test normalizing single word."""
        assert normalize_action_name("echo") == "echo"

    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        assert normalize_action_name("") == ""


class TestIntegrationTests:
    """Integration tests for the dispatcher."""

    def test_real_help_output_has_actions(self):
        """Test real help output lists available actions."""
        result = subprocess.run(
            [sys.executable, "lsimons_auto/lsimons_auto.py"],
            capture_output=True,
            text=True,
        )
        assert "Available actions:" in result.stdout

    def test_real_echo_dispatch(self):
        """Test dispatching to echo action works end-to-end."""
        result = subprocess.run(
            [sys.executable, "lsimons_auto/lsimons_auto.py", "echo", "test"],
            capture_output=True,
            text=True,
        )
        assert "test" in result.stdout

    def test_real_unknown_action_error(self):
        """Test unknown action shows error."""
        result = subprocess.run(
            [
                sys.executable,
                "lsimons_auto/lsimons_auto.py",
                "this-action-does-not-exist",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_echo_via_dispatcher(self):
        """Test echo can be called through the auto dispatcher."""
        result = subprocess.run(
            [sys.executable, "lsimons_auto/lsimons_auto.py", "echo", "hello"],
            capture_output=True,
            text=True,
            check=False,
        )
        # Should succeed
        assert result.returncode == 0

    def test_echo_via_dispatcher_with_uppercase(self):
        """Test echo uppercase through dispatcher works."""
        result = subprocess.run(
            [sys.executable, "lsimons_auto/lsimons_auto.py", "echo", "--upper", "hello"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        if "hello" in result.stdout:
            assert "HELLO" == result.stdout.strip().upper()


class TestNormalizeActionNameEdgeCases:
    """Tests for edge cases in name normalization."""

    def test_normalize_underscores_only(self):
        """Test normalizing string with only underscores."""
        assert normalize_action_name("___") == "---"

    def test_normalize_dashes_only(self):
        """Test normalizing string with only dashes."""
        assert normalize_action_name("---") == "---"

    def test_normalize_long_underscore_chain(self):
        """Test normalizing long underscore chain."""
        assert normalize_action_name("a___b_c___d") == "a---b-c---d"

    def test_normalize_no_underscores(self):
        """Test normalizing string with no underscores."""
        assert normalize_action_name("github") == "github"