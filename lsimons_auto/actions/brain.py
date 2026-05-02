#!/usr/bin/env python3
"""
brain.py - Orchestrate local lsimons-brain repos.

Subcommands:
  ingest    Pull lsimons-brain and lsimons-brain-* repos, then run
            `mise run ingest` in lsimons-brain/.
"""

import argparse
import subprocess
import sys
from pathlib import Path

BRAIN_PARENT = Path.home() / "git" / "lsimons"
BRAIN_MAIN_DIR = BRAIN_PARENT / "lsimons-brain"
BRAIN_GLOB = "lsimons-brain*"


def find_brain_repos(parent: Path) -> list[Path]:
    """Return sorted list of existing brain repo working trees under parent."""
    if not parent.exists():
        return []
    repos = [p for p in sorted(parent.glob(BRAIN_GLOB)) if (p / ".git").exists()]
    return repos


def git_pull(repo: Path, dry_run: bool) -> bool:
    """Run `git pull` in repo. Return True on success (or in dry-run)."""
    if dry_run:
        print(f"Would run: git pull  (in {repo})")
        return True
    print(f"git pull in {repo}...")
    result = subprocess.run(["git", "pull"], cwd=repo, check=False)
    return result.returncode == 0


def run_mise_ingest(repo: Path, dry_run: bool) -> bool:
    """Run `mise run ingest` in repo. Return True on success (or in dry-run)."""
    if dry_run:
        print(f"Would run: mise run ingest  (in {repo})")
        return True
    print(f"mise run ingest in {repo}...")
    result = subprocess.run(["mise", "run", "ingest"], cwd=repo, check=False)
    return result.returncode == 0


def cmd_ingest(dry_run: bool) -> int:
    """Implement `auto brain ingest`."""
    repos = find_brain_repos(BRAIN_PARENT)
    if not repos:
        print(f"Error: no brain repos found under {BRAIN_PARENT}", file=sys.stderr)
        return 1

    pull_failures: list[Path] = []
    for repo in repos:
        if not git_pull(repo, dry_run):
            pull_failures.append(repo)

    if pull_failures:
        print(
            "Error: git pull failed for: " + ", ".join(str(p) for p in pull_failures),
            file=sys.stderr,
        )
        return 1

    if not BRAIN_MAIN_DIR.exists():
        print(f"Error: {BRAIN_MAIN_DIR} not found", file=sys.stderr)
        return 1

    if not run_mise_ingest(BRAIN_MAIN_DIR, dry_run):
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the brain action."""
    parser = argparse.ArgumentParser(
        prog="auto brain",
        description="Orchestrate local lsimons-brain repos.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    ingest = subparsers.add_parser(
        "ingest",
        help="do a full local lsimons brain ingest run",
        description=(
            "Do a full local lsimons brain ingest run: git pull lsimons-brain and "
            "every lsimons-brain-* repo, then run `mise run ingest` in lsimons-brain/."
        ),
    )
    ingest.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without doing it",
    )

    return parser


def main(args: list[str] | None = None) -> None:
    """Entry point for the brain action."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    if parsed.subcommand == "ingest":
        sys.exit(cmd_ingest(dry_run=parsed.dry_run))

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
