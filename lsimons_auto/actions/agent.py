#!/usr/bin/env python3
"""
agent.py - Manage multiple Claude Code CLI instances in Ghostty terminal

Spawns Ghostty windows with configurable agent pane layouts, integrates with
Zed editor, and provides session management for multi-agent workflows.
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Constants
APPLESCRIPT_DELAY = 0.3  # seconds between AppleScript actions
SESSIONS_DIR = Path.home() / ".config" / "auto" / "agent" / "sessions"
GIT_ROOT = Path.home() / "git"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AgentPane:
    """Represents a single agent pane in the session."""

    id: str  # e.g., "M-lsimons-auto" or "001-lsimons-auto"
    pane_index: int  # 0 for main, 1+ for subagents
    command: str  # e.g., "claude" or "pi"
    is_main: bool


@dataclass
class AgentSession:
    """Represents an active agent session."""

    session_id: str  # e.g., "auto-agent-20260121-143052"
    workspace_path: str  # e.g., "/Users/lsimons/git/lsimons/lsimons-auto"
    repo_name: str  # e.g., "lsimons-auto"
    org_name: str  # e.g., "lsimons"
    created_at: str  # ISO timestamp
    panes: list[AgentPane] = field(default_factory=list)

    @classmethod
    def load(cls, session_id: str) -> "AgentSession":
        """Load session from disk."""
        session_file = SESSIONS_DIR / f"{session_id}.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        with open(session_file) as f:
            data = json.load(f)
        panes = [AgentPane(**p) for p in data.pop("panes", [])]
        return cls(**data, panes=panes)

    def save(self) -> None:
        """Persist session to disk."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session_file = SESSIONS_DIR / f"{self.session_id}.json"
        with open(session_file, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def delete(self) -> None:
        """Remove session file from disk."""
        session_file = SESSIONS_DIR / f"{self.session_id}.json"
        if session_file.exists():
            session_file.unlink()


# =============================================================================
# Workspace Discovery
# =============================================================================


def discover_workspaces(
    git_root: Optional[Path] = None,
) -> dict[str, dict[str, Path]]:
    """
    Scan ~/git for org/repo structure.
    Returns: {"org_name": {"repo_name": Path, ...}, ...}
    """
    if git_root is None:
        git_root = GIT_ROOT

    workspaces: dict[str, dict[str, Path]] = {}

    if not git_root.exists():
        return workspaces

    for org_dir in git_root.iterdir():
        if not org_dir.is_dir() or org_dir.name.startswith("."):
            continue

        repos: dict[str, Path] = {}
        for repo_dir in org_dir.iterdir():
            if repo_dir.is_dir() and not repo_dir.name.startswith("."):
                repos[repo_dir.name] = repo_dir

        if repos:
            workspaces[org_dir.name] = repos

    return workspaces


def fuzzy_match_workspace(
    query_org: str,
    query_repo: str,
    workspaces: dict[str, dict[str, Path]],
) -> tuple[str, str, Path]:
    """
    Fuzzy match org and repo names (case-insensitive substring).
    Returns (org, repo, path).
    Raises ValueError if ambiguous or not found.
    """
    matching_orgs = [o for o in workspaces if query_org.lower() in o.lower()]

    if len(matching_orgs) == 0:
        raise ValueError(f"No org found matching '{query_org}'")
    if len(matching_orgs) > 1:
        raise ValueError(f"Ambiguous org match for '{query_org}': {matching_orgs}")

    org = matching_orgs[0]
    repos = workspaces[org]

    matching_repos = [r for r in repos if query_repo.lower() in r.lower()]

    if len(matching_repos) == 0:
        raise ValueError(f"No repo found matching '{query_repo}' in org '{org}'")
    if len(matching_repos) > 1:
        raise ValueError(f"Ambiguous repo match for '{query_repo}': {matching_repos}")

    repo = matching_repos[0]
    return (org, repo, repos[repo])


# =============================================================================
# AppleScript Helpers
# =============================================================================


def run_applescript(script: str) -> str:
    """Execute AppleScript and return output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AppleScript failed: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError("osascript not found. This action requires macOS.") from None


def activate_app(app: str) -> None:
    """Activate (bring to front) an application."""
    script = f'tell application "{app}" to activate'
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def keystroke(app: str, key: str, modifiers: Optional[list[str]] = None) -> None:
    """Send keystroke to application."""
    mod_str = ""
    if modifiers:
        mod_str = " using {" + ", ".join(f"{m} down" for m in modifiers) + "}"

    script = f'''
    tell application "{app}" to activate
    delay 0.1
    tell application "System Events"
        tell process "{app}"
            keystroke "{key}"{mod_str}
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def key_code(app: str, code: int, modifiers: Optional[list[str]] = None) -> None:
    """Send key code to application."""
    mod_str = ""
    if modifiers:
        mod_str = " using {" + ", ".join(f"{m} down" for m in modifiers) + "}"

    script = f'''
    tell application "{app}" to activate
    delay 0.1
    tell application "System Events"
        tell process "{app}"
            key code {code}{mod_str}
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def send_text(app: str, text: str) -> None:
    """Type text into the focused application."""
    # Escape special characters for AppleScript
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')

    script = f'''
    tell application "{app}" to activate
    delay 0.1
    tell application "System Events"
        tell process "{app}"
            keystroke "{escaped}"
        end tell
    end tell
    '''
    run_applescript(script)
    time.sleep(APPLESCRIPT_DELAY)


def press_return(app: str) -> None:
    """Press return/enter key."""
    key_code(app, 36)  # 36 = return key


# =============================================================================
# Ghostty Control
# =============================================================================


def ghostty_new_window() -> None:
    """Create a new Ghostty window."""
    keystroke("Ghostty", "n", ["command"])
    time.sleep(0.5)  # Extra delay for window creation


def ghostty_split_right() -> None:
    """Split current pane horizontally (Cmd+D)."""
    keystroke("Ghostty", "d", ["command"])


def ghostty_split_down() -> None:
    """Split current pane vertically (Cmd+Shift+D)."""
    keystroke("Ghostty", "D", ["command", "shift"])


def ghostty_focus_direction(direction: str) -> None:
    """Focus pane in given direction using Option+Arrow."""
    # Key codes: left=123, right=124, down=125, up=126
    key_codes = {"left": 123, "right": 124, "down": 125, "up": 126}
    if direction not in key_codes:
        raise ValueError(f"Invalid direction: {direction}. Use: left, right, up, down")
    key_code("Ghostty", key_codes[direction], ["option"])


def ghostty_close_pane() -> None:
    """Close current pane (Cmd+W)."""
    keystroke("Ghostty", "w", ["command"])


def ghostty_run_command(cmd: str) -> None:
    """Type and execute a command in Ghostty."""
    send_text("Ghostty", cmd)
    press_return("Ghostty")
    time.sleep(APPLESCRIPT_DELAY)


# =============================================================================
# Layout Creation
# =============================================================================


def create_layout(
    num_subagents: int,
    workspace_path: Path,
    command: str,
    repo_name: str,
) -> list[AgentPane]:
    """
    Create Ghostty layout with main + subagent panes.
    Returns list of AgentPane objects.
    """
    panes: list[AgentPane] = []

    # Launch Ghostty with new window
    activate_app("Ghostty")
    ghostty_new_window()

    # Change to workspace directory
    ghostty_run_command(f"cd {workspace_path}")

    # Main pane
    main_pane = AgentPane(
        id=f"M-{repo_name}",
        pane_index=0,
        command=command,
        is_main=True,
    )
    panes.append(main_pane)

    if num_subagents >= 1:
        # Split right for first subagent
        ghostty_split_right()
        ghostty_run_command(f"cd {workspace_path}")
        panes.append(
            AgentPane(
                id=f"001-{repo_name}",
                pane_index=1,
                command=command,
                is_main=False,
            )
        )

    if num_subagents >= 2:
        # Split down for second subagent
        ghostty_split_down()
        ghostty_run_command(f"cd {workspace_path}")
        panes.append(
            AgentPane(
                id=f"002-{repo_name}",
                pane_index=2,
                command=command,
                is_main=False,
            )
        )

    if num_subagents >= 3:
        # Split down again for third subagent
        ghostty_split_down()
        ghostty_run_command(f"cd {workspace_path}")
        panes.append(
            AgentPane(
                id=f"003-{repo_name}",
                pane_index=3,
                command=command,
                is_main=False,
            )
        )

    if num_subagents >= 4:
        # For 4 subagents: focus up to s1, split right, split down
        # Current layout: main | s1/s2/s3
        # Target: main | s1/s2 | s3/s4
        ghostty_focus_direction("up")
        ghostty_focus_direction("up")  # Now at s1
        ghostty_split_right()
        ghostty_run_command(f"cd {workspace_path}")
        panes.append(
            AgentPane(
                id=f"003-{repo_name}",
                pane_index=3,
                command=command,
                is_main=False,
            )
        )
        ghostty_split_down()
        ghostty_run_command(f"cd {workspace_path}")
        # Re-number panes 3 and 4
        panes[3] = AgentPane(
            id=f"003-{repo_name}",
            pane_index=3,
            command=command,
            is_main=False,
        )
        panes.append(
            AgentPane(
                id=f"004-{repo_name}",
                pane_index=4,
                command=command,
                is_main=False,
            )
        )

    return panes


def start_agents_in_panes(panes: list[AgentPane], num_subagents: int) -> None:
    """Navigate to each pane and start the agent command."""
    # Start from main pane (leftmost)
    # Navigate to main pane first
    for _ in range(num_subagents + 1):
        ghostty_focus_direction("left")

    # Start main agent
    ghostty_run_command(panes[0].command)

    # Start subagent commands
    for i in range(1, len(panes)):
        ghostty_focus_direction("right")
        if i >= 2 and num_subagents <= 3:
            ghostty_focus_direction("down")
        ghostty_run_command(panes[i].command)


# =============================================================================
# Zed Integration
# =============================================================================


def launch_zed_with_terminal(workspace_path: Path) -> None:
    """Launch Zed editor with workspace and open terminal panel."""
    subprocess.Popen(
        ["zed", str(workspace_path)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)  # Wait for Zed to launch

    # Send Cmd+J to open terminal panel
    keystroke("Zed", "j", ["command"])


# =============================================================================
# Window Positioning
# =============================================================================


def position_windows_fill_screen() -> None:
    """Position Ghostty and Zed to fill screen (overlapping)."""
    script = '''
    tell application "Finder"
        set screenBounds to bounds of window of desktop
        set screenWidth to item 3 of screenBounds
        set screenHeight to item 4 of screenBounds
    end tell

    tell application "System Events"
        tell process "Ghostty"
            try
                set frontWindow to front window
                set position of frontWindow to {0, 25}
                set size of frontWindow to {screenWidth, screenHeight - 25}
            end try
        end tell
    end tell

    tell application "System Events"
        tell process "Zed"
            try
                set frontWindow to front window
                set position of frontWindow to {0, 25}
                set size of frontWindow to {screenWidth, screenHeight - 25}
            end try
        end tell
    end tell
    '''
    run_applescript(script)


# =============================================================================
# Session Management
# =============================================================================


def list_sessions() -> list[AgentSession]:
    """List all saved sessions."""
    sessions: list[AgentSession] = []
    if not SESSIONS_DIR.exists():
        return sessions

    for session_file in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        try:
            session = AgentSession.load(session_file.stem)
            sessions.append(session)
        except (json.JSONDecodeError, KeyError):
            continue

    return sessions


def get_most_recent_session() -> Optional[AgentSession]:
    """Get the most recently created session."""
    sessions = list_sessions()
    return sessions[0] if sessions else None


def find_pane_by_target(
    session: AgentSession, target: str
) -> Optional[tuple[AgentPane, int]]:
    """Find pane by ID, index, or 'main'."""
    target_lower = target.lower()

    # Check for 'main' keyword
    if target_lower == "main":
        for i, pane in enumerate(session.panes):
            if pane.is_main:
                return (pane, i)

    # Check for numeric index
    if target.isdigit():
        idx = int(target)
        if 0 <= idx < len(session.panes):
            return (session.panes[idx], idx)

    # Check for pane ID match
    for i, pane in enumerate(session.panes):
        if target_lower in pane.id.lower():
            return (pane, i)

    return None


# =============================================================================
# Subcommand Handlers
# =============================================================================


def cmd_spawn(args: argparse.Namespace) -> None:
    """Create new agent layout."""
    # Workspace selection
    if args.org and args.repo:
        workspaces = discover_workspaces()
        org, repo, workspace_path = fuzzy_match_workspace(args.org, args.repo, workspaces)
    else:
        # Interactive mode not implemented - require args
        print("Error: org and repo arguments required")
        print("Usage: auto agent spawn <org> <repo>")
        sys.exit(1)

    print(f"Workspace: {org}/{repo} ({workspace_path})")

    # Generate session ID
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    session_id = f"auto-agent-{timestamp}"

    # Create layout
    print(f"Creating layout with {args.subagents} subagent(s)...")
    panes = create_layout(args.subagents, workspace_path, args.command, repo)

    # Launch Zed if requested
    if not args.no_zed:
        print("Launching Zed editor...")
        launch_zed_with_terminal(workspace_path)

    # Position windows
    position_windows_fill_screen()

    # Focus back to Ghostty
    activate_app("Ghostty")

    # Create and save session
    session = AgentSession(
        session_id=session_id,
        workspace_path=str(workspace_path),
        repo_name=repo,
        org_name=org,
        created_at=datetime.now(timezone.utc).isoformat(),
        panes=panes,
    )
    session.save()

    print(f"Session created: {session_id}")
    print(f"Panes: {', '.join(p.id for p in panes)}")


def cmd_send(args: argparse.Namespace) -> None:
    """Send text to specific agent."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    # Find target pane
    result = find_pane_by_target(session, args.target)
    if not result:
        print(f"Error: Pane not found: {args.target}")
        print(f"Available panes: {', '.join(p.id for p in session.panes)}")
        sys.exit(1)

    pane, pane_idx = result
    text = " ".join(args.text)

    # Focus the pane and send text
    activate_app("Ghostty")

    # Navigate to main first, then to target
    for _ in range(len(session.panes)):
        ghostty_focus_direction("left")

    # Navigate to target pane
    # This is simplified - real navigation depends on layout
    for _ in range(pane_idx):
        ghostty_focus_direction("right")

    send_text("Ghostty", text)
    press_return("Ghostty")

    print(f"Sent to {pane.id}: {text}")


def cmd_broadcast(args: argparse.Namespace) -> None:
    """Send text to all agents."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    text = " ".join(args.text)
    target_panes = session.panes

    if args.exclude_main:
        target_panes = [p for p in target_panes if not p.is_main]

    activate_app("Ghostty")

    # Navigate to leftmost pane first
    for _ in range(len(session.panes)):
        ghostty_focus_direction("left")

    # Send to each pane
    for i, pane in enumerate(session.panes):
        if pane in target_panes:
            send_text("Ghostty", text)
            press_return("Ghostty")
            print(f"Sent to {pane.id}")

        if i < len(session.panes) - 1:
            ghostty_focus_direction("right")

    print(f"Broadcast complete: {text}")


def cmd_focus(args: argparse.Namespace) -> None:
    """Focus agent pane."""
    # Check if it's a direction
    if args.target.lower() in ("left", "right", "up", "down"):
        activate_app("Ghostty")
        ghostty_focus_direction(args.target.lower())
        print(f"Focused {args.target}")
        return

    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    # Find target pane
    result = find_pane_by_target(session, args.target)
    if not result:
        print(f"Error: Pane not found: {args.target}")
        sys.exit(1)

    pane, pane_idx = result

    activate_app("Ghostty")

    # Navigate to main first
    for _ in range(len(session.panes)):
        ghostty_focus_direction("left")

    # Navigate to target
    for _ in range(pane_idx):
        ghostty_focus_direction("right")

    print(f"Focused: {pane.id}")


def cmd_list(args: argparse.Namespace) -> None:
    """List active sessions."""
    sessions = list_sessions()

    if not sessions:
        print("No active sessions")
        return

    for session in sessions:
        if args.verbose:
            print(f"\nSession: {session.session_id}")
            print(f"  Workspace: {session.org_name}/{session.repo_name}")
            print(f"  Path: {session.workspace_path}")
            print(f"  Created: {session.created_at}")
            print(f"  Panes: {len(session.panes)}")
            for pane in session.panes:
                main_marker = " (main)" if pane.is_main else ""
                print(f"    - {pane.id}: {pane.command}{main_marker}")
        else:
            pane_count = len(session.panes)
            print(
                f"{session.session_id}: {session.org_name}/{session.repo_name} "
                f"({pane_count} panes)"
            )


def cmd_close(args: argparse.Namespace) -> None:
    """Close specific agent pane."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    # Find target pane
    result = find_pane_by_target(session, args.target)
    if not result:
        print(f"Error: Pane not found: {args.target}")
        sys.exit(1)

    pane, pane_idx = result

    activate_app("Ghostty")

    # Navigate to main first
    for _ in range(len(session.panes)):
        ghostty_focus_direction("left")

    # Navigate to target
    for _ in range(pane_idx):
        ghostty_focus_direction("right")

    # Close the pane
    ghostty_close_pane()

    # Update session
    session.panes = [p for p in session.panes if p.id != pane.id]
    if session.panes:
        session.save()
    else:
        session.delete()

    print(f"Closed: {pane.id}")


def cmd_kill(args: argparse.Namespace) -> None:
    """Terminate session and close window."""
    # Get session
    if args.session:
        session = AgentSession.load(args.session)
    else:
        session = get_most_recent_session()
        if not session:
            print("Error: No active session found")
            sys.exit(1)

    if not args.force:
        print(f"Kill session {session.session_id}? [y/N] ", end="", flush=True)
        response = input().strip().lower()
        if response != "y":
            print("Cancelled")
            return

    # Close all panes (close window)
    activate_app("Ghostty")
    keystroke("Ghostty", "w", ["command", "shift"])  # Close window

    # Delete session
    session.delete()

    print(f"Killed session: {session.session_id}")


# =============================================================================
# Argument Parser
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="auto agent",
        description="Manage Claude Code agent sessions in Ghostty terminal",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # spawn subcommand
    spawn_parser = subparsers.add_parser("spawn", help="Create new agent layout")
    spawn_parser.add_argument("org", nargs="?", help="Organization (fuzzy match)")
    spawn_parser.add_argument("repo", nargs="?", help="Repository (fuzzy match)")
    spawn_parser.add_argument(
        "--subagents",
        "-n",
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help="Number of subagent panes (default: 1)",
    )
    spawn_parser.add_argument(
        "--command",
        "-c",
        default="claude",
        help="Agent command to run (default: claude)",
    )
    spawn_parser.add_argument(
        "--no-zed",
        action="store_true",
        help="Skip launching Zed editor",
    )

    # send subcommand
    send_parser = subparsers.add_parser("send", help="Send text to specific agent")
    send_parser.add_argument("target", help="Agent ID, pane index, or 'main'")
    send_parser.add_argument("text", nargs="+", help="Text to send")
    send_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )

    # broadcast subcommand
    broadcast_parser = subparsers.add_parser(
        "broadcast", help="Send text to all agents"
    )
    broadcast_parser.add_argument("text", nargs="+", help="Text to broadcast")
    broadcast_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )
    broadcast_parser.add_argument(
        "--exclude-main",
        action="store_true",
        help="Exclude main agent from broadcast",
    )

    # focus subcommand
    focus_parser = subparsers.add_parser("focus", help="Focus agent pane")
    focus_parser.add_argument(
        "target", help="Agent ID, pane index, or direction (left/right/up/down)"
    )
    focus_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )

    # list subcommand
    list_parser = subparsers.add_parser("list", help="List active sessions")
    list_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed session info"
    )

    # close subcommand
    close_parser = subparsers.add_parser("close", help="Close specific agent pane")
    close_parser.add_argument("target", help="Agent ID or pane index")
    close_parser.add_argument(
        "--session", "-s", help="Session ID (default: most recent)"
    )

    # kill subcommand
    kill_parser = subparsers.add_parser(
        "kill", help="Terminate session and close window"
    )
    kill_parser.add_argument(
        "session", nargs="?", help="Session ID (default: most recent)"
    )
    kill_parser.add_argument(
        "--force", "-f", action="store_true", help="Force kill without confirmation"
    )

    return parser


# =============================================================================
# Main Entry Point
# =============================================================================


def main(args: Optional[list[str]] = None) -> None:
    """Main entry point for agent action."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    try:
        if parsed_args.subcommand == "spawn":
            cmd_spawn(parsed_args)
        elif parsed_args.subcommand == "send":
            cmd_send(parsed_args)
        elif parsed_args.subcommand == "broadcast":
            cmd_broadcast(parsed_args)
        elif parsed_args.subcommand == "focus":
            cmd_focus(parsed_args)
        elif parsed_args.subcommand == "list":
            cmd_list(parsed_args)
        elif parsed_args.subcommand == "close":
            cmd_close(parsed_args)
        elif parsed_args.subcommand == "kill":
            cmd_kill(parsed_args)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        if "Accessibility" in str(e) or "permission" in str(e).lower():
            print("Enable in System Settings > Privacy & Security > Accessibility")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(130)


if __name__ == "__main__":
    main()
