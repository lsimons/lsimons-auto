# Agent Instructions for lsimons-auto

> This file (`AGENTS.md`) is the canonical agent configuration. `CLAUDE.md` is a symlink to this file.

Personal automation toolkit for macOS with modular CLI (`auto`) and daily routine (`start-the-day`).

## Quick Reference

- **One-time**: `mise install`
- **Setup**: `mise run install`
- **Install (system)**: `python3 install.py`
- **Test (unit)**: `mise run test`
- **Test (integration)**: `mise run test:integration`
- **Lint**: `mise run lint` (ruff check + format --check)
- **Typecheck**: `mise run typecheck` (basedpyright)
- **Format**: `mise run format`
- **Run**: `auto <action_name>` or `start-the-day`
- **Full CI gate**: `mise run ci`

## Structure

Actions live in `lsimons_auto/actions/`. Each is a self-contained Python script with `main(args: Optional[list[str]] = None)` function.

**Adding a new action:**
1. Create spec in `docs/spec/`
2. Implement in `lsimons_auto/actions/`
3. Add tests in `tests/`

## Guidelines

**Code quality:**
- Full type annotations (strict basedpyright)
- PEP 8 formatting
- Unit tests (fast, no side effects) run by default
- Integration tests marked with `@pytest.mark.integration`

**Specs:** Focus on design decisions, keep under 100 lines, reference shared patterns.

**Pyright ignores:** Use specific codes like `# pyright: ignore[reportAny]`

## Commit Message Convention

Follow [Conventional Commits](https://conventionalcommits.org/):

**Format:** `type(scope): description`

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `build`, `ci`, `perf`, `revert`, `improvement`, `chore`

Reference spec numbers: `feat(actions): implement organize-desktop (spec-004)`

## Session Completion

Work is NOT complete until CI passes on the pushed commit.

1. **Quality gates** (if code changed):
   ```bash
   mise run ci
   ```

2. **Push**:
   ```bash
   git pull --rebase && git push
   git status  # must show "up to date with origin"
   ```

3. **Verify CI**:
   ```bash
   mise run ci-watch
   ```
   On failure, inspect with `gh run view --log-failed`, fix, push, and re-watch.

Never stop before CI is green. If push or CI fails, resolve and retry.
