#!/usr/bin/env python3
"""
copilot action: Activate Microsoft 365 Copilot and paste clipboard content.

This action invokes the ask_m365_copilot.scpt AppleScript which:
- Activates the Microsoft 365 Copilot GUI
- Attempts to paste clipboard content into the chat buffer
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point for the copilot action.

    Args:
        args: Command-line arguments (None uses sys.argv)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Activate Microsoft 365 Copilot and paste clipboard content"
    )
    parser.parse_args(args)

    # Find the AppleScript file
    script_path = Path(__file__).parent / "ask_m365_copilot.scpt"
    if not script_path.exists():
        print(f"Error: AppleScript not found at {script_path}", file=sys.stderr)
        return 1

    # Execute the AppleScript
    try:
        result = subprocess.run(
            ["osascript", str(script_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout.strip())
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error executing AppleScript: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr.strip(), file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(
            "Error: osascript command not found. Are you running on macOS?",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
