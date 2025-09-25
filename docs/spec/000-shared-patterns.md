# 000 - Shared Patterns Reference

This document contains templates and boilerplate code that specs can reference to avoid repetition. For architectural decisions, see [DESIGN.md](../../DESIGN.md).

## Action Script Template

Standard template for all action scripts in `lsimons_auto/actions/`:

```python
#!/usr/bin/env python3
"""
{action_name}.py - Brief description

This action can be run standalone or imported as a module.
"""

import argparse
import sys
from typing import Optional

def main(args: Optional[list[str]] = None) -> None:
    """Main function that performs the action work."""
    parser = argparse.ArgumentParser(description="Description of this action")
    # Add action-specific arguments
    parsed_args = parser.parse_args(args)
    
    try:
        # Implementation here
        pass
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Spec Template

Standard template for new specification documents:

```markdown
# XXX - Feature Name

**Purpose:** One-line description of what this does and why

**Requirements:**
- Key functional requirement 1
- Key functional requirement 2
- Important constraints or non-functional requirements

**Design Approach:**
- High-level design decision 1  
- High-level design decision 2
- Key technical choices and rationale

**Implementation Notes:**
- Critical implementation details only
- Dependencies or special considerations
- Integration points with existing code

**Status:** [Draft/Approved/Implemented]
```

## Test Function Template

Standard test structure for action tests:

```python
def test_action_cli():
    """Test command line interface works correctly."""
    # Test --help output
    # Test argument parsing
    # Test error handling

def test_action_functionality():
    """Test core action functionality end-to-end."""
    # Test actual behavior with realistic inputs
    # Use temporary directories for file operations
    # Verify expected outputs and side effects
```

## LaunchAgent Template

Template for macOS LaunchAgent plist files:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.leosimons.{service-name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/{username}/.local/bin/{command}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/{username}/.local/log/{service-name}.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/{username}/.local/log/{service-name}-error.log</string>
</dict>
</plist>
```

## Wrapper Script Template

Template for bash wrapper scripts that activate virtual environment:

```bash
#!/bin/bash
# Auto-generated wrapper script for lsimons-auto
# Uses project virtual environment to ensure dependencies are available
exec "{venv_python}" "{target_script}" "$@"
```
