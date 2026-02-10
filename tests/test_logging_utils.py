#!/usr/bin/env python3
"""
Tests for the logging_utils module.
"""

import logging
import tempfile
import unittest
from pathlib import Path

from lsimons_auto.logging_utils import get_logger, setup_logging


class TestLoggingUtils(unittest.TestCase):
    """Test cases for logging utilities."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Clear any existing loggers to start fresh
        logging.getLogger().handlers.clear()

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Clear loggers after each test
        logging.getLogger().handlers.clear()

    def test_get_logger(self) -> None:
        """Test that get_logger returns a properly configured logger."""
        logger = get_logger("test_logger")

        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.INFO)
        self.assertGreater(len(logger.handlers), 0)

    def test_setup_logging_basic(self) -> None:
        """Test basic logging setup."""
        logger = setup_logging("test_basic")

        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test_basic")
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 1)

    def test_setup_logging_with_file(self) -> None:
        """Test logging setup with file output."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as temp_file:
            temp_path = temp_file.name

        try:
            logger = setup_logging("test_file", log_file=temp_path)

            self.assertIsNotNone(logger)
            self.assertEqual(len(logger.handlers), 2)  # console + file

            # Test that logging to file works
            logger.info("Test message")

            # Check that file was created and contains the message
            log_path = Path(temp_path)
            self.assertTrue(log_path.exists())

            with open(temp_path) as f:
                content = f.read()
                self.assertIn("Test message", content)

        finally:
            # Clean up
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_setup_logging_duplicate_handlers(self) -> None:
        """Test that duplicate handlers are prevented."""
        logger1 = setup_logging("test_duplicate")
        handler_count_1 = len(logger1.handlers)

        # Call setup_logging again with same logger name
        logger2 = setup_logging("test_duplicate")
        handler_count_2 = len(logger2.handlers)

        # Should have same number of handlers (no duplicates)
        self.assertEqual(handler_count_1, handler_count_2)
        self.assertEqual(handler_count_1, 1)

    def test_setup_logging_different_levels(self) -> None:
        """Test logging setup with different levels."""
        debug_logger = setup_logging("test_debug", level=logging.DEBUG)
        warning_logger = setup_logging("test_warning", level=logging.WARNING)

        self.assertEqual(debug_logger.level, logging.DEBUG)
        self.assertEqual(warning_logger.level, logging.WARNING)

    def test_logger_reuse(self) -> None:
        """Test that get_logger reuses existing loggers."""
        logger1 = get_logger("test_reuse")
        logger2 = get_logger("test_reuse")

        self.assertIs(logger1, logger2)
        self.assertEqual(len(logger1.handlers), len(logger2.handlers))


if __name__ == "__main__":
    unittest.main()
