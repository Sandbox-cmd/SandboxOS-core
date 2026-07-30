# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""status, resume, play, doctor: the workshop meets its owner honestly."""
import os
import tempfile
import unittest

from engine import journal, notes, project, provisional, status


class TestStatusResume(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor", "the store's data")

    def test_status_quiet_page(self):
        out = status.status(self.ws)
        self.assertIn("nothing needs you.", out)

    def test_status_names_what_waits(self):
        notes.note(self.ws, "a finding", target_project="geardoor")
        f = os.path.join(project.dirpath(self.ws, "geardoor"), "x.md")
        open(f, "w").write("a\n")
        provisional.act(self.ws, f, "b\n", "why", "geardoor")
        out = status.status(self.ws)
        self.assertIn("1 draft(s) waiting", out)
        self.assertIn("1 provisional act(s)", out)

    def test_resume_headless_shows_but_touches_nothing(self):
        notes.note(self.ws, "a finding", target_project="geardoor")
        text, n = status.resume(self.ws, is_real_tty=False, keychar=None)
        self.assertEqual(n, 0)
        self.assertIn("real terminal", text)

    def test_resume_with_key_lands_and_confirms(self):
        notes.note(self.ws, "a finding", target_project="geardoor")
        f = os.path.join(project.dirpath(self.ws, "geardoor"), "x.md")
        open(f, "w").write("a\n")
        provisional.act(self.ws, f, "b\n", "clean act", "geardoor")
        text, n = status.resume(self.ws, is_real_tty=True, keychar="k")
        self.assertEqual(n, 2)
        self.assertEqual(provisional.pending(self.ws), [])

    def test_resume_never_auto_resolves_moved_on(self):
        f = os.path.join(project.dirpath(self.ws, "geardoor"), "x.md")
        open(f, "w").write("a\n")
        provisional.act(self.ws, f, "b\n", "then it moved", "geardoor")
        open(f, "a").write("later work\n")
        text, n = status.resume(self.ws, is_real_tty=True, keychar="k")
        self.assertIn("needs your hand", text)
        self.assertEqual(len(provisional.pending(self.ws)), 1)
        self.assertIn("later work", open(f).read())


class TestPlayDoctor(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def test_play_opens_the_free_room_off_the_record(self):
        before, _ = journal.read(self.ws)
        msg = status.play(self.ws)
        after, _ = journal.read(self.ws)
        self.assertIn("playground", msg)
        self.assertEqual(len(before), len(after))  # uncounted, by construction

    def test_doctor_green_on_a_fresh_workshop(self):
        ok, lines = status.doctor(self.ws)
        self.assertTrue(ok, "\n".join(lines))

    def test_doctor_names_a_torn_record(self):
        with open(journal.path(self.ws), "a") as f:
            f.write('{"op": "assert", "torn')
        ok, lines = status.doctor(self.ws)
        self.assertFalse(ok)
        self.assertTrue(any("torn" in l for l in lines))

    def test_doctor_flags_a_missing_workshop(self):
        empty = tempfile.mkdtemp(prefix="sbx8e-")
        ok, lines = status.doctor(empty)
        self.assertFalse(ok)
        self.assertTrue(any("sandbox init" in l for l in lines))


if __name__ == "__main__":
    unittest.main()
