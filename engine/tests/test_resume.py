# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""status, resume, play, doctor: the workshop meets its owner honestly."""
import os
import tempfile
import unittest

from engine import desk, journal, notes, project, provisional, status

from . import elsewhere_home, no_terminal, pressing


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
        self.assertTrue(out.startswith("two things need you."), out)
        self.assertIn("1 draft(s) · \"a finding\"", out)
        self.assertIn("1 provisional act(s) waiting", out)
        # the sentence opens the page; the table follows it, never precedes it
        self.assertLess(out.index("two things need you."),
                        out.index("project(s)"))

    def test_resume_headless_refuses_with_its_own_name_and_exits_one(self):
        """the scar: resume printed a refusal and returned 0 on it."""
        notes.note(self.ws, "a finding", target_project="geardoor")
        said = []
        with no_terminal():
            rc = status.resume(self.ws, out=said.append)
        self.assertEqual(rc, 1)
        self.assertEqual(said, ["landing needs your 'k' at a real terminal — run: sandbox resume"])
        self.assertEqual(len(desk.drafts(self.ws)[0]), 1)

    def test_resume_opens_with_the_needs_sentence(self):
        """one producer, three renderers: resume says what status says."""
        notes.note(self.ws, "a finding", target_project="geardoor")
        said = []
        with pressing("x"):
            status.resume(self.ws, out=said.append)
        self.assertEqual(said[0], "one thing needs you.")
        self.assertIn("1 draft(s) · \"a finding\"", said[1])
        self.assertIn("sandbox approve", said[1])

    def test_resume_with_key_lands_and_confirms_under_one_hash(self):
        notes.note(self.ws, "a finding", target_project="geardoor")
        f = os.path.join(project.dirpath(self.ws, "geardoor"), "x.md")
        with open(f, "w") as fh:
            fh.write("a\n")
        provisional.act(self.ws, f, "b\n", "clean act", "geardoor")
        said = []
        with pressing("k"):
            rc = status.resume(self.ws, out=said.append)
        self.assertEqual(rc, 0)
        block = [l for l in said if l[:4] in (" 1. ", " 2. ")]
        self.assertEqual(block, [" 1. [note] a finding",
                                 " 2. [provisional] clean act"])
        at = [n for n, l in enumerate(said) if l.startswith("shown: ")][0]
        digest = said[at].split("shown: ")[1]
        self.assertEqual(said[at + 1],
                         "press k to land these 2 · any other key cancels")
        self.assertEqual(said[-1], "landed 2 (shown %s)" % digest)
        self.assertEqual(provisional.pending(self.ws), [])
        events, _ = journal.read(self.ws)
        rode = [e for e in events if str(e.get("shown", "")).startswith(digest)]
        self.assertEqual(len(rode), 2)

    def test_resume_cancels_on_any_other_key(self):
        notes.note(self.ws, "a finding", target_project="geardoor")
        said = []
        with pressing("x"):
            rc = status.resume(self.ws, out=said.append)
        self.assertEqual(rc, 0)
        self.assertEqual(said[-1], "cancelled — nothing landed")
        self.assertEqual(len(desk.drafts(self.ws)[0]), 1)

    def test_resume_never_auto_resolves_moved_on(self):
        f = os.path.join(project.dirpath(self.ws, "geardoor"), "x.md")
        with open(f, "w") as fh:
            fh.write("a\n")
        provisional.act(self.ws, f, "b\n", "then it moved", "geardoor")
        with open(f, "a") as fh:
            fh.write("later work\n")
        said = []
        with pressing("k"):
            status.resume(self.ws, out=said.append)
        self.assertIn("needs your hand", "\n".join(said))
        self.assertEqual(len(provisional.pending(self.ws)), 1)
        with open(f) as fh:
            self.assertIn("later work", fh.read())


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

    def test_the_charter_of_the_free_room_says_what_it_is(self):
        """item X10, row 10: the room names itself and says what does not happen
        here; the three un-words and "room" were the engine's own nouns."""
        import os
        status.play(self.ws)
        p = os.path.join(self.ws, status.PLAYGROUND, "CHARTER.md")
        with open(p, encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text, "# the playground\n\nnothing in here is "
                               "counted, cited, or shipped. try things.\n")
        self.assertLessEqual(len(text.split()), 20)

    def test_doctor_green_on_a_fresh_workshop(self):
        from engine import onboard
        ws = tempfile.mkdtemp(prefix="sbx8-")
        onboard.run(ws)
        with elsewhere_home():
            ok, lines = status.doctor(ws)
        self.assertTrue(ok, "\n".join(lines))

    def test_doctor_names_a_workshop_the_core_never_met(self):
        ok, lines = status.doctor(self.ws)  # genesis without init
        self.assertFalse(ok)
        self.assertTrue(any("never met this core" in l for l in lines))

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
