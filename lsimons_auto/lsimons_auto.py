#!/usr/bin/env python3
"""
lsimons_auto.py - Command dispatcher for lsimons-auto actions

This script acts as a unified CLI interface that routes subcommands to
corresponding action scripts in the actions/ directory.

See AGENTS.md for agent instructions and DESIGN.md for design decisions.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from lsimons_auto.logging_utils import get_logger


def discover_actions() -> dict[str, Path]:
    """Discover available action scripts in the actions directory.

    Returns a dict mapping CLI command names (with dashes) to script paths.
    E.g., 'git-sync' -> Path('.../actions/git_sync.py')
    """
    # Determine project root relative to this script file
    # This script is at lsimons_auto/lsimons_auto.py
    # So project root is the parent directory
    script_dir = Path(__file__).parent
    actions_dir = script_dir / "actions"
    actions: dict[str, Path] = {}

    if not actions_dir.exists():
        return actions

    for file_path in actions_dir.glob("*.py"):
        if file_path.name != "__init__.py":
            # Convert Python naming (underscores) to CLI naming (dashes)
            action_name = file_path.stem.replace("_", "-")
            actions[action_name] = file_path

    return actions


def normalize_action_name(name: str) -> str:
    """Normalize action name to CLI convention (dashes).

    Accepts both 'git-sync' and 'git_sync', returns 'git-sync'.
    """
    return name.replace("_", "-")


def main() -> None:
    """Main dispatcher function."""
    logger = get_logger("lsimons_auto.dispatcher")
    parser = argparse.ArgumentParser(description="lsimons-auto command dispatcher", prog="auto")

    actions = discover_actions()

    if not actions:
        logger.error("No actions found in actions directory")
        logger.error(f"Expected location: {Path(__file__).parent / 'actions'}")
        sys.exit(1)

    # Parse arguments manually to handle unknown actions gracefully
    if len(sys.argv) < 2:
        parser.print_help()
        print("\nAvailable actions:")
        for name in sorted(actions.keys()):
            print(f"  {name:<24} Run {name} action")
        print("\nUse 'auto <action> --help' for help on a specific action")
        return

    action_input = sys.argv[1]
    remaining = sys.argv[2:]

    # Handle help for dispatcher
    if action_input in ["-h", "--help"]:
        parser.print_help()
        logger.info("\nAvailable actions:")
        for name in sorted(actions.keys()):
            logger.info(f"  {name:<24} Run {name} action")
        logger.info("\nUse 'auto <action> --help' for help on a specific action")
        return

    # Normalize action name (accept both dashes and underscores)
    action_name = normalize_action_name(action_input)

    if action_name not in actions:
        logger.error(f"Unknown action '{action_input}'")
        logger.error("\nAvailable actions:")
        for name in sorted(actions.keys()):
            logger.error(f"  {name}")
        sys.exit(1)

    # Execute the action script using subprocess
    action_script = actions[action_name]
    cmd = [sys.executable, str(action_script)] + remaining

    try:
        logger.info(f"Executing action '{action_name}' with command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)  # Don't raise on non-zero exit
        sys.exit(result.returncode)
    except FileNotFoundError:
        logger.error(f"Action script not found: {action_script}")
        logger.error("This usually indicates an installation or configuration problem.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error executing action '{action_name}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
