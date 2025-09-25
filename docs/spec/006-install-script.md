# 006 - Installation Script

**Purpose:** Install and configure lsimons-auto scripts with proper PATH integration and macOS LaunchAgent scheduling

**Requirements:**
- Install wrapper scripts in `~/.local/bin/` for `auto` and `start-the-day` commands
- Create LaunchAgent for automated daily execution at 7:00 AM
- Set up required directory structure (`~/.local/log/`, etc.)
- Generate wrapper scripts that activate virtual environment before execution
- Make commands globally accessible by ensuring `~/.local/bin` is in PATH

**Design Approach:**
- Follow installation architecture from DESIGN.md (templates in 000-shared-patterns.md)
- Generate wrapper scripts rather than direct symlinks for venv compatibility
- Template-based LaunchAgent creation with username substitution
- Graceful handling of missing dependencies or permission issues
- Idempotent installation (safe to run multiple times)

**Implementation Notes:**
- Dependencies: Standard library only (os, pathlib, subprocess)
- Wrapper scripts activate `.venv` before executing project scripts
- LaunchAgent template stored as string with `{username}` placeholder
- Directory permissions: 755 for `.local/bin`, 644 for scripts
- Error handling: Continue installation even if LaunchAgent fails
- Validation: Check for virtual environment and project structure before proceeding

**Status:** Implemented