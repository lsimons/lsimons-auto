#!/usr/bin/env python3
"""
launch_apps.py - Launch predefined applications and commands in the background

This action launches a hardcoded list of applications and commands that should
run in the background for daily workflow setup.
"""

import argparse
import subprocess
import sys
from typing import Optional


# Hardcoded list of commands to launch
LAUNCH_COMMANDS = [
    "open -g -a /System/Applications/TextEdit.app ~/scratch.txt",
    "open -g /Applications/Ghostty.app",
    "open -g -a '/Applications/Brave Browser.app' 'https://schubergphilis.okta-emea.com/'",
    "open -g /Applications/Slack.app",
    "open -g '/Applications/Zed.app'",
    "open -g '/Applications/Microsoft Outlook.app'",
    "open -g '/Applications/Microsoft Teams.app'",
    "open -g '/Applications/Microsoft Word.app'",
    "open -g '/Applications/Microsoft Excel.app'",
    "open -g '/Applications/Microsoft PowerPoint.app'",
    "open -g '/Users/lsimons/Applications/IntelliJ IDEA Ultimate.app'",
    # Add more commands here as needed
]


def launch_command(command: str) -> bool:
    """Launch a single command in the background."""
    try:
        print(f"Launching: {command}")

        # Use subprocess.Popen to launch command in background
        # start_new_session=True ensures the process runs independently
        process = subprocess.Popen(
            command,
            shell=True,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print(f"  → Process started with PID: {process.pid}")
        return True

    except Exception as e:
        print(f"  → Error launching command: {e}")
        return False


def launch_all_apps() -> None:
    """Launch all predefined applications and commands."""
    if not LAUNCH_COMMANDS:
        print("No commands configured to launch")
        return

    print(f"Launching {len(LAUNCH_COMMANDS)} command(s)...")

    success_count = 0
    total_count = len(LAUNCH_COMMANDS)

    for command in LAUNCH_COMMANDS:
        if launch_command(command):
            success_count += 1

    print(
        f"\nLaunch completed: {success_count}/{total_count} commands started successfully"
    )

    if success_count < total_count:
        print("Some commands failed to launch. Check the output above for details.")


def main(args: Optional[list[str]] = None) -> None:
    """Main function to launch predefined apps."""
    parser = argparse.ArgumentParser(
        description="Launch predefined applications and commands in the background"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all configured commands without launching them",
    )

    parsed_args = parser.parse_args(args)

    if parsed_args.list:
        print("Configured launch commands:")
        for i, command in enumerate(LAUNCH_COMMANDS, 1):
            print(f"  {i}. {command}")
        return

    try:
        launch_all_apps()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching apps: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
