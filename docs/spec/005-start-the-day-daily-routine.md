# 005 - Start-the-Day Daily Routine

## Overview
This specification documents the existing start-the-day daily automation routine that provides automated morning startup sequences with configurable scheduling and once-per-day execution tracking.

## Status
- [x] Draft
- [x] Under Review  
- [x] Approved
- [x] In Progress
- [x] Implemented
- [ ] Deprecated

## Motivation
Daily routines are essential for productivity and consistency. The start-the-day automation provides:
- Consistent morning setup without manual intervention
- Automated desktop organization and customization
- Smart execution tracking to prevent duplicate runs
- Reliable scheduling through macOS LaunchAgent integration
- Graceful error handling and status reporting

## Requirements

### Functional Requirements
1. **Daily Routine Execution**: Run a sequence of automation tasks each morning
2. **Once-Per-Day Logic**: Track execution state to prevent multiple runs on the same day
3. **Force Mode**: Allow override of daily limit when needed with `--force` flag
4. **Automated Scheduling**: macOS LaunchAgent runs routine at 7:00 AM daily
5. **Configuration Storage**: Persist execution state in TOML configuration file
6. **Status Reporting**: Provide colorized output and clear success/failure messages
7. **Error Handling**: Graceful handling of subprocess failures and system errors
8. **Standalone Operation**: Independent from the auto CLI system

### Non-Functional Requirements
1. **Reliability**: Must work consistently across system reboots and updates
2. **Performance**: Fast startup and execution without unnecessary delays
3. **User Experience**: Clear, colorized output with meaningful status messages
4. **Maintainability**: Modular design allowing easy addition of new daily tasks
5. **Safety**: Graceful error handling without system disruption

## Design

### Architecture Overview
The start-the-day system operates as a standalone daily automation script with three main components:

1. **Execution State Management**: TOML-based configuration for tracking daily runs
2. **Daily Task Orchestration**: Coordinated execution of desktop automation tasks
3. **LaunchAgent Integration**: Automated scheduling for consistent daily execution

### Core Components

#### State Management
- **Configuration File**: `~/.start_the_day.toml` stores execution metadata
- **Date Tracking**: ISO format date strings for last run comparison
- **Simple TOML Parser**: Custom lightweight parser for basic configuration needs
- **Atomic Updates**: Safe configuration file updates with error handling

#### Daily Task Sequence
Current daily tasks executed in order:
1. **Desktop Organization**: `auto organize_desktop` - Organize files by creation date
2. **Background Update**: `auto update_desktop_background` - Generate fresh wallpaper with UTC time

#### Scheduling Integration
- **LaunchAgent**: `~/Library/LaunchAgents/com.leosimons.start-the-day.plist`
- **Daily Schedule**: 7:00 AM execution time
- **Log Management**: Separate stdout and stderr log files
- **Installation Integration**: Automatic LaunchAgent setup via `install.py`

### Command Line Interface
```bash
start-the-day [--force]
```

**Arguments:**
- `--force`: Override once-per-day logic and force execution

**Exit Codes:**
- `0`: Success (routine completed or already ran today)
- `1`: Error during execution or configuration issues

### Configuration Format
The TOML configuration file uses a minimal format:
```toml
# start_the_day.py execution state
# Generated on 2024-01-15T08:30:00.123456

last_run_date = "2024-01-15"
```

### Output Format
The script provides colorized terminal output:
- **Yellow**: Greeting messages ("Good morning!")
- **Blue**: Progress messages ("Starting your day...")
- **Green**: Success indicators ("✓ Desktop organized")
- **Default**: Warning messages for non-critical failures

## Implementation Details

### State Management Functions

#### Configuration Path Resolution
```python
def get_config_path(test_mode: bool = False) -> str:
    """Get the path to the configuration file."""
    if test_mode:
        return os.path.expanduser("~/.start_the_day_test.toml")
    return os.path.expanduser("~/.start_the_day.toml")
```

#### TOML Parsing
Custom lightweight TOML parser for basic key-value pairs:
```python
def parse_toml_simple(content: str) -> dict[str, str]:
    """Simple TOML parser for our basic needs (last_run_date only)."""
    config: dict[str, str] = {}
    for line in content.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().strip("\"'")
                value = value.strip().strip("\"'")
                config[key] = value
    return config
```

#### State Persistence
```python
def save_execution_state(config: dict[str, str], test_mode: bool = False) -> None:
    """Save execution state to config file."""
    config_path = get_config_path(test_mode)
    
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        write_toml_simple(config, config_path)
    except (IOError, OSError) as e:
        print(f"Error: Could not write config file {config_path}: {e}")
        sys.exit(1)
```

### Daily Execution Logic

#### Run Detection
```python
def already_ran_today(test_mode: bool = False) -> bool:
    """Check if the script already ran today."""
    config = load_execution_state(test_mode)
    last_run = config.get("last_run_date")
    today = get_today_date()
    
    return last_run == today
```

#### Task Execution
```python
def run_command(command: list[str], action_name: str, success_message: str) -> None:
    """Run a command with error handling and status messages."""
    print(f"{action_name}...")
    try:
        _ = subprocess.run(command, check=True, capture_output=True)
        print(colorize_text(f"✓ {success_message}", "green"))
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to {action_name.lower()}: {e}")
```

#### Main Routine Orchestration
```python
def start_the_day() -> None:
    """Main function that runs the daily startup routine."""
    print(colorize_text("Good morning!", "yellow"))
    print(colorize_text("Starting your day...", "blue"))
    
    # Run daily tasks
    run_command(["auto", "organize_desktop"], "Organizing desktop", "Desktop organized")
    
    run_command(
        ["auto", "update_desktop_background"],
        "Updating desktop background", 
        "Desktop background updated",
    )
    
    print(colorize_text("✓ Daily startup routine completed", "green"))
```

