# 018 - Brain Action

**Purpose:** Provide an `auto brain` subcommand group that orchestrates the local
`lsimons-brain` repos. The first subcommand, `ingest`, performs a full local
brain ingest run.

**Requirements:**
- Add a single action `brain` exposed via the `auto` dispatcher with internal
  subcommands (so `auto brain ingest` works today and `auto brain <other>` can
  be added later).
- `auto brain ingest`:
  - Run `git pull` in `~/git/lsimons/lsimons-brain/` and in every sibling
    directory matching `~/git/lsimons/lsimons-brain-*/` that is a git working
    tree.
  - After pulls succeed, change into `~/git/lsimons/lsimons-brain/` and run
    `mise run ingest`.
  - Help text should read along the lines of "do a full local lsimons brain
    ingest run".
- Help (`auto brain --help`) lists available subcommands.
- Support `--dry-run` to print what would happen without running git or mise.

**Design Approach:**
- Standard action script template with `argparse` subparsers — the dispatcher
  passes through unparsed args, so the action handles its own subcommand
  routing.
- Reuse `subprocess.run` directly for git/mise; no need for the heavier helpers
  in `git_sync.py` because we only do a plain `git pull` per repo.
- Skip non-existent repos with a warning rather than failing — the
  `lsimons-brain-*` set varies by host (e.g. `lsimons-brain-data` is sbp-only).
- Exit non-zero if `mise run ingest` fails or any repo's `git pull` fails;
  pulls are attempted for all repos before reporting failure so a transient
  failure on one repo is visible alongside the others.

**Implementation Notes:**
- Brain repos live under `~/git/lsimons/`; resolve with `Path.home() / "git" /
  "lsimons"` and `glob("lsimons-brain*")`.
- `mise run ingest` is invoked with `cwd=~/git/lsimons/lsimons-brain/`; output
  is streamed to the user's terminal (do not capture).
- No new dependencies.

**Status:** Implemented
