"""
layout.py - Ghostty pane layout creation and agent startup.

Creates multi-pane Ghostty layouts with git worktrees for isolated agent sessions.
"""

import time
from pathlib import Path

from .ghostty import (
    activate_app,
    ghostty_focus_direction,
    ghostty_new_window,
    ghostty_run_command,
    ghostty_split_down,
    ghostty_split_right,
)
from .session import AgentPane
from .worktree import ensure_worktree, ensure_worktrees_dir


def create_layout(
    num_subagents: int,
    workspace_path: Path,
    command: str,
    repo_name: str,
) -> list[AgentPane]:
    """
    Create Ghostty layout with main + subagent panes.

    Each pane gets its own git worktree for isolated work:
    - Main pane: {repo}-worktrees/M
    - Subagents: {repo}-worktrees/001, 002, etc.

    Args:
        num_subagents: Number of subagent panes (1-4)
        workspace_path: Path to the original git repository
        command: Agent command to run (e.g., "claude")
        repo_name: Name of the repository

    Returns:
        List of AgentPane objects with worktree paths
    """
    panes: list[AgentPane] = []

    # Create worktrees directory
    worktrees_dir = ensure_worktrees_dir(workspace_path)

    # Launch Ghostty with new window
    activate_app("Ghostty")
    ghostty_new_window()

    # Create worktree for main pane
    main_worktree = ensure_worktree(workspace_path, "M", worktrees_dir)

    # Change to worktree directory and clear screen
    ghostty_run_command(f"cd {main_worktree}")
    ghostty_run_command("clear")

    # Main pane
    main_pane = AgentPane(
        id=f"M-{repo_name}",
        pane_index=0,
        command=command,
        is_main=True,
        worktree_path=str(main_worktree),
    )
    panes.append(main_pane)

    if num_subagents >= 1:
        # Create worktree for first subagent
        worktree_001 = ensure_worktree(workspace_path, "001", worktrees_dir)

        # Split right for first subagent
        ghostty_split_right()
        ghostty_run_command(f"cd {worktree_001}")
        ghostty_run_command("clear")
        panes.append(
            AgentPane(
                id=f"001-{repo_name}",
                pane_index=1,
                command=command,
                is_main=False,
                worktree_path=str(worktree_001),
            )
        )

    if num_subagents >= 2:
        # Create worktree for second subagent
        worktree_002 = ensure_worktree(workspace_path, "002", worktrees_dir)

        # Split down for second subagent
        ghostty_split_down()
        ghostty_run_command(f"cd {worktree_002}")
        ghostty_run_command("clear")
        panes.append(
            AgentPane(
                id=f"002-{repo_name}",
                pane_index=2,
                command=command,
                is_main=False,
                worktree_path=str(worktree_002),
            )
        )

    if num_subagents >= 3:
        # Create worktree for third subagent
        worktree_003 = ensure_worktree(workspace_path, "003", worktrees_dir)

        # Split down again for third subagent
        ghostty_split_down()
        ghostty_run_command(f"cd {worktree_003}")
        ghostty_run_command("clear")
        panes.append(
            AgentPane(
                id=f"003-{repo_name}",
                pane_index=3,
                command=command,
                is_main=False,
                worktree_path=str(worktree_003),
            )
        )

    if num_subagents >= 4:
        # Get existing worktree path for pane 3 and create worktree for fourth subagent
        # worktree_003 was created in the num_subagents >= 3 block above
        worktree_003_path = worktrees_dir / "003"
        worktree_004 = ensure_worktree(workspace_path, "004", worktrees_dir)

        # For 4 subagents: focus up to s1, split right, split down
        # Current layout: main | s1/s2/s3
        # Target: main | s1/s2 | s3/s4
        ghostty_focus_direction("up")
        ghostty_focus_direction("up")  # Now at s1
        ghostty_split_right()
        ghostty_run_command(f"cd {worktree_003_path}")
        ghostty_run_command("clear")
        # Re-assign pane 3 with correct worktree
        panes[3] = AgentPane(
            id=f"003-{repo_name}",
            pane_index=3,
            command=command,
            is_main=False,
            worktree_path=str(worktree_003_path),
        )
        ghostty_split_down()
        ghostty_run_command(f"cd {worktree_004}")
        ghostty_run_command("clear")
        panes.append(
            AgentPane(
                id=f"004-{repo_name}",
                pane_index=4,
                command=command,
                is_main=False,
                worktree_path=str(worktree_004),
            )
        )

    return panes


def start_agents_in_panes(panes: list[AgentPane], num_subagents: int) -> None:
    """
    Navigate to each pane and start the agent command.

    Args:
        panes: List of AgentPane objects
        num_subagents: Number of subagent panes
    """
    # Give Ghostty time to be ready after app switch
    time.sleep(0.5)

    # Navigate to main pane first (keep going left)
    # Use Cmd+Opt+Left which is Ghostty's goto_split:left
    for _ in range(3):  # Enough to reach leftmost from any position
        ghostty_focus_direction("left")
        time.sleep(0.2)

    # Start main agent
    time.sleep(0.3)
    ghostty_run_command(panes[0].command)

    if num_subagents == 1:
        # Layout: main | s1
        ghostty_focus_direction("right")
        ghostty_run_command(panes[1].command)

    elif num_subagents == 2:
        # Layout: main | s1/s2
        ghostty_focus_direction("right")
        ghostty_run_command(panes[1].command)
        ghostty_focus_direction("down")
        ghostty_run_command(panes[2].command)

    elif num_subagents == 3:
        # Layout: main | s1/s2/s3
        ghostty_focus_direction("right")
        ghostty_run_command(panes[1].command)
        ghostty_focus_direction("down")
        ghostty_run_command(panes[2].command)
        ghostty_focus_direction("down")
        ghostty_run_command(panes[3].command)

    elif num_subagents == 4:
        # Layout: main | s1/s2 | s3/s4
        ghostty_focus_direction("right")
        ghostty_run_command(panes[1].command)
        ghostty_focus_direction("down")
        ghostty_run_command(panes[2].command)
        ghostty_focus_direction("up")
        ghostty_focus_direction("right")
        ghostty_run_command(panes[3].command)
        ghostty_focus_direction("down")
        ghostty_run_command(panes[4].command)
