# 002 - Actions Submodule and Command Dispatcher

**Purpose:** Create modular automation tasks as individual Python scripts with unified CLI access through a command dispatcher

**Requirements:**
- Actions submodule at `lsimons_auto/actions/` with individual Python scripts
- Each action executable standalone with `python -m lsimons_auto.actions.{action_name}`
- Each action importable as module with `main()` function
- Command dispatcher `lsimons_auto.py` routing subcommands to actions
- Installation as `~/.local/bin/lsimons_auto` for global access
- Dynamic action discovery and help system

**Design Approach:**
- Follow action script architecture from DESIGN.md (template in 000-shared-patterns.md)
- Dispatcher uses argparse subparsers for each discovered action
- Execute actions via subprocess to maintain isolation
- Basic `echo.py` action for testing without side effects
- Integration with existing `pyproject.toml` entry points

**Implementation Notes:**
- Action discovery scans `actions/*.py` files (excluding `__init__.py`)
- Dispatcher forwards remaining args to action scripts
- Error handling for missing actions and execution failures
- Echo action supports `--upper`, `--prefix` flags for testing argument passing
- Update installation process to include dispatcher symlink

**Status:** Implemented