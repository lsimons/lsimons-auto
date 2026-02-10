#!/usr/bin/env python3
"""
Tests for the echo action.
"""

import subprocess
import sys
import unittest
from pathlib import Path

from lsimons_auto.actions.echo import main


class TestEchoAction(unittest.TestCase):
    """Test cases for the echo action."""

    def test_echo_default_message(self) -> None:
        """Test echo with no arguments (default message)."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.echo"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Hello, World!")

    def test_echo_custom_message(self) -> None:
        """Test echo with custom message."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.echo", "Hello", "Test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Hello Test")

    def test_echo_uppercase(self) -> None:
        """Test echo with uppercase conversion."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.echo", "--upper", "hello"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "HELLO")

    def test_echo_with_prefix(self) -> None:
        """Test echo with prefix."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.echo", "--prefix", "INFO", "test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "INFO: test")

    def test_echo_combined_options(self) -> None:
        """Test echo with multiple options combined."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lsimons_auto.actions.echo",
                "--prefix",
                "WARNING",
                "--upper",
                "test",
                "message",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "WARNING: TEST MESSAGE")

    def test_echo_programmatic_usage(self) -> None:
        """Test echo action called programmatically."""
        # Test default message - echo uses print(), not logging
        import contextlib
        import io

        # Capture stdout for programmatic testing
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            main([])

        self.assertEqual(stdout_capture.getvalue().strip(), "Hello, World!")

        # Test with arguments
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            main(["test", "message"])

        self.assertEqual(stdout_capture.getvalue().strip(), "test message")

    def test_echo_help_output(self) -> None:
        """Test echo help output."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.echo", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Echo a message", result.stdout)
        self.assertIn("--upper", result.stdout)
        self.assertIn("--prefix", result.stdout)

    def test_echo_empty_message(self) -> None:
        """Test echo with empty message (should use default)."""
        result = subprocess.run(
            [sys.executable, "-m", "lsimons_auto.actions.echo"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Hello, World!")


if __name__ == "__main__":
    unittest.main()
