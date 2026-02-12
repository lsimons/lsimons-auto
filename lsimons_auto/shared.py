"""
shared.py - Shared utility functions for lsimons-auto actions

Provides common functionality used across multiple actions including
subprocess handling, path validation, and error management.
"""

import subprocess
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any


class CommandError(Exception):
    """Exception raised when a subprocess command fails."""

    def __init__(self, command: list[str] | str, returncode: int, output: str = ""):
        self.command = command
        self.returncode = returncode
        self.output = output
        super().__init__(f"Command failed with exit code {returncode}: {' '.join(command) if isinstance(command, list) else command}")

    def __str__(self) -> str:
        msg = f"Command failed (exit code {self.returncode}): {self.command}"
        if self.output:
            msg += f"\nOutput:\n{self.output}"
        return msg


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str] | subprocess.CalledProcessError:
    """
    Run a subprocess command with consistent error handling.

    Args:
        cmd: Command and arguments as a list
        cwd: Working directory for the command
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise CommandError on non-zero exit

    Returns:
        CompletedProcess object with the command results,
        or CalledProcessError if check=False and command fails

    Raises:
        CommandError: If check=True and command fails
        FileNotFoundError: If the command executable is not found
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            raise CommandError(cmd, e.returncode, e.stdout or e.stderr) from e
        return e
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Command not found: {cmd[0]}") from e


def get_command_output(
    cmd: list[str],
    cwd: Path | None = None,
    default: str | None = None,
) -> str | None:
    """
    Run a command and return its stdout.

    Args:
        cmd: Command and arguments as a list
        cwd: Working directory for the command
        default: Value to return if command fails (None to raise CommandError)

    Returns:
        Command stdout stripped, or default if command fails and default is provided

    Raises:
        CommandError: If command fails and default is None
    """
    try:
        result = run_command(cmd, cwd=cwd, capture_output=True, check=True)
        return result.stdout.strip()
    except CommandError:
        if default is not None:
            return default
        raise


def run_background_command(cmd: str) -> int:
    """
    Launch a command in the background.

    Args:
        cmd: Command string to execute

    Returns:
        Process ID of the launched process

    Raises:
        CommandError: If the command cannot be started
    """
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process.pid
    except (OSError, subprocess.SubprocessError) as e:
        raise CommandError(cmd, 1) from e


def validate_path_in_directory(path: Path, base_dir: Path) -> Path:
    """
    Validate that a path is within a base directory.

    Args:
        path: Path to validate
        base_dir: Base directory that path must be within

    Returns:
        The resolved, validated path

    Raises:
        ValueError: If path escapes base_dir
    """
    resolved_path = path.resolve()
    resolved_base = base_dir.resolve()

    try:
        resolved_path.relative_to(resolved_base)
        return resolved_path
    except ValueError as e:
        raise ValueError(f"Path {resolved_path} is not within base directory {resolved_base}") from e


def ensure_directory(path: Path, mode: int = 0o755) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
        mode: Permission mode for created directories

    Returns:
        The verified directory path
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        if mode:
            path.chmod(mode)
    return path


def safe_path_join(*parts: str | Path) -> Path:
    """
    Safely join path parts, expanding user paths.

    Args:
        *parts: Path components as strings or Path objects

    Returns:
        Joined and expanded Path

    Raises:
        ValueError: If no valid path parts are provided
    """
    result_parts: list[Path] = []
    for part in parts:
        if isinstance(part, str):
            part = Path(part).expanduser()
        result_parts.append(part)

    if not result_parts:
        raise ValueError("At least one path part must be provided")

    result = result_parts[0]
    for part in result_parts[1:]:
        result = result / part

    return result


class DryRunContext(AbstractContextManager[bool]):
    """Context manager for dry-run operations that can suppress side effects."""

    def __init__(self, dry_run: bool, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self._actions: list[str] = []

    def would_execute(self) -> bool:
        """Return True if action would be executed (not in dry-run mode)."""
        return not self.dry_run

    def record_action(self, description: str) -> None:
        """Record a dry-run action description."""
        if self.dry_run and self.verbose:
            print(f"[DRY RUN] Would: {description}")
        self._actions.append(description)

    def get_recorded_actions(self) -> list[str]:
        """Get list of all recorded actions."""
        return list(self._actions)

    def __enter__(self) -> bool:
        return self.would_execute()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        return False