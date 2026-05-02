"""Tests for lsimons_auto.actions.brain module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lsimons_auto.actions.brain import (
    cmd_ingest,
    find_brain_repos,
    main,
)


def _make_repo(parent: Path, name: str) -> Path:
    repo = parent / name
    repo.mkdir(parents=True)
    (repo / ".git").mkdir()
    return repo


class TestFindBrainRepos:
    """Test repo discovery."""

    def test_returns_empty_when_parent_missing(self, tmp_path: Path) -> None:
        assert find_brain_repos(tmp_path / "missing") == []

    def test_finds_brain_and_brain_star(self, tmp_path: Path) -> None:
        main_repo = _make_repo(tmp_path, "lsimons-brain")
        personal = _make_repo(tmp_path, "lsimons-brain-personal")
        data = _make_repo(tmp_path, "lsimons-brain-data")
        # Should not be picked up:
        _make_repo(tmp_path, "lsimons-other")
        (tmp_path / "lsimons-brain-not-a-repo").mkdir()  # no .git

        repos = find_brain_repos(tmp_path)

        assert main_repo in repos
        assert personal in repos
        assert data in repos
        assert len(repos) == 3

    def test_skips_dirs_without_git(self, tmp_path: Path) -> None:
        (tmp_path / "lsimons-brain").mkdir()  # no .git subdir
        assert find_brain_repos(tmp_path) == []


class TestCmdIngest:
    """Test the ingest subcommand."""

    def test_errors_when_no_repos(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_PARENT", tmp_path)
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_MAIN_DIR", tmp_path / "lsimons-brain")

        rc = cmd_ingest(dry_run=False)

        assert rc == 1
        assert "no brain repos" in capsys.readouterr().err

    def test_dry_run_does_not_run_subprocess(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _make_repo(tmp_path, "lsimons-brain")
        _make_repo(tmp_path, "lsimons-brain-personal")
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_PARENT", tmp_path)
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_MAIN_DIR", tmp_path / "lsimons-brain")

        with patch("lsimons_auto.actions.brain.subprocess.run") as mock_run:
            rc = cmd_ingest(dry_run=True)

        assert rc == 0
        assert not mock_run.called
        out = capsys.readouterr().out
        assert "Would run: git pull" in out
        assert "Would run: mise run ingest" in out

    def test_pulls_each_repo_then_runs_mise(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        main_repo = _make_repo(tmp_path, "lsimons-brain")
        personal = _make_repo(tmp_path, "lsimons-brain-personal")
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_PARENT", tmp_path)
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_MAIN_DIR", main_repo)

        with patch("lsimons_auto.actions.brain.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            rc = cmd_ingest(dry_run=False)

        assert rc == 0
        # 2 git pulls + 1 mise run = 3 calls
        assert mock_run.call_count == 3
        calls = mock_run.call_args_list
        assert calls[0].args[0] == ["git", "pull"]
        assert calls[0].kwargs["cwd"] in (main_repo, personal)
        assert calls[1].args[0] == ["git", "pull"]
        assert calls[2].args[0] == ["mise", "run", "ingest"]
        assert calls[2].kwargs["cwd"] == main_repo

    def test_pull_failure_aborts_before_mise(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _make_repo(tmp_path, "lsimons-brain")
        _make_repo(tmp_path, "lsimons-brain-personal")
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_PARENT", tmp_path)
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_MAIN_DIR", tmp_path / "lsimons-brain")

        results: list[subprocess.CompletedProcess[str]] = [
            subprocess.CompletedProcess(args=[], returncode=1),
            subprocess.CompletedProcess(args=[], returncode=0),
        ]
        with patch("lsimons_auto.actions.brain.subprocess.run", side_effect=results) as mock_run:
            rc = cmd_ingest(dry_run=False)

        assert rc == 1
        # Both pulls attempted, mise NOT called
        assert mock_run.call_count == 2
        assert "git pull failed" in capsys.readouterr().err

    def test_mise_failure_propagates(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        main_repo = _make_repo(tmp_path, "lsimons-brain")
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_PARENT", tmp_path)
        monkeypatch.setattr("lsimons_auto.actions.brain.BRAIN_MAIN_DIR", main_repo)

        results: list[subprocess.CompletedProcess[str]] = [
            subprocess.CompletedProcess(args=[], returncode=0),  # git pull
            subprocess.CompletedProcess(args=[], returncode=2),  # mise run
        ]
        with patch("lsimons_auto.actions.brain.subprocess.run", side_effect=results):
            rc = cmd_ingest(dry_run=False)

        assert rc == 1


class TestBrainCLI:
    """Test the main() CLI entry point."""

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "ingest" in out

    def test_ingest_help_mentions_full_brain_run(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["ingest", "--help"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out.lower()
        assert "full local lsimons brain ingest run" in out

    def test_no_subcommand_prints_help_and_exits_nonzero(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "ingest" in out

    def test_ingest_dispatches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        called = MagicMock(return_value=0)
        monkeypatch.setattr("lsimons_auto.actions.brain.cmd_ingest", called)

        with pytest.raises(SystemExit) as exc_info:
            main(["ingest", "--dry-run"])

        assert exc_info.value.code == 0
        called.assert_called_once_with(dry_run=True)
