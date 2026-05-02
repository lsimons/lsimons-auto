"""Tests for lsimons_auto.actions.git_dependabot_review."""

from lsimons_auto.actions.git_dependabot_review import (
    DepPR,
    aggregate_ci,
    build_pr,
    classify_bump,
    parse_title,
    render_lines,
)


def test_parse_title_simple() -> None:
    title = "chore(deps): bump foo from 1.2.3 to 1.2.4"
    assert parse_title(title) == ("foo", "1.2.3", "1.2.4")


def test_parse_title_capitalized_bump() -> None:
    title = "chore(deps-dev): Bump @biomejs/biome from 2.4.12 to 2.4.13"
    assert parse_title(title) == ("@biomejs/biome", "2.4.12", "2.4.13")


def test_parse_title_with_directory_suffix() -> None:
    title = "chore(deps): bump hashicorp/aws from 6.33.0 to 6.42.0 in /terraform/foo"
    assert parse_title(title) == ("hashicorp/aws", "6.33.0", "6.42.0")


def test_parse_title_build_prefix() -> None:
    title = "build(deps): bump softprops/action-gh-release from 2.3.3 to 3.0.0"
    assert parse_title(title) == ("softprops/action-gh-release", "2.3.3", "3.0.0")


def test_parse_title_no_match() -> None:
    assert parse_title("Random PR title") is None


def test_classify_bump_major() -> None:
    assert classify_bump("2.3.3", "3.0.0") == "major"


def test_classify_bump_minor() -> None:
    assert classify_bump("6.33.0", "6.42.0") == "minor"


def test_classify_bump_patch() -> None:
    assert classify_bump("2.4.12", "2.4.13") == "patch"


def test_classify_bump_v_prefix() -> None:
    assert classify_bump("v1.2.3", "v1.3.0") == "minor"


def test_classify_bump_two_segments() -> None:
    # Treat "1.2" as "1.2.0".
    assert classify_bump("1.2", "1.2") == "patch"
    assert classify_bump("1.2", "1.3") == "minor"


def test_classify_bump_unknown_for_non_numeric() -> None:
    assert classify_bump("abc", "def") == "unknown"


def test_aggregate_ci_empty() -> None:
    assert aggregate_ci([]) == "PENDING"


def test_aggregate_ci_all_success() -> None:
    checks = [{"conclusion": "SUCCESS"}, {"conclusion": "SUCCESS"}]
    assert aggregate_ci(checks) == "SUCCESS"


def test_aggregate_ci_any_failure() -> None:
    checks = [{"conclusion": "SUCCESS"}, {"conclusion": "FAILURE"}]
    assert aggregate_ci(checks) == "FAILURE"


def test_aggregate_ci_pending_mix() -> None:
    checks = [{"conclusion": "SUCCESS"}, {"status": "IN_PROGRESS"}]
    assert aggregate_ci(checks) == "PENDING"


def test_aggregate_ci_handles_falsy_status() -> None:
    # A check with neither conclusion nor status is treated as pending-equivalent.
    checks = [{"conclusion": "SUCCESS"}, {}]
    assert aggregate_ci(checks) == "PENDING"


def test_build_pr_full() -> None:
    raw = {
        "number": 7,
        "title": "chore(deps): bump foo from 1.0.0 to 1.0.1",
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
    }
    pr = build_pr("lsimons/x", raw)
    assert pr == DepPR(
        repo="lsimons/x",
        number=7,
        title="chore(deps): bump foo from 1.0.0 to 1.0.1",
        dep="foo",
        old="1.0.0",
        new="1.0.1",
        bump="patch",
        ci="SUCCESS",
    )


def test_build_pr_unparseable_title() -> None:
    raw: dict[str, object] = {
        "number": 9,
        "title": "Manual maintenance PR",
        "statusCheckRollup": [],
    }
    pr = build_pr("lsimons/x", raw)
    assert pr.dep == "?"
    assert pr.bump == "unknown"
    assert pr.ci == "PENDING"


def test_render_lines_empty() -> None:
    assert render_lines([]) == ["No open Dependabot PRs."]


def test_render_lines_basic() -> None:
    prs = [
        DepPR("lsimons/a", 1, "t", "biome", "2.4.12", "2.4.13", "patch", "SUCCESS"),
        DepPR(
            "lsimons/b",
            2,
            "t",
            "softprops/action-gh-release",
            "2.3.3",
            "3.0.0",
            "major",
            "SUCCESS",
        ),
    ]
    lines = render_lines(prs)
    assert any("PATCH" in line and "biome" in line for line in lines)
    assert any("MAJOR" in line and "action-gh-release" in line for line in lines)