### Installation Integration

The start-the-day script integrates with the existing installation system:

1. **Script Installation**: `install.py` creates `~/.local/bin/start-the-day` symlink
2. **LaunchAgent Setup**: Automatic creation of macOS LaunchAgent plist file
3. **Log Directory**: Creation of `~/.local/log/` for execution logs
4. **PATH Integration**: Ensures `~/.local/bin` is available for execution

### LaunchAgent Configuration
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.leosimons.start-the-day</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/username/.local/bin/start-the-day</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/username/.local/log/start-the-day.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/username/.local/log/start-the-day-error.log</string>
</dict>
</plist>
```

## Testing Strategy

### Unit Tests
- **State Management**: Test TOML parsing, configuration file handling
- **Date Logic**: Test today's date comparison and execution state tracking  
- **Command Execution**: Test subprocess execution with mocked commands
- **Configuration Paths**: Test path resolution for normal and test modes
- **Error Handling**: Test graceful handling of file system errors

### Integration Tests
- **End-to-End Execution**: Test complete daily routine with real commands
- **Force Mode**: Test `--force` flag overrides daily limit
- **State Persistence**: Test configuration file creation and updates
- **Already-Run Detection**: Test skip logic when already executed today
- **LaunchAgent Integration**: Test scheduled execution (manual verification)

### Test Implementation Considerations
- **Test Mode**: Use separate configuration file (`~/.start_the_day_test.toml`) 
- **Command Mocking**: Mock `auto` subcommands to avoid side effects during testing
- **Temporary Directories**: Use temporary paths for file system tests
- **Date Manipulation**: Test different date scenarios and edge cases
- **Error Simulation**: Test behavior with file permission issues and disk space

## Usage Examples

### Manual Execution
```bash
# Standard daily run (skips if already ran today)
start-the-day

# Force run even if already executed today  
start-the-day --force

# Check execution logs
tail -f ~/.local/log/start-the-day.log
tail -f ~/.local/log/start-the-day-error.log
```

### LaunchAgent Management
```bash
# Check if LaunchAgent is loaded
launchctl list | grep com.leosimons.start-the-day

# Manually trigger LaunchAgent
launchctl start com.leosimons.start-the-day

# Disable automatic execution
launchctl unload ~/Library/LaunchAgents/com.leosimons.start-the-day.plist

# Re-enable automatic execution
launchctl load ~/Library/LaunchAgents/com.leosimons.start-the-day.plist
```

### Configuration Management
```bash
# View current configuration
cat ~/.start_the_day.toml

# Reset daily execution (allows re-run)
rm ~/.start_the_day.toml
```

## Extensibility

### Adding New Daily Tasks
To add new tasks to the daily routine, modify the `start_the_day()` function:

```python
def start_the_day() -> None:
    """Main function that runs the daily startup routine."""
    print(colorize_text("Good morning!", "yellow"))
    print(colorize_text("Starting your day...", "blue"))
    
    # Existing tasks
    run_command(["auto", "organize_desktop"], "Organizing desktop", "Desktop organized")
    run_command(["auto", "update_desktop_background"], "Updating desktop background", "Desktop background updated")
    
    # New task example
    run_command(["auto", "sync_calendar"], "Syncing calendar", "Calendar synced")
    
    print(colorize_text("✓ Daily startup routine completed", "green"))
```

### Configuration Extensions
The TOML configuration can be extended for additional state tracking:

```toml
# Extended configuration example
last_run_date = "2024-01-15"
last_successful_run = "2024-01-15"
consecutive_successful_days = "7"
last_desktop_organization = "2024-01-15"
last_background_update = "2024-01-15"
```

### Custom Scheduling
Alternative scheduling can be implemented by modifying the LaunchAgent plist or creating additional LaunchAgents for different times/frequencies.

## Migration and Compatibility

### Backward Compatibility
- Existing configuration files continue to work without modification
- LaunchAgent configuration remains stable across updates
- Command line interface maintains consistent behavior
- Log file locations and formats remain unchanged

### Future Evolution
- Additional command line options can be added without breaking existing usage
- Configuration format can be extended while maintaining backward compatibility
- New daily tasks can be added without affecting existing functionality
- Alternative scheduling options can be implemented alongside existing LaunchAgent

## Dependencies

### System Requirements
- **macOS**: Required for LaunchAgent integration and desktop management
- **Python 3.13+**: Modern Python version with type hints support
- **File System Access**: Read/write permissions for home directory and subdirectories

### External Dependencies
- **auto CLI**: Depends on `auto organize_desktop` and `auto update_desktop_background` commands
- **subprocess**: Standard library subprocess module for command execution
- **os/sys**: Standard library modules for file system and system interaction

### Runtime Dependencies  
- `~/.local/bin/auto` must be executable and available in PATH
- Desktop organization and background update actions must be functional
- Sufficient disk space for log files and configuration storage

## Security Considerations

### File System Security
- Configuration files stored in user home directory with standard permissions
- Log files contain no sensitive information (command names and timestamps only)
- No network access or external API dependencies

### Execution Security
- Runs with user privileges (not root or elevated permissions)  
- Limited to executing predefined `auto` subcommands
- No arbitrary command execution or user input processing
- LaunchAgent runs in user context, not system-wide

### Data Privacy
- No collection or transmission of personal data
- Local configuration and logs only
- No external service dependencies or telemetry

## References
- macOS LaunchAgent documentation: `man launchctl`, `man plist`
- TOML specification: https://toml.io/en/
- Python subprocess documentation: https://docs.python.org/3/library/subprocess.html
- Similar daily automation tools: `cron`, `anacron`, macOS Shortcuts app
- Desktop automation patterns in macOS automation suites