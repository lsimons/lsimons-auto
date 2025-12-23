#!/usr/bin/env python3
"""
git_sync.py - Synchronize GitHub repositories

This action fetches all repositories for user 'lsimons' and syncs them locally.
Active repos go to ~/git/lsimons.
Archived repos go to ~/git/lsimons/archive.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> bool:
    """
    Run a shell command.
    Returns True if successful, False otherwise.
    Output is suppressed unless the command fails.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        if cwd:
            print(f"  Directory: {cwd}")
        print("  Output:")
        print(e.stdout)
        return False


def get_repos(owner: str, archive: bool = False) -> list[str]:
    """Fetch list of repositories using gh CLI."""
    # gh repo list owner -L 1000 --json name,isFork,isArchived
    cmd = [
        "gh",
        "repo",
        "list",
        owner,
        "-L",
        "1000",
        "--json",
        "name,isFork,isArchived",
    ]
    try:
        result = subprocess.run(
            cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        repos_data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching repo list: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing gh output: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'gh' command not found. Please install GitHub CLI.")
        sys.exit(1)

    # Filter repos
    # .[] | select(.isFork == false && .isArchived == false) | .name
    filtered_repos = []
    for repo in repos_data:
        if repo.get("isFork") is True:
            continue
        
        is_repo_archived = repo.get("isArchived", False)
        if archive and is_repo_archived:
            filtered_repos.append(repo["name"])
        elif not archive and not is_repo_archived:
            filtered_repos.append(repo["name"])

    return filtered_repos


def sync_repo(owner: str, repo_name: str, target_dir: Path) -> None:
    """Sync a single repository."""
    repo_path = target_dir / repo_name
    
    if repo_path.exists():
        # git fetch --all
        print(f"Updating {owner}/{repo_name}...")
        success = run_command(["git", "fetch", "--all"], cwd=repo_path)
    else:
        # git clone
        print(f"Cloning {owner}/{repo_name}...")
        repo_url = f"https://github.com/{owner}/{repo_name}.git"
        success = run_command(["git", "clone", repo_url], cwd=target_dir)

    if not success:
        print(f"Failed to sync {owner}/{repo_name}")


def main(args: Optional[list[str]] = None) -> None:
    """Main function that performs the action work."""
    parser = argparse.ArgumentParser(description="Synchronize GitHub repositories")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print what would be done without doing it"
    )
    parser.add_argument(
        "--include-archive",
        action="store_true",
        help="Include archived repositories in the sync",
    )
    parsed_args = parser.parse_args(args)

    base_dir = Path.home() / "git"
    owners = ["lsimons", "typelinkmodel"]

    for owner in owners:
        owner_dir = base_dir / owner
        archive_dir = owner_dir / "archive"

        # Create directories
        if not parsed_args.dry_run:
            owner_dir.mkdir(parents=True, exist_ok=True)
            archive_dir.mkdir(parents=True, exist_ok=True)
        else:
            print(f"Would create directories: {owner_dir}, {archive_dir}")

        # Sync active repos
        print(f"Fetching active repository list for {owner}...")
        active_repos = get_repos(owner=owner, archive=False)
        print(f"Found {len(active_repos)} active repositories for {owner}.")

        for repo in active_repos:
            if parsed_args.dry_run:
                print(f"Would sync active repo: {owner}/{repo} to {owner_dir}")
            else:
                sync_repo(owner, repo, owner_dir)

        # Sync archived repos
        if parsed_args.include_archive:
            print(f"Fetching archived repository list for {owner}...")
            archived_repos = get_repos(owner=owner, archive=True)
            print(f"Found {len(archived_repos)} archived repositories for {owner}.")

            for repo in archived_repos:
                if parsed_args.dry_run:
                    print(f"Would sync archived repo: {owner}/{repo} to {archive_dir}")
                else:
                    sync_repo(owner, repo, archive_dir)


if __name__ == "__main__":
    main()
