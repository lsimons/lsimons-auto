# GitHub Copilot Repository Onboarding Instructions

This file provides ONLY GitHub collaboration and workflow layering. All core development rules (spec-first process, testing requirements, diagnostic handling, style, action architecture) are defined in `AGENTS.md`. Do not restate them here; treat that file as authoritative.

## Scope
Use this document for:
- Deciding how to structure a PR
- Commit message patterns
- When to add or reference a spec
- Minimal checklists before pushing
Everything else → read `AGENTS.md`.

## When Beginning Work
1. Confirm the task type:
   - Feature → there MUST be a numbered spec in `docs/spec/`
   - Minor fix / doc tweak → no spec unless design impact
2. If a spec is needed and missing: create `docs/spec/NNN-short-name.md` (keep it concise; follow shared patterns).
3. Locate target files (do not guess paths). Actions live in `lsimons_auto/actions/`.

## Minimal Action Addition Checklist (Workflow Layer)
- Spec exists (referenced by number)
- New action file in `lsimons_auto/actions/` exposing `main(...)`
- Test file in `tests/`
- README updated with a one-line action summary
- Commit message starts with spec number (e.g. `008: add foo action`)
- No dispatcher modification (discovery must remain dynamic)

## Commit Message Conventions
- Feature: `00X: short imperative summary`
- Spec authoring: `00X: add spec for <purpose>`
- Bug fix: `fix: <area> <concise issue>`
- Avoid multi-topic commits; split if unrelated.

## Pull Request Guidelines
PR description should state:
- What changed (one paragraph max)
- Why (reference spec number or explain fix)
- Tests added/updated (`uv run pytest` must pass)
- Any intentional omissions or follow-ups

Avoid PRs that combine unrelated concerns (e.g. refactor + feature + formatting).

## Documentation Touch Points (When to Touch)
- `README.md`: only for user-visible capability changes
- `DESIGN.md`: only for cross-cutting architectural decisions
- `docs/spec/`: new or revised feature definitions
If you find yourself duplicating philosophy → stop and link `AGENTS.md`.

## Safe Change Checklist (Pre-Commit)
- Matches an existing spec (or clearly a trivial fix)
- Tests added/updated
- No accidental dispatcher coupling
- No new dependencies
- No unapproved architectural shifts
- Docs updated only where necessary

## Handling a Bug
1. Reproduce
2. Add or adjust a failing test
3. Apply smallest fix
4. Commit with clear scope
5. Do not opportunistically refactor unrelated code in same PR.

## Security / Safety (Workflow Reminders)
- Do not broaden shell execution surfaces
- Keep subprocess usage explicit
- Avoid hidden global state additions

## What Is Intentionally NOT Repeated Here
- Spec format and philosophy
- Diagnostic suppression rules
- Style and type guidance
- Detailed testing philosophy
All of that is in `AGENTS.md`.

## Quick Reference
- Run tests: `uv run pytest`
- Single test file: `uv run pytest tests/test_start_the_day.py`
- Install/update wrappers: `python3 install.py`

## If Unsure
1. Re-read `AGENTS.md`
2. Look at an existing similar spec or action
3. Propose a tiny spec stub if direction unclear
4. Keep the PR small

## Final Note
This file is a thin GitHub-facing layer. If you need to add more here, first ask: “Is this already guaranteed by AGENTS.md?” If yes—link it instead of repeating it.
