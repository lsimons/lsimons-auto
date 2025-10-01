# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For general agent instructions that apply to all AI assistants, see [AGENTS.md](AGENTS.md).

## Project Overview

**lsimons-auto** is a personal automation toolkit for macOS providing daily routines and desktop management through modular Python scripts. The project emphasizes simplicity, minimal dependencies, and spec-driven development.

## Key Architecture

### Dual-Command System
- **`start-the-day`**: Standalone daily routine script with macOS LaunchAgent automation (7 AM daily)
- **`auto` CLI**: Command dispatcher that dynamically discovers and routes to action scripts

### Action Script Pattern
Actions live in `lsimons_auto/actions/` and follow a standard interface:
- Each action has `main(args: Optional[list[str]] = None)` function
- Can run standalone or be imported as a module
- Auto-discovered by the dispatcher (no manual registration needed)
- See `docs/spec/000-shared-patterns.md` for the template

### Core Design Principles
- **Dependency-free core**: Standard library only (os, sys, datetime, argparse)
- **Selective dependencies**: Pillow only for image processing actions
- **Functional over OOP**: Simple functions for clarity
- **Graceful degradation**: Continue on failures, clear error messages

## Common Commands

```bash
# Run full test suite
uv run pytest

# Run specific test file
uv run pytest tests/test_start_the_day.py

# Run with verbose output
uv run pytest -v

# Install/reinstall the toolkit
python3 install.py

# Check LaunchAgent status
launchctl list | grep com.leosimons.start-the-day
```

## Development Workflow

1. **Spec-First Development**: Document features in `docs/spec/XXX-feature-name.md` before coding
   - Use sequential numbering (001, 002, 003...)
   - Focus on design decisions and rationale, not implementation details
   - Keep specs under 100 lines when possible
   - Reference spec number in commit messages

2. **Testing**: Always run `uv run pytest` after changes
   - Integration-first testing (real I/O over mocking)
   - Use temp directories and separate config files for tests

3. **Documentation Updates**:
   - Update `DESIGN.md` when making architectural decisions
   - Update `AGENTS.md` for new development patterns

## Project Structure

```
lsimons_auto/
  lsimons_auto.py       # Auto CLI dispatcher (dynamic action discovery)
  start_the_day.py      # Daily routine with state tracking
  actions/              # Modular action scripts (auto-discovered)
    organize_desktop.py
    update_desktop_background.py
    launch_apps.py
    echo.py
tests/                  # Integration and unit tests
docs/spec/              # Feature specifications
  000-shared-patterns.md  # Reusable templates
  001-spec-based-development.md
  002-actions-submodule-command-dispatcher.md
etc/                    # LaunchAgent plist templates
```

## Adding New Actions

1. Create spec in `docs/spec/XXX-action-name.md`
2. Implement in `lsimons_auto/actions/action_name.py` following the standard template
3. No dispatcher changes needed (automatic discovery)
4. Add tests in `tests/test_action_name.py`
5. Update README.md with action description

## State and Configuration

- **Daily routine state**: `~/.start_the_day.toml` (TOML with custom parser)
- **Background images**: `~/.local/share/lsimons-auto/backgrounds/`
- **Logs**: `~/.local/log/start-the-day.log` and `*-error.log`
- **Installed scripts**: `~/.local/bin/start-the-day` and `~/.local/bin/auto`

## Type Safety

- Comprehensive type annotations (Pyright strict mode)
- Use specific ignore comments when needed:
  - `# pyright: ignore[reportAny]` for argparse/unittest dynamic patterns
  - `# pyright: ignore[reportImplicitOverride]` for unittest overrides

## Important Files

- **AGENTS.md**: General agent instructions for all AI assistants
- **DESIGN.md**: Architectural decisions and design philosophy
- **README.md**: User-facing documentation
- **docs/spec/000-shared-patterns.md**: Templates and boilerplate
