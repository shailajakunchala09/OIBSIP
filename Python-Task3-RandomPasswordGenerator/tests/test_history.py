"""Unit tests for history.py - verifies session-only, non-persistent history."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from history import SessionHistory


class TestSessionHistory(unittest.TestCase):
    def test_history_keeps_at_most_max_entries(self):
        history = SessionHistory(max_entries=5)
        for i in range(10):
            history.add(f"Password{i}!", "Strong")
        self.assertEqual(len(history), 5)

    def test_most_recent_entry_is_first(self):
        history = SessionHistory(max_entries=5)
        history.add("First!!", "Medium")
        history.add("Second!!", "Strong")
        self.assertEqual(history.entries[0].password, "Second!!")

    def test_remove_single_entry(self):
        history = SessionHistory(max_entries=5)
        history.add("Alpha123!", "Strong")
        entry_to_remove = history.entries[0]
        history.add("Beta123!", "Strong")
        history.remove(entry_to_remove)
        remaining = [e.password for e in history.entries]
        self.assertNotIn("Alpha123!", remaining)
        self.assertIn("Beta123!", remaining)

    def test_clear_empties_history(self):
        history = SessionHistory(max_entries=5)
        history.add("Gamma123!", "Strong")
        history.clear()
        self.assertEqual(len(history), 0)

    def test_masked_output_never_reveals_password(self):
        history = SessionHistory(max_entries=5)
        history.add("SuperSecret123!", "Strong")
        masked = history.entries[0].masked()
        self.assertNotIn("SuperSecret123!", masked)
        self.assertTrue(all(ch == "•" for ch in masked))

    def test_no_files_created_by_history_module(self):
        """History must be in-memory only: verify no files/dirs appear on disk."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        before = set()
        for root, _dirs, files in os.walk(project_root):
            if "__pycache__" in root:
                continue
            for f in files:
                before.add(os.path.join(root, f))

        history = SessionHistory(max_entries=5)
        for i in range(10):
            history.add(f"DiskCheckPass{i}!", "Strong")
        history.clear()

        after = set()
        for root, _dirs, files in os.walk(project_root):
            if "__pycache__" in root:
                continue
            for f in files:
                after.add(os.path.join(root, f))

        self.assertEqual(before, after, "History module must not write any files to disk.")


if __name__ == "__main__":
    unittest.main()
