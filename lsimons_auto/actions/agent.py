#!/usr/bin/env python3
"""
agent.py - Manage multiple Claude Code CLI instances in Ghostty terminal

Spawns Ghostty windows with configurable agent pane layouts, integrates with
Zed editor, and provides session management for multi-agent workflows.

This module is a thin wrapper that delegates to the agent_impl package.
All implementation is in lsimons_auto/actions/agent_impl/.
"""

# Handle both package import and direct script execution
try:
    # Package import (when imported as lsimons_auto.actions.agent)
    from .agent_impl import (
        APPLESCRIPT_DELAY,
        GIT_ROOT,
        SESSIONS_DIR,
        AgentPane,
        AgentSession,
        create_parser,
        discover_workspaces,
        find_pane_by_target,
        fuzzy_match_workspace,
        get_most_recent_session,
        list_sessions,
        main,
        run_applescript,
    )
    from .agent_impl.cli import (
        cmd_broadcast,
        cmd_close,
        cmd_focus,
        cmd_kill,
        cmd_list,
        cmd_send,
        cmd_spawn,
    )
    from .agent_impl.ghostty import (
        activate_app,
        ghostty_close_pane,
        ghostty_close_window_by_id,
        ghostty_focus_direction,
        ghostty_get_front_window_id,
        ghostty_new_window,
        ghostty_run_command,
        ghostty_split_down,
        ghostty_split_right,
        key_code,
        keystroke,
        press_return,
        send_text,
    )
    from .agent_impl.layout import create_layout, start_agents_in_panes
    from .agent_impl.worktree import (
        ensure_worktree,
        ensure_worktrees_dir,
        get_worktree_branch,
        list_worktrees,
        remove_worktree,
    )
    from .agent_impl.zed import launch_zed_with_terminal, position_windows_fill_screen
except ImportError:
    # Direct script execution (when run as `python agent.py`)
    from agent_impl import (  # pyright: ignore[reportMissingImports]
        APPLESCRIPT_DELAY,
        GIT_ROOT,
        SESSIONS_DIR,
        AgentPane,
        AgentSession,
        create_parser,
        discover_workspaces,
        find_pane_by_target,
        fuzzy_match_workspace,
        get_most_recent_session,
        list_sessions,
        main,
        run_applescript,
    )
    from agent_impl.cli import (  # pyright: ignore[reportMissingImports]
        cmd_broadcast,
        cmd_close,
        cmd_focus,
        cmd_kill,
        cmd_list,
        cmd_send,
        cmd_spawn,
    )
    from agent_impl.ghostty import (  # pyright: ignore[reportMissingImports]
        activate_app,
        ghostty_close_pane,
        ghostty_close_window_by_id,
        ghostty_focus_direction,
        ghostty_get_front_window_id,
        ghostty_new_window,
        ghostty_run_command,
        ghostty_split_down,
        ghostty_split_right,
        key_code,
        keystroke,
        press_return,
        send_text,
    )
    from agent_impl.layout import (  # pyright: ignore[reportMissingImports]
        create_layout,
        start_agents_in_panes,
    )
    from agent_impl.worktree import (  # pyright: ignore[reportMissingImports]
        ensure_worktree,
        ensure_worktrees_dir,
        get_worktree_branch,
        list_worktrees,
        remove_worktree,
    )
    from agent_impl.zed import (  # pyright: ignore[reportMissingImports]
        launch_zed_with_terminal,
        position_windows_fill_screen,
    )

__all__ = [
    # Main entry point
    "main",
    "create_parser",
    # Data classes
    "AgentPane",
    "AgentSession",
    # Constants
    "APPLESCRIPT_DELAY",
    "SESSIONS_DIR",
    "GIT_ROOT",
    # Session management
    "list_sessions",
    "get_most_recent_session",
    "find_pane_by_target",
    # Workspace discovery
    "discover_workspaces",
    "fuzzy_match_workspace",
    # Worktree management
    "ensure_worktrees_dir",
    "ensure_worktree",
    "get_worktree_branch",
    "remove_worktree",
    "list_worktrees",
    # AppleScript helpers
    "run_applescript",
    "activate_app",
    "keystroke",
    "key_code",
    "send_text",
    "press_return",
    # Ghostty control
    "ghostty_new_window",
    "ghostty_split_right",
    "ghostty_split_down",
    "ghostty_focus_direction",
    "ghostty_close_pane",
    "ghostty_run_command",
    "ghostty_get_front_window_id",
    "ghostty_close_window_by_id",
    # Layout
    "create_layout",
    "start_agents_in_panes",
    # Zed integration
    "launch_zed_with_terminal",
    "position_windows_fill_screen",
    # Subcommand handlers
    "cmd_spawn",
    "cmd_send",
    "cmd_broadcast",
    "cmd_focus",
    "cmd_list",
    "cmd_close",
    "cmd_kill",
]

if __name__ == "__main__":
    main()
