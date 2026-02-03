"""Tests for the tc (Technology Council) action."""

import os
import tempfile
import unittest
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from lsimons_auto.actions import tc


class TestDateFunctions(unittest.TestCase):
    """Tests for date utility functions."""

    def test_get_next_monday_on_monday(self) -> None:
        """If today is Monday, return today."""
        monday = date(2025, 1, 6)  # Known Monday
        result = tc.get_next_monday(monday)
        self.assertEqual(result, monday)

    def test_get_next_monday_on_tuesday(self) -> None:
        """If today is Tuesday, return next Monday."""
        tuesday = date(2025, 1, 7)
        result = tc.get_next_monday(tuesday)
        self.assertEqual(result, date(2025, 1, 13))

    def test_get_next_monday_on_sunday(self) -> None:
        """If today is Sunday, return next Monday."""
        sunday = date(2025, 1, 5)
        result = tc.get_next_monday(sunday)
        self.assertEqual(result, date(2025, 1, 6))

    def test_get_previous_monday(self) -> None:
        """Get Monday before a given Monday."""
        monday = date(2025, 1, 13)
        result = tc.get_previous_monday(monday)
        self.assertEqual(result, date(2025, 1, 6))

    def test_format_date_yyyymmdd(self) -> None:
        """Format date as YYYYMMDD string."""
        d = date(2025, 1, 6)
        result = tc.format_date_yyyymmdd(d)
        self.assertEqual(result, "20250106")

    def test_mondays_of_year(self) -> None:
        """Generate all Mondays of a year."""
        mondays = list(tc.mondays_of_year(2025))
        self.assertEqual(mondays[0], date(2025, 1, 6))  # First Monday of 2025
        self.assertEqual(len(mondays), 52)
        for m in mondays:
            self.assertEqual(m.weekday(), 0)  # All are Mondays
            self.assertEqual(m.year, 2025)


class TestGetBaseDir(unittest.TestCase):
    """Tests for base directory resolution."""

    def test_args_takes_precedence(self) -> None:
        """Argument should override env and default."""
        with patch.dict(os.environ, {"TC_BASE_DIR": "/env/path"}):
            result = tc.get_base_dir("/arg/path")
            self.assertEqual(result, Path("/arg/path"))

    def test_env_used_when_no_args(self) -> None:
        """Environment variable used when no argument provided."""
        with patch.dict(os.environ, {"TC_BASE_DIR": "/env/path"}, clear=False):
            result = tc.get_base_dir(None)
            self.assertEqual(result, Path("/env/path"))

    def test_default_when_nothing_set(self) -> None:
        """Default path used when nothing else specified."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove TC_BASE_DIR if present
            os.environ.pop("TC_BASE_DIR", None)
            result = tc.get_base_dir(None)
            self.assertIn("Technology Council", str(result))


class TestFindDocxFile(unittest.TestCase):
    """Tests for finding .docx files."""

    def test_find_existing_docx(self) -> None:
        """Find existing .docx file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            docx_file = tmppath / "20250106 Minutes Technology Council.docx"
            docx_file.touch()

            result = tc.find_docx_file(tmppath, "20250106")
            self.assertEqual(result, docx_file)

    def test_return_none_for_missing(self) -> None:
        """Return None when .docx doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tc.find_docx_file(Path(tmpdir), "20250106")
            self.assertIsNone(result)


class TestFindDocxWithoutPdf(unittest.TestCase):
    """Tests for finding .docx files without corresponding PDFs."""

    def test_find_docx_needing_pdf(self) -> None:
        """Find .docx files that don't have corresponding PDFs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            subdir = tmppath / "20250106"
            subdir.mkdir()
            docx_file = subdir / "20250106 Minutes Technology Council.docx"
            docx_file.touch()

            result = tc.find_docx_without_pdf(tmppath)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][1], docx_file)

    def test_skip_docx_with_pdf(self) -> None:
        """Skip .docx files that already have PDFs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            subdir = tmppath / "20250106"
            subdir.mkdir()
            docx_file = subdir / "20250106 Minutes Technology Council.docx"
            docx_file.touch()
            pdf_file = subdir / "20250106 Minutes Technology Council.pdf"
            pdf_file.touch()

            result = tc.find_docx_without_pdf(tmppath)
            self.assertEqual(len(result), 0)


class TestCreateDirs(unittest.TestCase):
    """Tests for create-dirs subcommand."""

    def test_create_dirs_dry_run(self) -> None:
        """Dry run should not create directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            next_year = date.today().year + 1

            captured = StringIO()
            with patch("sys.stdout", captured):
                result = tc.create_dirs(tmppath, dry_run=True)

            self.assertEqual(result, 0)
            year_dir = tmppath / str(next_year)
            self.assertFalse(year_dir.exists())
            self.assertIn("Would create", captured.getvalue())

    def test_create_dirs_creates_year_directory(self) -> None:
        """Should create year directory and Monday subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            next_year = date.today().year + 1

            result = tc.create_dirs(tmppath, dry_run=False)

            self.assertEqual(result, 0)
            year_dir = tmppath / str(next_year)
            self.assertTrue(year_dir.exists())
            subdirs = list(year_dir.iterdir())
            self.assertGreater(len(subdirs), 50)  # ~52 Mondays

    def test_create_dirs_skips_existing(self) -> None:
        """Should skip directories that already exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            next_year = date.today().year + 1
            year_dir = tmppath / str(next_year)
            year_dir.mkdir()
            first_monday = list(tc.mondays_of_year(next_year))[0]
            existing_dir = year_dir / first_monday.strftime("%Y%m%d")
            existing_dir.mkdir()

            captured = StringIO()
            with patch("sys.stdout", captured):
                result = tc.create_dirs(tmppath, dry_run=False)

            self.assertEqual(result, 0)
            self.assertIn("Skipping", captured.getvalue())


class TestCLI(unittest.TestCase):
    """Tests for command-line interface."""

    def test_no_command_shows_help(self) -> None:
        """No command should print help."""
        captured = StringIO()
        with patch("sys.stdout", captured):
            tc.main([])
        self.assertIn("usage:", captured.getvalue().lower())

    def test_help_flag(self) -> None:
        """--help should work."""
        with self.assertRaises(SystemExit) as cm:
            tc.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_invalid_base_dir_exits(self) -> None:
        """Invalid base directory should exit with error."""
        with self.assertRaises(SystemExit) as cm:
            tc.main(["--base-dir", "/nonexistent/path", "create-dirs"])
        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
