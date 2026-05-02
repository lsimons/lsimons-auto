# 017 - Git Dependabot Review

**Purpose:** Triage and (optionally) merge open Dependabot PRs across every local repo from one place, instead of clicking through GitHub repo by repo.

**Requirements:**
- Same root-scan and owner filters as `git-actions-watch` / `git-actions-upgrade`:
  - `--root DIR` (default `~/git/lsimons`).
  - `-o/--owner OWNER`.
- Per-PR output (one line per PR):
  - repo (`owner/name`)
  - PR number
  - bump kind: `MAJOR` / `MINOR` / `PATCH` / `UNKNOWN`
  - dependency name (e.g. `@biomejs/biome`, `actions/checkout`)
  - version transition (`old → new`)
  - CI rollup status (`SUCCESS` / `FAILURE` / `PENDING` / `MIXED`)
- Filtering:
  - `--bump {patch,minor,major}` (repeatable) to limit which PRs are listed/merged.
- Two modes:
  - Default (dry-run): print summary only.
  - `--apply`: squash-merge each listed PR whose CI rollup is `SUCCESS`. PRs with non-success CI are skipped with a one-line reason.

**Design Approach:**
- New action `lsimons_auto/actions/git_dependabot_review.py` (CLI: `auto git-dependabot-review`).
- Reuses `lsimons_auto/github.py` helpers (`iter_local_repos`, `get_origin_repo`).
- Discovery query per repo:
  ```
  gh pr list -R <owner>/<name> --author "app/dependabot" --state open \
    --json number,title,additions,deletions,changedFiles,mergeable,statusCheckRollup
  ```
- Title parsing: a single regex against the conventional Dependabot title shape `bump <dep> from <old> to <new>` (case-insensitive). Bump classification compares dotted-numeric segments; non-semver versions degrade to `UNKNOWN`.
- Merge command (with `--apply`):
  ```
  gh pr merge <number> -R <owner>/<name> --squash --delete-branch
  ```
- Safety: never merge a PR whose CI rollup is not pure `SUCCESS`. No `--admin`, no force.

**Implementation Notes:**
- Title regex needs to accept all forms Dependabot emits: `bump`, `Bump`, with or without scope (`chore(deps-dev): Bump ...`), with or without trailing `in /<directory>`. The scope/prefix is irrelevant — only the `bump <dep> from X to Y` clause matters.
- CI rollup aggregation: any FAILURE → FAILURE; all SUCCESS → SUCCESS; mix of SUCCESS + PENDING → PENDING; otherwise MIXED. Treat unknown / null status as PENDING for the purpose of merge eligibility.
- Tests (`tests/test_git_dependabot_review.py`): bump classifier (patch/minor/major/unknown), title parsing on real-world Dependabot titles, CI rollup aggregation, render snapshot.
- No `gh` calls in unit tests — inject pure data into the rendering / merge-decision functions.
- Composition: this is the post-`git-actions-watch` step. `git-actions-watch` confirms the repo's CI is green; once that is true, `git-dependabot-review --apply` cleans up the open Dependabot queue.

**Status:** Implemented
