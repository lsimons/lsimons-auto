# 014 - Git Actions Upgrade

**Purpose:** Keep GitHub Actions `uses:` references across a set of local git repositories pinned to the latest stable release SHAs, with a single human confirmation step. Mechanizes the per-repo upgrade work previously done by hand or by an AI agent.

**Requirements:**
- Discover target repositories by scanning a root directory.
  - Default root: `~/git/lsimons` (aligns with 009's `git-sync` layout).
  - Works equally for unrelated roots, e.g. `~/git/typelinkmodel`.
  - A target is any directory containing a `.git/` and at least one `.github/workflows/*.y*ml` file.
- For each unique `uses: owner/repo@<ref>` across all discovered workflows:
  - Resolve the latest stable release tag via `gh api repos/<owner>/<repo>/releases/latest`.
  - Resolve that tag to a full-length commit SHA (two-hop deref for annotated tags).
  - Handle both "already pinned" (`@<sha>` with optional `# vN` comment) and "unpinned" (`@v4`) inputs symmetrically — unpinning-then-upgrading is the same algorithm as upgrading an already-pinned ref.
- Build a proposal grouped first by action, then by repo:
  - Per action: current → proposed version, with full SHA.
  - Per repo: affected files and ref counts.
  - Skipped: unknown actions (not in a known registry), archived remotes, local action refs (`./...`), already-latest refs.
- Prompt for confirmation before making any changes.
  - `--yes` / `-y` to skip the prompt.
  - `--dry-run` to run discovery + proposal but never apply, commit, or push.
- On confirmation, per repo:
  - Apply the rewrites (idempotent; re-running produces no diff).
  - One conventional commit per repo, referencing this spec number.
  - `git pull --rebase` then `git push`. On push failure due to archived remote (403), reset the local commit so the working tree matches origin; report these repos in the summary.
- Flags:
  - `--root DIR`: override scan root.
  - `-o/--owner OWNER`: only act on repos whose origin matches that owner (reusing git-sync's owner model).
  - `--dry-run`, `--yes`, `--verbose`.

**Design Approach:**
- New action `lsimons_auto/actions/git_actions_upgrade.py` (CLI: `auto git-actions-upgrade`).
- Introduce `lsimons_auto/github.py` as the shared module for this command, `git-actions-watch` (spec 015), and portions of `git-sync` (spec 009) that currently open-code repo iteration:
  - `iter_local_repos(root: Path) -> Iterator[Path]`
  - `iter_workflow_files(repo: Path) -> Iterator[Path]`
  - `parse_uses(line: str) -> Optional[UsesRef]` — yields `(owner, name, ref, is_sha, comment)`
  - `resolve_latest(owner: str, name: str) -> tuple[str, str]` — returns `(tag, sha)`; wraps `gh api releases/latest` and the tag-to-SHA deref
  - `rewrite_workflow(path: Path, upgrades: Mapping[str, tuple[str, str]]) -> int` — line-oriented regex rewriter that preserves indentation and restores the `# vN` trailing comment
- Line-oriented regex rather than full YAML parsing: `^(\s*uses:\s+)(\S+)(\s*(?:#.*)?)$`. This keeps file formatting identical under no-op runs and avoids taking a YAML dependency for a tool whose job is to preserve-and-edit.
- Latest-version policy (captured from the April 2026 session):
  - Default: upgrade to the action repo's latest release, even across major boundaries.
  - The trailing `# vN` comment holds the resolved major tag (e.g. `# v6`, not `# v6.0.2`) so Dependabot recognizes the version line.
  - Transitive unpinned deps (e.g. `upload-pages-artifact@v3` internally uses `upload-artifact@v4`) are NOT detected here; they manifest as CI failures and are surfaced by `git-actions-watch`. Document the limitation rather than attempt recursive inspection.
- `sha_pinning_required` GitHub setting is assumed to already be on; configuring it is a one-time repo setup, out of scope for an ongoing upgrade command.

**Implementation Notes:**
- Reuses `utils.run_command` / `handle_error` and follows the action template from 000-shared-patterns.
- Network dependencies: `gh` CLI (action release lookups) and `git` (fetch/pull/push). Fail fast with a helpful message if either is missing or unauthenticated.
- Release resolution is O(unique actions), not O(repos × uses), so no on-disk cache is needed for typical runs (~15 unique actions).
- Tests (`tests/test_git_actions_upgrade.py`):
  - Unit: `parse_uses`, regex invariants, proposal aggregation, rewrite idempotence.
  - Integration: fixture directory of fake repos + recorded `gh api` JSON responses; verify dry-run output and file rewrites end to end.
- Pairs with `git-actions-watch` (spec 015): upgrade prints a final line suggesting `auto git-actions-watch --recent` to follow CI.

**Status:** Draft
