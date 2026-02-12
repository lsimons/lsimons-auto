"""
Tests for shared utility functions.
"""

import tempfile
import pytest
from pathlib import Path

from lsimons_auto.shared import (
    CommandError,
    run_command,
    get_command_output,
    run_background_command,
    validate_path_in_directory,
    ensure_directory,
    safe_path_join,
    DryRunContext,
)


class TestRunCommand:
    """Tests for run_command function."""

    def test_run_command_success(self):
        """Test successful command execution."""
        result = run_command(["echo", "hello"])
        assert result.returncode == 0
        assert result.stdout.strip() == "hello"

    def test_run_command_with_cwd(self):
        """Test command with working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command(["pwd"], cwd=Path(tmpdir))
            assert result.returncode == 0
            # Resolve both paths to handle macOS tempdir symlinks
            assert Path(result.stdout.strip()).resolve() == Path(tmpdir).resolve()

    def test_run_command_failure_with_check(self):
        """Test command failure raises CommandError when check=True."""
        with pytest.raises(CommandError) as exc_info:
            run_command(["false"], check=True)
        assert exc_info.value.returncode != 0

    def test_run_command_failure_without_check(self):
        """Test command failure returns result when check=False."""
        result = run_command(["false"], check=False)
        assert result.returncode != 0

    def test_run_command_not_found(self):
        """Test FileNotFoundError for non-existent command."""
        with pytest.raises(FileNotFoundError):
            run_command(["this-command-does-not-exist-xyz123"])

    def test_run_command_capture_output(self):
        """Test output capture behavior."""
        result = run_command(["echo", "test"], capture_output=True)
        assert "test" in result.stdout

        result = run_command(["echo", "test"], capture_output=False)
        # subprocess.run returns None for stdout when capture_output=False
        assert result.stdout is None

    def test_run_command_with_list_args(self):
        """Test command with list arguments."""
        result = run_command(["echo", "a", "b", "c"])
        assert result.stdout.strip() == "a b c"

    def test_command_error_str_representation(self):
        """Test CommandError string representation."""
        error = CommandError(["test", "cmd"], 1, "output text")
        error_str = str(error)
        assert "exit code 1" in error_str
        # Error shows list representation for list commands
        assert "test" in error_str and "cmd" in error_str
        assert "output text" in error_str


class TestGetCommandOutput:
    """Tests for get_command_output function."""

    def test_get_command_output_success(self):
        """Test successful output retrieval."""
        output = get_command_output(["echo", "hello"])
        assert output == "hello"

    def test_get_command_output_default_on_failure(self):
        """Test default value returned on failure."""
        output = get_command_output(["false"], default="fallback")
        assert output == "fallback"

    def test_get_command_output_raises_on_failure_no_default(self):
        """Test exception raised on failure without default."""
        with pytest.raises(CommandError):
            get_command_output(["false"])

    def test_get_command_output_with_cwd(self):
        """Test output retrieval with working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = get_command_output(["pwd"], cwd=Path(tmpdir))
            # Resolve both paths to handle macOS tempdir symlinks
            assert Path(output).resolve() == Path(tmpdir).resolve()

    def test_get_command_output_empty_output(self):
        """Test handling of empty output."""
        output = get_command_output(["true"])
        assert output == ""

    def test_get_command_output_whitespace_stripped(self):
        """Test whitespace is stripped from output."""
        output = get_command_output(["echo", "  test  "])
        assert output == "test"


class TestRunBackgroundCommand:
    """Tests for run_background_command function."""

    def test_run_background_command_success(self):
        """Test successful background command launch."""
        pid = run_background_command("sleep 0.1")
        assert isinstance(pid, int)
        assert pid > 0

    def test_run_background_command_invalid(self):
        """Test invalid background command."""
        # The shell will return a non-zero exit code for invalid commands
        # The function returns the PID which may be valid even for failed commands
        pid = run_background_command("exit 1")
        assert isinstance(pid, int)


