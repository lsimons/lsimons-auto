# 015 - Git Actions Watch

**Purpose:** Show GitHub Actions CI status per repo for a set of local repositories, one-shot or follow-mode. Stand-alone command; pairs with `git-actions-upgrade` (spec 014) but is useful on its own for post-push sanity checking.

**Requirements:**
- Accept the same root-scan and owner filters as `git-actions-upgrade`:
  - `--root DIR` (default `~/git/lsimons`).
  - `-o/--owner OWNER`.
- Subject selection:
  - Default: for each discovered repo, the latest workflow run for the commit currently at `HEAD`.
  - `--recent`: any run whose `createdAt` is within the last N minutes (default 10), regardless of commit — useful right after `git-actions-upgrade` finishes pushing.
  - `--latest`: the latest run overall, regardless of commit or time.
- Output format (one line per repo):
  - repo name (left-padded to the longest in the set)
  - status icon (see mapping below)
  - conclusion or status label
  - short commit SHA
  - workflow name (or count when multiple workflows ran for the same commit)
  - run URL (muted/grey, shown on failure or with `--verbose`)
- Two modes:
  - One-shot (default): print once and exit.
  - Follow (`-f/--follow`): re-poll repos with in-progress runs; update output in place until all are terminal or `--timeout` (default 20 min) elapses.
- Exit code:
  - `0` if every discovered repo's latest run is `success`, `skipped`, or has no run at all.
  - `1` if any run is `failure` / `cancelled` / `timed_out`.
  - `2` if any run is still `in_progress` and follow mode was not used.

**Design Approach:**
- New action `lsimons_auto/actions/git_actions_watch.py` (CLI: `auto git-actions-watch`).
- Reuses `lsimons_auto/github.py` helpers introduced by spec 014 (`iter_local_repos`, owner-origin parsing).
- Per repo, preferred query:
  ```
  gh run list --repo <owner>/<name> --commit <sha> --limit 1 --json \
    status,conclusion,displayTitle,url,workflowName,createdAt,headSha
  ```
  Falls back to `--limit 1` without `--commit` when in `--recent` or `--latest` mode.
- `gh run watch` deliberately not used — it blocks on one run at a time and doesn't compose with multi-repo follow mode. Follow mode here is a polling loop with backoff.
- Rendering:
  - In-place updates use `\r` plus cursor-up/clear ANSI; falls back to line-by-line when stdout is not a TTY or `NO_COLOR` is set.
  - Poll interval 5s, backing off to 15s after 1 minute. `--timeout` caps total wait.
- No terminal alt-screen, no curses — keeps it usable through `tee`, CI logs, and `script(1)`.

**Implementation Notes:**
- Status/conclusion → label/color mapping:
  - `queued` / `in_progress` → `running` (yellow dim)
  - `completed` + `success` → `ok` (green)
  - `completed` + `failure` / `cancelled` / `timed_out` → `failed` (red)
  - `completed` + `skipped` → `skipped` (dim)
  - no run found for commit → `pending` (dim)
- Archived repos: `gh run list` returns an empty set; rendered as `skipped (archived)` and excluded from the exit-code reduction.
- Tests (`tests/test_git_actions_watch.py`):
  - Snapshot tests on the renderer: given a list of `(repo, run_json_or_none)` tuples, assert rendered text.
  - Unit tests on the exit-code reduction and follow-loop termination condition (no real `gh` calls; inject a fake command runner).
- Composition with spec 014: `git-actions-upgrade` closes with a hint of the form `auto git-actions-watch --recent --follow`; no implicit coupling beyond that.

**Status:** Draft
