"""Exercise replacement flow without Windows, a display or real clipboard."""
import time
import unittest
from unittest.mock import Mock
from app import App


class ReplacementTests(unittest.TestCase):
    def setUp(self):
        self.app = App.__new__(App)
        self.app.root = Mock()
        self.app.root.winfo_id.return_value = 100
        self.app.status = Mock()
        self.app.api = Mock()
        self.app.api.foreground.return_value = 77
        self.app.api.modifiers_down.return_value = False
        self.app.api.sequence.return_value = 11
        self.app.target = 77
        self.app.before = 10
        self.app.deadline = time.monotonic() + 1
        self.app.busy = True
        self.app.mode = lambda: "auto"

    def test_replacement(self):
        self.app.api.read_clipboard.return_value = "ghbdtn"
        self.app.wait_copy()
        self.app.api.write_clipboard.assert_called_once_with(100, "привет")
        self.app.api.shortcut.assert_called_once_with("v")
        self.assertFalse(self.app.busy)

    def test_unchanged_clipboard_never_pastes_stale_text(self):
        self.app.api.sequence.return_value = 10
        self.app.deadline = time.monotonic() - 1
        self.app.wait_copy()
        self.app.api.read_clipboard.assert_not_called()
        self.app.api.shortcut.assert_not_called()
        self.assertFalse(self.app.busy)

    def test_changed_window_cancels(self):
        self.app.api.foreground.return_value = 88
        self.app.wait_copy()
        self.app.api.write_clipboard.assert_not_called()
        self.app.api.shortcut.assert_not_called()

    def test_busy_clipboard_reports_error(self):
        self.app.api.read_clipboard.side_effect = OSError("Буфер занят")
        self.app.wait_copy()
        self.app.api.shortcut.assert_not_called()
        self.assertFalse(self.app.busy)

    def test_empty_selection(self):
        self.app.api.read_clipboard.return_value = ""
        self.app.wait_copy()
        self.app.api.write_clipboard.assert_not_called()
        self.app.api.shortcut.assert_not_called()

    def test_new_modifiers_cancel_paste(self):
        self.app.api.read_clipboard.return_value = "ghbdtn"
        self.app.api.modifiers_down.return_value = True
        self.app.wait_copy()
        self.app.api.write_clipboard.assert_not_called()
        self.app.api.shortcut.assert_not_called()


if __name__ == "__main__":
    unittest.main()