class TestValidatePathInDirectory:
    """Tests for validate_path_in_directory function."""

    def test_validate_path_within_directory(self):
        """Test path within directory is valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            test_path = base_dir / "sub" / "file.txt"
            test_path.parent.mkdir()

            result = validate_path_in_directory(test_path, base_dir)
            # Resolve both paths to handle macOS tempdir symlinks
            assert result.resolve() == test_path.resolve()

    def test_validate_path_exactly_base_directory(self):
        """Test path exactly equal to base directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            result = validate_path_in_directory(base_dir, base_dir)
            # Resolve both paths to handle macOS tempdir symlinks
            assert result.resolve() == base_dir.resolve()

    def test_validate_path_escapes_directory(self):
        """Test path escaping directory raises error."""
        base_dir = Path("/some/dir")
        test_path = Path("/other/dir/file.txt")

        with pytest.raises(ValueError, match="is not within base directory"):
            validate_path_in_directory(test_path, base_dir)

    def test_validate_path_relative_to_parent(self):
        """Test path using .. to escape raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            test_path = base_dir / "sub" / ".." / ".." / "other"
            test_path = test_path.resolve()

            if not test_path.is_relative_to(base_dir):
                with pytest.raises(ValueError):
                    validate_path_in_directory(test_path, base_dir)

    def test_validate_path_resolves_symlinks(self):
        """Test path resolution handles symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            test_dir = base_dir / "sub"
            test_dir.mkdir()

            link_dir = base_dir / "link"
            link_dir.symlink_to(test_dir)

            # Path inside symlinked directory should be valid
            test_path = link_dir / "file.txt"
            result = validate_path_in_directory(test_path, base_dir)
            assert result.resolve().is_relative_to(base_dir.resolve())


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_ensure_existing_directory(self):
        """Test existing directory is returned unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / "existing"
            existing.mkdir()

            result = ensure_directory(existing)
            assert result == existing
            assert result.exists()

    def test_ensure_create_new_directory(self):
        """Test new directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"

            result = ensure_directory(new_dir)
            assert result == new_dir
            assert result.exists()
            assert result.is_dir()

    def test_ensure_directory_idempotent(self):
        """Test multiple calls are safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "test"

            ensure_directory(new_dir)
            ensure_directory(new_dir)
            ensure_directory(new_dir)

            assert new_dir.exists()

    def test_ensure_directory_with_mode(self):
        """Test directory creation with specific mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "restricted"

            # Use a conservative mode that should work
            result = ensure_directory(new_dir, mode=0o700)
            assert result.exists()
            # Note: Actual mode may be affected by umask

    def test_ensure_directory_creates_parents(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "a" / "b" / "c" / "d"

            ensure_directory(nested)
            assert nested.exists()
            assert nested.is_dir()


class TestSafePathJoin:
    """Tests for safe_path_join function."""

    def test_safe_path_join_strings(self):
        """Test joining string paths."""
        result = safe_path_join("/home", "user", "documents")
        assert str(result).endswith("home/user/documents")

    def test_safe_path_join_with_path_objects(self):
        """Test joining Path objects."""
        result = safe_path_join(Path("/home"), Path("user"), Path("docs"))
        assert str(result).endswith("home/user/docs")

    def test_safe_path_join_mixed(self):
        """Test joining mixed string and Path objects."""
        result = safe_path_join("/home", Path("user"), "docs")
        assert str(result).endswith("home/user/docs")

    def test_safe_path_join_expands_tilde(self):
        """Test tilde expansion."""
        result = safe_path_join("~", "documents")
        assert "~" not in str(result)
        assert str(result).endswith("documents")

    def test_safe_path_join_single_part(self):
        """Test joining a single part."""
        result = safe_path_join("/home")
        assert "home" in str(result)

    def test_safe_path_join_empty_parts_raises(self):
        """Test that no path parts raise error."""
        with pytest.raises(ValueError, match="At least one path part"):
            safe_path_join()

    def test_safe_path_join_empty_parts(self):
        """Test joining with empty path parts."""
        result = safe_path_join("", "user", "")
        assert "user" in str(result)


class TestDryRunContext:
    """Tests for DryRunContext class."""

    def test_dry_run_mode_false(self):
        """Test dry-run mode False would execute."""
        ctx = DryRunContext(dry_run=False)
        assert ctx.would_execute() is True

    def test_dry_run_mode_true(self):
        """Test dry-run mode True would not execute."""
        ctx = DryRunContext(dry_run=True)
        assert ctx.would_execute() is False

    def test_dry_run_context_manager_false(self):
        """Test context manager with dry_run=False returns True."""
        with DryRunContext(dry_run=False) as should_execute:
            assert should_execute is True

    def test_dry_run_context_manager_true(self):
        """Test context manager with dry_run=True returns False."""
        with DryRunContext(dry_run=True) as should_execute:
            assert should_execute is False

    def test_record_action_not_dry_run(self):
        """Test action recording when not in dry-run mode."""
        ctx = DryRunContext(dry_run=False, verbose=True)
        ctx.record_action("test action")
        assert ctx.get_recorded_actions() == ["test action"]

    def test_record_action_with_dry_run_verbose(self):
        """Test action recording prints in dry-run verbose mode."""
        ctx = DryRunContext(dry_run=True, verbose=True)
        # Should print but not raise
        ctx.record_action("test action")
        assert "test action" in ctx.get_recorded_actions()

    def test_record_action_with_dry_run_not_verbose(self):
        """Test action recording silent in dry-run non-verbose mode."""
        ctx = DryRunContext(dry_run=True, verbose=False)
        # Should not raise
        ctx.record_action("test action")
        assert "test action" in ctx.get_recorded_actions()

    def test_get_recorded_actions_returns_copy(self):
        """Test that get_recorded_actions returns a copy."""
        ctx = DryRunContext(dry_run=True)
        ctx.record_action("action1")

        actions = ctx.get_recorded_actions()
        actions.append("action2")

        # Original list should be unchanged
        assert ctx.get_recorded_actions() == ["action1"]

    def test_multiple_recorded_actions(self):
        """Test recording multiple actions."""
        ctx = DryRunContext(dry_run=True)
        ctx.record_action("action1")
        ctx.record_action("action2")
        ctx.record_action("action3")

        actions = ctx.get_recorded_actions()
        assert actions == ["action1", "action2", "action3"]

    def test_context_manager_suppression(self):
        """Test context manager does not suppress exceptions."""
        ctx = DryRunContext(dry_run=True)
        # __exit__ returns False, so exceptions should propagate
        with pytest.raises(ValueError, match="Should not be suppressed"):
            with ctx:
                raise ValueError("Should not be suppressed")

    def test_exit_behavior_dry_run(self):
        """Test context exit in dry-run mode."""
        ctx = DryRunContext(dry_run=True)
        result = ctx.__exit__(None, None, None)
        assert result is False

    def test_exit_behavior_normal(self):
        """Test context exit in normal mode."""
        ctx = DryRunContext(dry_run=False)
        result = ctx.__exit__(None, None, None)
        assert result is False