# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The pen and the keystroke: staging, landing, canon, recall, and why."""
import os
import tempfile
import unittest

from engine import journal, notes, project


class TestNotes(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")

    def test_machine_note_stages_then_approve_lands_and_canon_fills(self):
        disp, _ = notes.note(self.ws, "the tax rule is 5%", target_project="geardoor")
        self.assertEqual(disp, "staged")
        n, _ = notes.approve(self.ws, is_real_tty=True, keychar="k")
        self.assertEqual(n, 1)
        canon = open(os.path.join(project.dirpath(self.ws, "geardoor"), "CANON.md")).read()
        self.assertIn("the tax rule is 5%", canon)
        self.assertIn("computed, not stored", canon)

    def test_approve_headless_lands_nothing(self):
        notes.note(self.ws, "x", target_project="geardoor")
        n, msg = notes.approve(self.ws, is_real_tty=False, keychar="k")
        self.assertEqual(n, 0)

    def test_canon_is_disposable_and_rebuilds(self):
        notes.note(self.ws, "a landed fact", target_project="geardoor")
        notes.approve(self.ws, is_real_tty=True, keychar="k")
        cpath = os.path.join(project.dirpath(self.ws, "geardoor"), "CANON.md")
        os.remove(cpath)
        notes.refresh_canon(self.ws, "geardoor")
        self.assertIn("a landed fact", open(cpath).read())

    def test_recall_finds_landed_not_staged(self):
        notes.note(self.ws, "findable ruling material", target_project="geardoor")
        self.assertEqual(notes.recall(self.ws, "findable"), [])  # staged is not landed
        notes.approve(self.ws, is_real_tty=True, keychar="k")
        hits = notes.recall(self.ws, "findable")
        self.assertEqual(len(hits), 1)

    def test_why_walks_lineage_with_supersession(self):
        journal.append(self.ws, {"op": "session", "phase": "open", "key": "s1"})
        old = journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                       "body": "curses stays", "stratum": "taste"})
        journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                 "body": "textual now", "stratum": "taste",
                                 "supersedes": old["id"]})
        out = notes.why(self.ws, "textual")
        text = "\n".join(out)
        self.assertIn("textual now", text)
        self.assertIn("supersedes: curses stays", text)
        self.assertIn("during session", text)

    def test_why_on_nothing_says_so(self):
        out = notes.why(self.ws, "ghost")
        self.assertIn("nothing landed", out[0])


if __name__ == "__main__":
    unittest.main()
