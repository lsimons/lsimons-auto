"""
Tests for echo action.
"""

import subprocess
import sys


def test_echo_default_message():
    """Test echo with default message."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "Hello, World!"


def test_echo_custom_message():
    """Test echo with custom message."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py", "Hello", "from", "test"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "Hello from test"


def test_echo_uppercase():
    """Test echo with --upper flag."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py", "hello", "--upper"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "HELLO"


def test_echo_prefix():
    """Test echo with --prefix flag."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py", "test", "--prefix", "LOG"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "LOG: test"


def test_echo_uppercase_with_prefix():
    """Test echo with both --upper and --prefix flags."""
    result = subprocess.run(
        [
            sys.executable,
            "lsimons_auto/actions/echo.py",
            "test",
            "--upper",
            "--prefix",
            "LOG",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "LOG: TEST"


def test_echo_uppercase_does_not_apply_to_prefix():
    """Test that --upper does not apply to the prefix."""
    result = subprocess.run(
        [
            sys.executable,
            "lsimons_auto/actions/echo.py",
            "test",
            "--upper",
            "--prefix",
            "log",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    # The prefix is added after uppercase conversion, so it's not uppercased
    assert result.stdout.strip() == "log: TEST"


def test_echo_help():
    """Test echo help output."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "echo a message" in result.stdout.lower()


def test_echo_module_import():
    """Test that echo module can be imported."""
    from lsimons_auto.actions.echo import main

    # Should not raise
    assert callable(main)


def test_echo_main_function_with_args():
    """Test echo main function with arguments."""
    from lsimons_auto.actions.echo import main
    import io
    from contextlib import redirect_stdout

    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        main(["custom", "message"])

    assert f.getvalue().strip() == "custom message"


def test_echo_main_function_none_args():
    """Test echo main function with None args (uses sys.argv)."""
    from lsimons_auto.actions.echo import main

    # Should use sys.argv when args is None
    # We can't easily test this without modifying sys.argv
    # Just verify it doesn't crash
    main([])


def test_echo_main_function_with_none():
    """Test echo main function with None (default behavior)."""
    from lsimons_auto.actions.echo import main
    import io
    from contextlib import redirect_stdout
    import sys
    from unittest.mock import patch

    # Mock sys.argv
    with patch.object(sys, "argv", ["echo.py", "test"]):
        f = io.StringIO()
        with redirect_stdout(f):
            main(None)

        assert "test" in f.getvalue()


def test_echo_empty_message():
    """Test echo with empty message list."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "Hello, World!"


def test_echo_multiple_words():
    """Test echo with multiple words."""
    result = subprocess.run(
        [
            sys.executable,
            "lsimons_auto/actions/echo.py",
            "one",
            "two",
            "three",
            "four",
            "five",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "one two three four five"


def test_echo_special_characters():
    """Test echo with special characters."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py", "hello@world.com"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "hello@world.com"


def test_echo_unicode():
    """Test echo with unicode characters."""
    result = subprocess.run(
        [sys.executable, "lsimons_auto/actions/echo.py", "hello", "🌍", "world"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "🌍" in result.stdout