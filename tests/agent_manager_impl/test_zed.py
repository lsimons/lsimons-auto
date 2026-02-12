"""
Tests for zed.py module (Zed editor integration).
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# pyright: ignore[reportUnknownParameterType, reportMissingParameterType, reportUnknownMemberType, reportUnknownVariableType, reportUnusedExpression]

from lsimons_auto.actions.agent_manager_impl.zed import (
    launch_zed_with_terminal,
    position_windows_fill_screen,
)


class TestLaunchZedWithTerminal:
    """Tests for launch_zed_with_terminal function."""

    @patch("lsimons_auto.actions.agent_manager_impl.zed.subprocess.Popen")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.time.sleep")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.keystroke")
    def test_launch_zed_with_terminal_basic(
        self, mock_keystroke, mock_sleep, mock_popen
    ):
        """Test basic Zed launch with terminal panel."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        workspace_path = Path("/path/to/workspace")
        launch_zed_with_terminal(workspace_path)

        # Verify zed command was launched
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["zed", str(workspace_path)]

        # Verify sleep was called
        mock_sleep.assert_called_once_with(1.5)

        # Verify keystroke was sent to open terminal
        mock_keystroke.assert_called_once()
        keystroke_call = mock_keystroke.call_args
        keystroke_call[0] == ("Zed", "j", ["command"])

    @patch("lsimons_auto.actions.agent_manager_impl.zed.subprocess.Popen")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.time.sleep")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.keystroke")
    def test_launch_zed_with_different_workspace(
        self, mock_keystroke, mock_sleep, mock_popen
    ):
        """Test Zed launch with different workspace path."""
        mock_process = Mock()
        mock_process.pid = 54321
        mock_popen.return_value = mock_process

        workspace_path = Path("/another/workspace")
        launch_zed_with_terminal(workspace_path)

        mock_popen.assert_called_once()
        assert mock_popen.call_args[0][0][1] == str(workspace_path)

    @patch("lsimons_auto.actions.agent_manager_impl.zed.subprocess.Popen")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.time.sleep")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.keystroke")
    def test_launch_zed_handles_popen_exception(
        self, mock_keystroke, mock_sleep, mock_popen
    ):
        """Test that Popen exceptions are propagated."""
        mock_popen.side_effect = FileNotFoundError("zed not found")

        workspace_path = Path("/path/to/workspace")
        with pytest.raises(FileNotFoundError):
            launch_zed_with_terminal(workspace_path)

        # sleep should not be called if Popen fails
        mock_sleep.assert_not_called()

    @patch("lsimons_auto.actions.agent_manager_impl.zed.subprocess.Popen")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.time.sleep")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.keystroke")
    def test_launch_zed_keystroke_exception(
        self, mock_keystroke, mock_sleep, mock_popen
    ):
        """Test that keystroke exceptions are propagated."""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        mock_keystroke.side_effect = RuntimeError("AppleScript failed")

        workspace_path = Path("/path/to/workspace")
        with pytest.raises(RuntimeError):
            launch_zed_with_terminal(workspace_path)

        # Popen and sleep should still be called
        mock_popen.assert_called_once()
        mock_sleep.assert_called_once()


class TestPositionWindowsFillScreen:
    """Tests for position_windows_fill_screen function."""

    @patch(
        "lsimons_auto.actions.agent_manager_impl.zed.run_applescript"
    )
    def test_position_windows_creates_applescript(
        self, mock_run_applescript
    ):
        """Test that position windows creates and runs AppleScript."""
        position_windows_fill_screen()

        # Verify run_applescript was called
        mock_run_applescript.assert_called_once()
        script_arg = mock_run_applescript.call_args[0][0]

        # Verify the script contains expected content
        assert "Ghostty" in script_arg
        assert "Zed" in script_arg
        assert "set position" in script_arg
        assert "set size" in script_arg

    @patch(
        "lsimons_auto.actions.agent_manager_impl.zed.run_applescript"
    )
    def test_position_windows_script_structure(
        self, mock_run_applescript
    ):
        """Test that the AppleScript has proper structure."""
        position_windows_fill_screen()

        script = mock_run_applescript.call_args[0][0]

        # Should have Finder bounds section
        assert "tell application \"Finder\"" in script
        assert "screenBounds" in script

        # Should have Ghostty positioning
        assert "tell process \"Ghostty\"" in script

        # Should have Zed positioning
        assert "tell process \"Zed\"" in script

    @patch(
        "lsimons_auto.actions.agent_manager_impl.zed.run_applescript"
    )
    def test_position_windows_handles_exception(
        self, mock_run_applescript
    ):
        """Test that exceptions from run_applescript are propagated."""
        mock_run_applescript.side_effect = RuntimeError(
            "AppleScript execution failed"
        )

        with pytest.raises(RuntimeError):
            position_windows_fill_screen()

    @patch(
        "lsimons_auto.actions.agent_manager_impl.zed.run_applescript"
    )
    def test_position_windows_with_applescript_error(
        self, mock_run_applescript
    ):
        """Test handling of AppleScript runtime errors."""
        mock_run_applescript.side_effect = Exception(
            "Application not running"
        )

        with pytest.raises(Exception):
            position_windows_fill_screen()

    @patch(
        "lsimons_auto.actions.agent_manager_impl.zed.run_applescript"
    )
    def test_position_windows_position_values(
        self, mock_run_applescript
    ):
        """Test that window position values are set correctly."""
        position_windows_fill_screen()

        script = mock_run_applescript.call_args[0][0]

        # Windows should be positioned at x=0
        assert "set position of frontWindow to {0, 25}" in script

    @patch(
        "lsimons_auto.actions.agent_manager_impl.zed.run_applescript"
    )
    def test_position_windows_size_values(
        self, mock_run_applescript
    ):
        """Test that window size values reference screen dimensions."""
        position_windows_fill_screen()

        script = mock_run_applescript.call_args[0][0]

        # Size should reference screen width and height
        assert "screenWidth" in script
        assert "screenHeight" in script
        assert "screenHeight - 25" in script


class TestModuleIntegration:
    """Integration tests for zed module."""

    @patch("lsimons_auto.actions.agent_manager_impl.zed.subprocess.Popen")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.time.sleep")
    @patch("lsimons_auto.actions.agent_manager_impl.zed.keystroke")
    @patch(
        "lsimons_auto.actions.agent_manager_impl.zed.run_applescript"
    )
    def test_full_workflow(
        self,
        mock_run_applescript,
        mock_keystroke,
        mock_sleep,
        mock_popen,
    ):
        """Test complete workflow of launching and positioning Zed."""
        mock_process = Mock()
        mock_popen.return_value = mock_process

        workspace_path = Path("/test/workspace")

        # Launch Zed
        launch_zed_with_terminal(workspace_path)

        # Position windows
        position_windows_fill_screen()

        # Verify all steps were called
        mock_popen.assert_called_once()
        mock_sleep.assert_called_once()
        mock_keystroke.assert_called_once()
        mock_run_applescript.assert_called_once()