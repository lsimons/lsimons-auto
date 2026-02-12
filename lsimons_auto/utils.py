"""
Utility functions for lsimons-auto actions.

This module provides common patterns used across multiple actions to reduce
code duplication and improve maintainability.
"""

import subprocess
import sys
from typing import NoReturn


def handle_error(message: str, exception: Exception, exit_code: int = 1) -> NoReturn:
    """
    Handle errors consistently across all actions.

    Args:
        message: Error message to display
        exception: The exception that was raised
        exit_code: Exit code to use (default: 1)
    """
    print(f"{message}: {exception}", file=sys.stderr)
    sys.exit(exit_code)


def run_command(
    cmd: list[str],
    error_message: str | None = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """
    Run a subprocess command with consistent error handling.

    Args:
        cmd: Command and arguments as a list
        error_message: Optional custom error message (default: command string)
        check: Whether to exit on non-zero return code (default: True)
        capture_output: Whether to capture stdout/stderr (default: True)

    Returns:
        CompletedProcess object with result

    Raises:
        SystemExit: If check=True and command fails
    """
    result: subprocess.CompletedProcess[str]
    if capture_output:
        result = subprocess.run(cmd, capture_output=True, text=True)
    else:
        result = subprocess.run(cmd, text=True)

    if result.returncode != 0 and check:
        msg = error_message or f"Command failed: {' '.join(cmd)}"
        if result.stderr:
            print(f"{msg}\n{result.stderr}", file=sys.stderr)
        else:
            print(msg, file=sys.stderr)
        sys.exit(result.returncode)

    return result
