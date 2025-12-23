# 009 - Git Sync Action

**Purpose:** Synchronize git repositories from GitHub for user `lsimons` to the local machine.

**Requirements:**
- Ensure `~/git/lsimons` and `~/git/lsimons/archive` exist.
- Fetch list of repositories using `gh` CLI.
  - Active repos: `isFork == false && isArchive == false` -> `~/git/lsimons`
  - Archived repos: `isFork == false && isArchive == true` -> `~/git/lsimons/archive`
- For each repository:
  - If it doesn't exist locally: `git clone`
  - If it exists locally: `git fetch --all`
- Suppress git output unless there is an error (non-zero exit code).

**Design Approach:**
- Use `subprocess` to call `gh` and `git` commands.
- Parse `gh` output (JSON) to get repository lists.
- Iterate through lists and perform sync operations.
- Use a helper function for running shell commands that handles output buffering and error reporting.

**Implementation Notes:**
- Dependencies: `gh` (GitHub CLI) must be installed and authenticated. `git` must be installed.
- Error handling: If `gh` fails, abort. If a single repo fails to sync, log error and continue with others.
- Path handling: Use `pathlib` for all path manipulations.
- The action name will be `git_sync.py` (which maps to `auto git-sync`).

**Status:** Draft
