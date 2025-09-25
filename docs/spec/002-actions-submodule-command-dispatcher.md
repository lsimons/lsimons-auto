# 002 - Actions Submodule and Command Dispatcher

## Overview
This specification defines a new actions submodule containing individual Python scripts that can be executed both standalone and as subcommands through a centralized `lsimons_auto` command dispatcher.

## Status
- [x] Draft
- [x] Under Review  
- [x] Approved
- [x] In Progress
- [x] Implemented
- [ ] Deprecated

## Motivation
As the lsimons-auto project grows, we need:
- A modular architecture for discrete automation tasks
- Individual scripts that can be run standalone or as part of larger workflows
- A unified command-line interface for discoverability and ease of use
- Consistent structure across all action scripts
- Easy extensibility for adding new automation tasks

## Requirements

### Functional Requirements
1. **Actions Submodule**: Create `lsimons_auto/actions/` directory containing individual Python scripts
2. **Standalone Execution**: Each action script must be executable independently with `python -m lsimons_auto.actions.{action_name}`
3. **Import Support**: Each action script must be importable as a module
4. **Main Function**: Each action script must have a `main()` function that performs the core work
5. **Command Dispatcher**: Create `lsimons_auto.py` script that acts as a unified CLI interface
6. **Subcommand Routing**: The dispatcher should route subcommands to corresponding action scripts
7. **Installation**: The dispatcher should be installable as `~/.local/bin/lsimons_auto`

### Non-Functional Requirements
1. **Consistency**: All action scripts follow the same structural pattern
2. **Discoverability**: Help system shows available actions and their descriptions
3. **Error Handling**: Graceful handling of missing actions and execution errors
4. **Performance**: Minimal startup overhead for the dispatcher
5. **Maintainability**: Clear separation between dispatcher logic and action implementations

## Design

### Directory Structure
```
lsimons_auto/
├── __init__.py
├── start_the_day.py              # Existing script
├── actions/                      # New actions submodule
│   ├── __init__.py
│   ├── echo.py                   # Basic echo action for testing
│   └── {future_actions}.py       # Additional actions added over time
└── lsimons_auto.py               # New command dispatcher
```

### Action Script Pattern
Each action script follows this template:
```python
#!/usr/bin/env python3
"""
{action_name}.py - Brief description of what this action does

This action can be run standalone or imported as a module.
"""

import argparse
import sys
from typing import Optional


def main(args: Optional[list[str]] = None) -> None:
    """Main function that performs the action work."""
    parser = argparse.ArgumentParser(description="Description of this action")

    # Add action-specific arguments
    parser.add_argument("--example", help="Example argument")

    parsed_args = parser.parse_args(args)

    # Perform the actual work
    print(f"Running {__file__} action...")
    # ... action implementation ...


if __name__ == "__main__":
    main()
```

### Command Dispatcher Design
The `lsimons_auto.py` script follows the pattern of `start_the_day.py` but acts as a command router:

1. **Argument Parsing**: Uses argparse with subparsers for each action
2. **Dynamic Discovery**: Automatically discovers available actions from the actions directory
3. **Module Loading**: Imports and executes action modules dynamically
4. **Help System**: Provides help for main command and individual subcommands
5. **Error Handling**: Graceful handling of missing actions and execution errors

### Installation Integration
- Update `pyproject.toml` to include new script entry point
- Create installation mechanism similar to existing `install.py` pattern
- Install as `~/.local/bin/lsimons_auto` for global access

## Implementation

### Phase 1: Core Infrastructure
1. Create `lsimons_auto/actions/` directory with `__init__.py`
2. Create basic `echo.py` action script following the standard pattern
3. Create `lsimons_auto.py` dispatcher with basic subcommand routing
4. Update `pyproject.toml` for new script entry point

### Phase 2: Dynamic Discovery
1. Implement action discovery mechanism in dispatcher
2. Add help system showing available actions
3. Add error handling for missing or invalid actions

### Phase 3: Installation & Integration
1. Update installation process to include new dispatcher
2. Add tests for action scripts and dispatcher
3. Update documentation

### Key Implementation Details

