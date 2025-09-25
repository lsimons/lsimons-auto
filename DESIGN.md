# Design Decisions

This document captures key design decisions for the lsimons-auto project. For detailed feature specifications, see the [specs directory](docs/spec/).

## Core Philosophy
- **Dependency-free core**: Core functionality uses only Python3 standard library (os, sys, datetime, argparse, unittest)
- **Selective dependencies**: Image processing (Pillow) only when needed for specific actions
- **Organized structure**: Main code in `lsimons_auto/`, tests in `tests/`, configuration in `etc/`
- **Functional approach**: Avoids OOP, uses simple functions for clarity and maintainability

## Action Script Architecture
- **Modular design**: Individual Python scripts in `lsimons_auto/actions/`
- **Dual execution**: Each action works standalone and as importable module
- **Standard interface**: All actions have `main(args: Optional[list[str]] = None)` function
- **Unified CLI**: Command dispatcher routes subcommands to individual actions
- **Discovery mechanism**: Dispatcher automatically finds actions by scanning directory

## Installation & Integration
- **Standard locations**: Scripts in `~/.local/bin/`, config in `~/.local/share/lsimons-auto/`, logs in `~/.local/log/`
- **Virtual environment**: Wrapper scripts activate project `.venv` for proper dependencies
- **macOS integration**: LaunchAgent for automated daily execution at 7:00 AM
- **File permissions**: Executables 755, configuration 600, logs 644

## State Management
- **State tracking**: Uses ~/.start_the_day.toml to track execution state and prevent multiple runs per day
- **Cross-day detection**: Uses date comparison rather than 24-hour intervals for "daily" logic
- **TOML format**: Human-readable config format, implemented with simple parsing/writing

## Error Handling & Reliability
- **Graceful degradation**: Continue execution when individual tasks fail, with clear error messages
- **Exit codes**: 0 for success/already-ran, 1 for errors, 2 for test failures
- **User-friendly errors**: Print descriptive messages, avoid stack traces for expected failures
- **File operations**: Create parent directories automatically, handle permissions gracefully
- **Subprocess calls**: Use `check=True` and catch `CalledProcessError` with context

## Testing Strategy
- **Integration-first**: Prefer end-to-end tests over mocking for reliability
- **Test separation**: Unit tests in dedicated `tests/` directory using Python's unittest framework
- **Real I/O testing**: Use separate config files (~/.start_the_day_test.toml) rather than complex mocking
- **CLI testing**: Test both standalone execution and programmatic usage
- **Temporary directories**: Use temp paths for file system tests to avoid conflicts

## Code Quality
- **Type safety**: Comprehensive type annotations for better IDE support and static analysis
- **Acceptable diagnostics**: Some remaining warnings for argparse/unittest patterns that are inherently dynamic
- **Pyright ignores**: Use specific error codes (`reportAny`, `reportImplicitOverride`) when needed

## Development Process
- **Spec-driven development**: New features documented in `docs/spec/` before implementation
- **Concise specs**: Focus on design decisions, reference shared patterns, avoid implementation details
- **Design documentation**: This file updated with architectural decisions made during feature implementation