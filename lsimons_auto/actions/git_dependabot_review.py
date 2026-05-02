#!/usr/bin/env python3
"""
git_dependabot_review.py - Review and (optionally) merge Dependabot PRs.

Lists every open Dependabot PR across local repos, summarises bump kind and
CI status, and with --apply squash-merges PRs whose CI rollup is fully green.

See docs/spec/017-git-dependabot-review.md.
"""

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from lsimons_auto.github import get_origin_repo, iter_local_repos

DEFAULT_ROOT = Path.home() / "git" / "lsimons"

# Matches the bump clause Dependabot puts in every title, regardless of the
# conventional-commits scope/prefix or trailing `in /<dir>` annotation.
TITLE_RE = re.compile(
    r"\bbump\s+(?P<dep>\S+)\s+from\s+(?P<old>\S+)\s+to\s+(?P<new>\S+)",
    re.IGNORECASE,
)


@dataclass
class DepPR:
    repo: str  # "owner/name"
    number: int
    title: str
    dep: str
    old: str
    new: str
    bump: str  # major | minor | patch | unknown
    ci: str  # SUCCESS | FAILURE | PENDING | MIXED


def parse_title(title: str) -> tuple[str, str, str] | None:
    """Extract `(dep, old, new)` from a Dependabot PR title, or None."""
    m = TITLE_RE.search(title)
    if m is None:
        return None
    return m.group("dep"), m.group("old"), m.group("new")


def _split_semver(s: str) -> list[int] | None:
    parts = s.lstrip("v").split(".")
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            return None
    while len(out) < 3:
        out.append(0)
    return out[:3]


def classify_bump(old: str, new: str) -> str:
    """Return one of: major, minor, patch, unknown."""
    o = _split_semver(old)
    n = _split_semver(new)
    if o is None or n is None:
        return "unknown"
    if o[0] != n[0]:
        return "major"
    if o[1] != n[1]:
        return "minor"
    return "patch"


def aggregate_ci(checks: Sequence[object]) -> str:
    """Reduce a statusCheckRollup list to SUCCESS / FAILURE / PENDING / MIXED.

    Treats unknown / empty entries as pending-equivalent.
    """
    if not checks:
        return "PENDING"
    states: list[str] = []
    for c in checks:
        if not isinstance(c, Mapping):
            continue
        check: Mapping[object, object] = c  # pyright: ignore[reportUnknownVariableType]
        conclusion = check.get("conclusion")
        status = check.get("status")
        states.append(str(conclusion or status or "").upper())
    if not states:
        return "PENDING"
    if any(s == "FAILURE" for s in states):
        return "FAILURE"
    if all(s == "SUCCESS" for s in states):
        return "SUCCESS"
    if all(s in ("SUCCESS", "QUEUED", "IN_PROGRESS", "PENDING", "") for s in states):
        return "PENDING"
    return "MIXED"


def _gh_pr_list(repo: str) -> list[dict[str, object]]:
    cmd = [
        "gh",
        "pr",
        "list",
        "-R",
        repo,
        "--author",
        "app/dependabot",
        "--state",
        "open",
        "--json",
        "number,title,mergeable,statusCheckRollup",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [d for d in data if isinstance(d, dict)]  # pyright: ignore[reportUnknownVariableType]


def build_pr(repo: str, raw: Mapping[str, object]) -> DepPR:
    title = str(raw.get("title", ""))
    parsed = parse_title(title)
    if parsed is None:
        dep, old, new = "?", "?", "?"
        bump = "unknown"
    else:
        dep, old, new = parsed
        bump = classify_bump(old, new)
    rollup_raw = raw.get("statusCheckRollup")
    rollup: list[object] = []
    if isinstance(rollup_raw, list):
        rollup = list(rollup_raw)  # pyright: ignore[reportUnknownArgumentType]
    number_raw = raw.get("number") or 0
    number = int(number_raw) if isinstance(number_raw, (int, str)) else 0
    return DepPR(
        repo=repo,
        number=number,
        title=title,
        dep=dep,
        old=old,
        new=new,
        bump=bump,
        ci=aggregate_ci(rollup),
    )


def list_dependabot_prs(repo: str) -> list[DepPR]:
    return [build_pr(repo, raw) for raw in _gh_pr_list(repo)]


def collect_prs(root: Path, owner: str | None) -> list[DepPR]:
    prs: list[DepPR] = []
    for repo_path in iter_local_repos(root):
        gh_repo = get_origin_repo(repo_path)
        if gh_repo is None:
            continue
        repo_owner, repo_name = gh_repo
        if owner is not None and repo_owner != owner:
            continue
        prs.extend(list_dependabot_prs(f"{repo_owner}/{repo_name}"))
    return prs


def render_lines(prs: Sequence[DepPR]) -> list[str]:
    if not prs:
        return ["No open Dependabot PRs."]
    width_repo = max(len(p.repo) for p in prs)
    width_dep = max(len(p.dep) for p in prs)
    out: list[str] = []
    for p in prs:
        out.append(
            f"  {p.repo:<{width_repo}}  "
            f"#{p.number:<4}  "
            f"{p.bump.upper():<7}  "
            f"{p.dep:<{width_dep}}  "
            f"{p.old} -> {p.new}  "
            f"ci={p.ci}"
        )
    return out


def render(prs: Sequence[DepPR]) -> None:
    for line in render_lines(prs):
        print(line)


def merge_pr(pr: DepPR) -> tuple[bool, str]:
    """Squash-merge a PR. Returns (success, message)."""
    if pr.ci != "SUCCESS":
        return False, f"ci={pr.ci}"
    cmd = [
        "gh",
        "pr",
        "merge",
        str(pr.number),
        "-R",
        pr.repo,
        "--squash",
        "--delete-branch",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "merge failed"
        return False, msg
    return True, "merged"


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="auto git-dependabot-review",
        description="List and optionally merge open Dependabot PRs across local repos.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="scan root")
    parser.add_argument("-o", "--owner", default=None, help="filter repos by origin owner")
    parser.add_argument(
        "--bump",
        choices=("patch", "minor", "major"),
        action="append",
        default=None,
        help="only act on bumps of this kind (repeatable; default: all)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="squash-merge listed PRs whose CI is SUCCESS (default: dry run)",
    )
    parsed = parser.parse_args(args)

    root: Path = parsed.root
    if not root.is_dir():
        print(f"Error: root not found: {root}", file=sys.stderr)
        sys.exit(1)

    prs = collect_prs(root, parsed.owner)
    if parsed.bump:
        prs = [p for p in prs if p.bump in parsed.bump]

    render(prs)
    if not prs:
        return

    if not parsed.apply:
        print(f"\n{len(prs)} PR(s). Re-run with --apply to merge those passing CI.")
        return

    print("\nMerging...")
    merged = 0
    skipped = 0
    for p in prs:
        ok, msg = merge_pr(p)
        marker = "OK   " if ok else "SKIP "
        print(f"  {marker} {p.repo}#{p.number}: {msg}")
        if ok:
            merged += 1
        else:
            skipped += 1
    print(f"\nmerged={merged} skipped={skipped}")
    if skipped and not merged:
        sys.exit(1)


if __name__ == "__main__":
    main()
