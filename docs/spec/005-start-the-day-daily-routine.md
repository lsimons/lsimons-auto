# 005 - Start-the-Day Daily Routine

**Purpose:** Automated morning startup sequence that runs desktop organization and background updates with once-per-day execution tracking

**Requirements:**
- Run sequence of automation tasks each morning at 7:00 AM
- Track execution state to prevent multiple runs per day
- Support `--force` flag to override daily limit when needed
- Persist execution state in TOML configuration file
- Provide colorized output with clear success/failure messages
- Integrate with macOS LaunchAgent for automated scheduling

**Design Approach:**
- Standalone script independent from auto CLI system
- Custom lightweight TOML parser for execution state tracking
- Configuration stored at `~/.start_the_day.toml` with ISO date format
- Daily task sequence: organize desktop → update background
- LaunchAgent integration via `install.py` for 7:00 AM execution
- Graceful error handling continues execution on individual task failures

**Implementation Notes:**
- Dependencies: Standard library only (subprocess, os, datetime)
- Task execution via `subprocess.run()` with `auto` CLI commands
- Exit codes: 0 for success/already-ran, 1 for errors
- State format: `last_run_date = "2024-01-15"` in TOML
- Log files: `~/.local/log/start-the-day.log` and `-error.log`
- Color output: Yellow greetings, blue progress, green success
- Test mode uses separate config file `~/.start_the_day_test.toml`

**Status:** Implemented