#### Action Discovery
```python
def discover_actions() -> dict[str, Path]:
    """Discover available action scripts in the actions directory."""
    project_root = Path.home() / "dev" / "lsimons-auto"
    actions_dir = project_root / "lsimons_auto" / "actions"
    actions = {}
    
    for file_path in actions_dir.glob("*.py"):
        if file_path.name != "__init__.py":
            action_name = file_path.stem
            actions[action_name] = file_path
    
    return actions
```

#### Subcommand Routing
```python
def main() -> None:
    """Main dispatcher function."""
    parser = argparse.ArgumentParser(description="lsimons-auto command dispatcher")
    subparsers = parser.add_subparsers(dest="action", help="Available actions")
    
    actions = discover_actions()
    
    for action_name in actions:
        subparsers.add_parser(action_name, help=f"Run {action_name} action")
    
    args, remaining = parser.parse_known_args()
    
    if not args.action:
        parser.print_help()
        return
    
    # Execute the action script using subprocess
    action_script = actions[args.action]
    cmd = [sys.executable, str(action_script)] + remaining
    
    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {args.action}: {e}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"Error: Action script not found: {action_script}")
        sys.exit(1)
```

### Echo Action Example
The basic echo action provides a simple, side-effect-free script for testing:

```python
#!/usr/bin/env python3
"""
echo.py - Simple echo action for testing the dispatcher system

This action echoes back the provided arguments, making it ideal for
testing the command dispatcher without side effects.
"""

import argparse
import sys
from typing import Optional


def main(args: Optional[list[str]] = None) -> None:
    """Echo the provided message with optional formatting."""
    parser = argparse.ArgumentParser(description="Echo a message")
    
    parser.add_argument("message", nargs="*", help="Message to echo")
    parser.add_argument("--upper", action="store_true", help="Convert to uppercase")
    parser.add_argument("--prefix", default="", help="Prefix to add")
    
    parsed_args = parser.parse_args(args)
    
    message = " ".join(parsed_args.message) if parsed_args.message else "Hello, World!"
    
    if parsed_args.upper:
        message = message.upper()
    
    if parsed_args.prefix:
        message = f"{parsed_args.prefix}: {message}"
    
    print(message)


if __name__ == "__main__":
    main()
```

## Testing

### Integration Test Strategy
Focus on end-to-end testing without mocks to ensure the complete system works:

**Dispatcher Integration Tests:**
- Test `lsimons_auto --help` shows available actions including echo
- Test `lsimons_auto echo --help` shows action-specific help
- Test `lsimons_auto echo "hello world"` produces expected output
- Test `lsimons_auto echo --upper "hello"` produces "HELLO"
- Test `lsimons_auto echo --prefix "Test" "message"` produces "Test: message"
- Test error handling for invalid actions: `lsimons_auto nonexistent`
- Test argument passing: `lsimons_auto echo --unknown-flag` shows echo's error

**Standalone Action Tests:**
- Test direct execution: `python ~/dev/lsimons-auto/lsimons_auto/actions/echo.py "hello"`
- Test action help: `python ~/dev/lsimons-auto/lsimons_auto/actions/echo.py --help`
- Test action argument parsing and edge cases

**Installation Tests:**
- Test `lsimons_auto` symlink creation in `~/.local/bin/`
- Test symlink points to correct script location
- Test executable permissions are correct
- Verify `lsimons_auto` works from any directory after installation

**Action Discovery Tests:**
- Test discovery finds echo action in actions directory
- Test discovery ignores `__init__.py` and non-Python files
- Test behavior when actions directory is empty or missing

### Test Implementation Notes
- Use temporary directories for installation tests to avoid system conflicts
- Capture subprocess output for verification in dispatcher tests  
- Test both success and error exit codes
- Verify proper argument forwarding from dispatcher to actions

## Migration Strategy

### Backward Compatibility
- Existing `start-the-day` command continues to work unchanged
- No changes to existing `start_the_day.py` functionality
- Installation process maintains existing LaunchAgent setup

### Future Actions
- New automation tasks added as action scripts in `actions/` directory
- Existing functionality can be gradually refactored into actions if beneficial
- Clear upgrade path for users to adopt unified CLI

## References
- Similar pattern to `git` command with subcommands (`git commit`, `git push`, etc.)
- Follows Django management command pattern (`python manage.py {command}`)
- Inspired by modern CLI tools like `aws cli`, `gcloud`, etc.
- Builds on existing `start_the_day.py` installation and execution patterns
