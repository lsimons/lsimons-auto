# GitHub Copilot Repository Onboarding Instructions

These instructions help a GitHub-based coding agent (Copilot-type code assistant) work effectively in this repository. They supplement (not replace) the canonical agent guidance in `AGENTS.md` — ALWAYS read and follow `AGENTS.md` first. That file defines the authoritative workflow, response style, and development philosophy. This file only adds GitHub / PR / repo-collaboration specific practices and guardrails.

## Core Principles (Reinforced for GitHub Context)
- Single source of truth for general process: `AGENTS.md`
- Spec-first: Do NOT implement a non-trivial feature without a spec in `docs/spec/`
- Keep the code minimal, functional, dependency-light
- Never introduce new third‑party packages unless a spec explicitly justifies it
- Prefer small, focused changes per PR (one spec or one fix)

## When Starting a Task
1. Identify whether it's:
   - A new feature → Check for existing numbered spec in `docs/spec/`
   - A bug / refinement → Open/update a spec only if design impact exists
2. If spec is missing for a feature-level change: propose adding `docs/spec/NNN-something.md`
3. Confirm location of target files instead of guessing (e.g. actions live in `lsimons_auto/actions/`)

## File & Architecture Orientation
- Dispatcher: `lsimons_auto/lsimons_auto.py`
- Daily routine: `lsimons_auto/start_the_day.py` (standalone command: `start-the-day`)
- Actions directory: `lsimons_auto/actions/*.py` (auto-discovered; must expose `main(args: Optional[list[str]] = None)`)
- Specs: `docs/spec/*.md` (sequential numbering, keep concise)
- Design rationale: `DESIGN.md`
- Cross-agent rules: `AGENTS.md`
- Claude-specific notes (do not duplicate here): `CLAUDE.md`
- LaunchAgent templates: `etc/`
- Tests: `tests/`

## Adding a New Action (GitHub Workflow Focus)
1. Create/verify spec: `docs/spec/NNN-new-action-name.md`
2. Implement: `lsimons_auto/actions/new_action_name.py` using the template in `docs/spec/000-shared-patterns.md`
3. Add tests: `tests/test_new_action_name.py`
4. Update `README.md` "Available Actions" section
5. Commit messages reference the spec number: e.g. `NNN: implement new action dispatcher integration`
6. Do NOT modify the dispatcher for discovery; it must remain dynamic.

## Commit Message Conventions
- Feature implementation: `00X: short description`
- Bug fix referencing file: `fix: organize_desktop date folder creation edge case`
- Spec addition: `00X: add spec for <feature>`
- Avoid verbose narratives—keep messages actionable
- Group logically related changes; avoid multi-topic commits

## Pull Request (PR) Guidelines
Provide a concise PR description including:
- What changed
- Why (reference spec number or rationale)
- Testing performed (`uv run pytest`, mention any added tests)
- Any potential follow-ups

DO NOT open PRs that mix:
- Spec authoring + multiple implementations
- Refactors + new feature logic
- Formatting-only noise + functional changes

## Testing Expectations
- Always run: `uv run pytest`
- Add tests for new behaviors; prefer integration-style
- Use temp dirs (follow patterns in existing tests)
- Avoid network or side-effect heavy test additions

## Type & Diagnostic Handling
- Maintain type annotations
- Only use targeted Pyright ignores:
  - `# pyright: ignore[reportAny]`
  - `# pyright: ignore[reportImplicitOverride]`
- Do NOT blanket-ignore entire files
- If adding dynamic argparse logic, keep it readable and minimally reflective

## Style & Code Quality
- Favor plain functions over classes unless a spec justifies otherwise
- Keep argument parsing straightforward
- Avoid introducing global state or hidden side effects
- Log/print user-facing messages plainly (no color dependencies except simple ANSI already in use)
- Maintain graceful error handling: fail a single action without crashing the rest of a routine where applicable

## Installation & Runtime Assumptions
- Scripts installed to `~/.local/bin/`
- `uv` is the package manager assumed
- macOS specific paths (e.g. LaunchAgent usage) must remain intact unless a spec broadens scope

## Safe Modification Checklist (Before Committing)
- Did I read `AGENTS.md` again for alignment?
- Does change match an existing spec? If not, should one be created?
- Are tests added or adjusted? (`tests/`)
- Did I avoid speculative abstractions?
- Are doc updates needed (README, DESIGN, or new spec)?
- Could this silently break action discovery or daily routine scheduling?

## What NOT to Do Without a Spec
- Introduce dependency management changes
- Convert functional scripts into classes
- Add caching layers
- Replace TOML parsing with external libs
- Change the dynamic discovery model
- Add asynchronous concurrency

## Handling Bugs
- Reproduce first
- Add/extend a test that fails pre-fix
- Apply the smallest corrective change
- Reference impacted file(s) in commit title/body

## Documentation Touch Points
Update the following only when necessary:
- `README.md` — user-facing capabilities (new action, new routine behavior)
- `DESIGN.md` — architectural or cross-cutting decision changes
- `docs/spec/` — new or revised feature design
- Do NOT duplicate high-level philosophy already in `AGENTS.md`

## LaunchAgent / Scheduling Notes
- Do not change timing defaults (7:00 AM) unless a spec states a new scheduling policy
- If modifying output/logging, ensure existing log path assumptions remain valid

## Performance & Scalability
- Current scale is personal automation; avoid premature optimization
- Only optimize if a spec or test reveals measurable slowness

## Security / Safety Considerations
- Avoid executing arbitrary shell input
- Validate external file operations (e.g., Desktop file handling)
- Keep subprocess usage constrained and explicit

## If Unsure
1. Re-read `AGENTS.md`
2. Inspect analogous existing action or spec
3. Propose a minimal spec stub rather than guessing
4. Keep the PR small and reviewable

## Quick Reference Commands
- Full test run: `uv run pytest`
- Single test file: `uv run pytest tests/test_start_the_day.py`
- Install (create/update wrappers): `python3 install.py`

## Final Reminder
AGENTS.md is the governing document. This file is a GitHub operational layer: PR discipline, commit hygiene, change scoping, and safeguards to preserve the established minimalist, spec-driven architecture.

Stay small. Stay explicit. Ship only what is specified.
