import sys
import unittest
from unittest.mock import patch, MagicMock
from lsimons_auto.actions.gdrive_sync import main

class TestGdriveSync(unittest.TestCase):
    
    @patch('socket.gethostname')
    def test_wrong_hostname(self, mock_hostname):
        mock_hostname.return_value = "wrong-host"
        with patch('builtins.print') as mock_print:
            main([])
            mock_print.assert_any_call("Skipping: Hostname is 'wrong-host', expected 'paddo'.")

    @patch('socket.gethostname')
    @patch('os.path.ismount')
    @patch('os.path.exists')
    def test_volume_not_mounted(self, mock_exists, mock_ismount, mock_hostname):
        mock_hostname.return_value = "paddo"
        mock_ismount.return_value = False
        mock_exists.return_value = False # Treat as not existing for this test case
        
        with patch('builtins.print') as mock_print:
            main([])
            mock_print.assert_any_call("Skipping: /Volumes/LSData is not available/mounted.")

    @patch('socket.gethostname')
    @patch('os.path.ismount')
    @patch('shutil.which')
    def test_rclone_missing(self, mock_which, mock_ismount, mock_hostname):
        mock_hostname.return_value = "paddo"
        mock_ismount.return_value = True
        mock_which.return_value = None
        
        with patch('builtins.print') as mock_print:
            with self.assertRaises(SystemExit) as cm:
                main([])
            self.assertEqual(cm.exception.code, 1)
            mock_print.assert_any_call("Error: rclone is not installed or not in PATH.")

    @patch('socket.gethostname')
    @patch('os.path.ismount')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_sync_success(self, mock_run, mock_which, mock_ismount, mock_hostname):
        mock_hostname.return_value = "paddo"
        mock_ismount.return_value = True
        mock_which.return_value = "/usr/bin/rclone"
        
        with patch('builtins.print') as mock_print:
            main([])
            
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[:2], ["rclone", "sync"])
            self.assertEqual(args[3], "/Volumes/LSData/Google Drive")
            
            mock_print.assert_any_call("Sync completed successfully.")

if __name__ == '__main__':
    unittest.main()
