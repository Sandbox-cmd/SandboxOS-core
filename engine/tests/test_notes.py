# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the pen and the keystroke: staging, the shown pile, landing, canon,
recall, and why."""
import os
import tempfile
import unittest
from unittest import mock

from engine import desk, journal, notes, project

from . import no_terminal, pressing


class TestNotes(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self.said = []

    def approve(self, **kw):
        return notes.approve(self.ws, out=self.said.append, **kw)

    def test_machine_note_stages_then_approve_lands_and_canon_fills(self):
        disp, _ = notes.note(self.ws, "the tax rule is 5%", target_project="geardoor")
        self.assertEqual(disp, "staged")
        with pressing("k"):
            rc = self.approve()
        self.assertEqual(rc, 0)
        with open(os.path.join(project.dirpath(self.ws, "geardoor"), "CANON.md")) as f:
            canon = f.read()
        self.assertIn("the tax rule is 5%", canon)
        self.assertIn("computed, not stored", canon)

    def test_a_note_typed_at_a_terminal_stages_and_says_so(self):
        """rule R3: the tty note stages like every other. START-HERE step 4 is
        true for a person at a keyboard because of this line."""
        with mock.patch("sys.stdin.isatty", return_value=True):
            disp, msg = notes.note(self.ws, "typed by a hand", target_project="geardoor")
        self.assertEqual(disp, "staged")
        self.assertEqual(msg, "waiting for your approval — approve it: sandbox approve")
        pile, _ = desk.drafts(self.ws)
        self.assertEqual([d["origin"] for d in pile], ["human"])
        events, _ = journal.read(self.ws)
        self.assertEqual([e for e in events if e.get("body") == "typed by a hand"], [])

    def test_approve_shows_the_pile_then_lands_what_it_showed(self):
        notes.note(self.ws, "one finding", target_project="geardoor")
        notes.note(self.ws, "another finding", target_project="geardoor")
        with pressing("k"):
            rc = self.approve()
        self.assertEqual(rc, 0)
        self.assertEqual(self.said[0], " 1. [note] one finding")
        self.assertEqual(self.said[1], " 2. [note] another finding")
        digest = self.said[2].split("shown: ")[1]
        self.assertEqual(self.said[3], "press k to land these 2 · any other key cancels")
        self.assertEqual(self.said[4], "landed 2 (shown %s)" % digest)
        events, _ = journal.read(self.ws)
        landed = [e for e in events if e.get("cls") == "note"]
        self.assertEqual(len(landed), 2)
        for e in landed:
            self.assertTrue(e["shown"].startswith(digest))

    def test_one_draft_says_this_one(self):
        notes.note(self.ws, "alone", target_project="geardoor")
        with pressing("k"):
            self.approve()
        self.assertIn("press k to land this one · any other key cancels", self.said)

    def test_any_other_key_cancels_and_lands_nothing(self):
        notes.note(self.ws, "waiting still", target_project="geardoor")
        with pressing("x"):
            rc = self.approve()
        self.assertEqual(rc, 0)
        self.assertEqual(self.said[-1], "cancelled — nothing landed")
        self.assertEqual(len(desk.drafts(self.ws)[0]), 1)

    def test_approve_headless_refuses_with_the_verb_in_it(self):
        notes.note(self.ws, "x", target_project="geardoor")
        with no_terminal():
            rc = self.approve()
        self.assertEqual(rc, 1)
        self.assertEqual(self.said, ["landing needs your 'k' at a real terminal — run: sandbox approve"])
        self.assertEqual(len(desk.drafts(self.ws)[0]), 1)

    def test_approve_narrows_to_one_project(self):
        project.new(self.ws, "other")
        notes.note(self.ws, "for geardoor", target_project="geardoor")
        notes.note(self.ws, "for other", target_project="other")
        with pressing("k"):
            rc = self.approve(target_project="geardoor")
        self.assertEqual(rc, 0)
        self.assertEqual([d["body"] for d in desk.drafts(self.ws)[0]], ["for other"])
        self.assertNotIn("arrived while you read", "\n".join(self.said))

    def test_canon_is_disposable_and_rebuilds(self):
        notes.note(self.ws, "a landed fact", target_project="geardoor")
        with pressing("k"):
            self.approve()
        cpath = os.path.join(project.dirpath(self.ws, "geardoor"), "CANON.md")
        os.remove(cpath)
        notes.refresh_canon(self.ws, "geardoor")
        with open(cpath) as f:
            self.assertIn("a landed fact", f.read())

    def test_recall_finds_landed_not_staged(self):
        notes.note(self.ws, "findable ruling material", target_project="geardoor")
        self.assertEqual(notes.recall(self.ws, "findable"), [])  # staged is not landed
        with pressing("k"):
            self.approve()
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

    def test_a_ruling_is_the_same_pen_with_a_stratum_on_it(self):
        """the J5 case: a ruling made outside a make is captured. Taste is the only
        stratum this verb reaches — law binds until the owner amends it, and
        an amendment is its own sitting, never a flag (law 14)."""
        from engine import verbs
        self.assertNotIn("--law", verbs.FLAGS["note"])
        disp, _ = notes.note(self.ws, "the prefix is per brand",
                             target_project="geardoor", stratum="taste")
        self.assertEqual(disp, "staged")
        self.assertEqual(desk.drafts(self.ws)[0][0]["cls"], "ruling")
        with pressing("k"):
            self.approve()
        self.assertEqual(notes.rulings(self.ws, "geardoor"),
                         ["[taste] ruling: the prefix is per brand"])

    def test_a_newer_ruling_supersedes_and_the_older_stays_readable(self):
        notes.note(self.ws, "the prefix is per project", target_project="geardoor",
                   stratum="taste")
        with pressing("k"):
            self.approve()
        events, _ = journal.read(self.ws)
        old = [e for e in events if e.get("cls") == "ruling"][0]
        notes.note(self.ws, "the prefix is per brand", target_project="geardoor",
                   stratum="taste", supersedes=old["id"])
        with pressing("k"):
            self.approve()
        self.assertEqual(notes.rulings(self.ws, "geardoor"),
                         ["[taste] ruling: the prefix is per brand"])
        self.assertEqual(len(notes.recall(self.ws, "the prefix")), 2)

    def test_the_ruling_verb_takes_the_flags_the_door_declares(self):
        import contextlib
        import io
        from engine import verbs
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = verbs.dispatch(self.ws, "note", ["--ruling", "--project", "geardoor",
                                                  "the prefix is per brand"])
        self.assertEqual(rc, 0, buf.getvalue())
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(pile[0]["cls"], "ruling")
        self.assertEqual(pile[0]["stratum"], "taste")

    def test_why_walks_every_link(self):
        """the whole chain, one addressed line each: what it says, the note
        that proposed it, when it landed, the sitting it landed inside, what
        it replaced, the run that proved it, the thought that struck it, and
        the block the key was pressed over."""
        journal.append(self.ws, {"op": "session", "phase": "open", "key": "sess-9",
                                 "project": "geardoor"})
        journal.append(self.ws, {"op": "make", "phase": "open", "project": "geardoor",
                                 "body": "the door work"})
        notes.note(self.ws, "the count is 11", target_project="geardoor")
        with pressing("k"):
            self.approve()
        events, _ = journal.read(self.ws)
        old = [e for e in events if e.get("body") == "the count is 11"][0]
        notes.note(self.ws, "the count is 12", target_project="geardoor",
                   supersedes=old["id"])
        notes.note(self.ws, "one more that rode the same key", target_project="geardoor")
        with pressing("k"):
            self.approve()
        events, _ = journal.read(self.ws)
        fact = [e for e in events if e.get("body") == "the count is 12"][0]
        run = journal.append(self.ws, {"op": "check", "project": "geardoor",
                                       "green": 1, "proves": [fact["id"]],
                                       "hash": "abc"})
        mark = journal.append(self.ws, {"op": "invalidate", "of": fact["id"],
                                        "body": "the count was wrong"})
        out = notes.why(self.ws, "the count is 12")
        text = "\n".join(out)
        self.assertEqual(len(out), 8, text)
        self.assertIn("the fact: [struck] [machine] [synthetic] the count is 12", text)
        self.assertIn("staged: %s  (draft %s)"
                      % (fact["staged_at"], fact["from_draft"][:8]), text)
        self.assertIn("landed: %s  (journal:%s)" % (fact["ts"], fact["id"]), text)
        self.assertIn("during session: sess-9 (opened", text)
        self.assertIn("supersedes: the count is 11", text)
        self.assertIn("proved by: check %s (1 green," % run["id"], text)
        self.assertIn("struck by: %s — the count was wrong" % mark["id"], text)
        self.assertIn("shown: %s with 1 other — see them: sandbox recall --shown %s"
                      % (fact["shown"][:8], fact["shown"][:8]), text)

    def test_the_session_line_names_the_sitting_a_fact_landed_inside(self):
        """the old walk named the last session event at or before the fact,
        which could be a closed sitting's own goodbye."""
        journal.append(self.ws, {"op": "session", "phase": "open", "key": "a",
                                 "ts": "2026-01-01T09:00:00Z"})
        journal.append(self.ws, {"op": "session", "phase": "close", "key": "a",
                                 "ts": "2026-01-01T17:00:00Z"})
        notes.note(self.ws, "landed with nothing open", target_project="geardoor")
        with pressing("k"):
            self.approve()
        self.assertNotIn("during session",
                         "\n".join(notes.why(self.ws, "nothing open")))

    def test_shown_lists_everything_that_rode_one_keypress(self):
        notes.note(self.ws, "first of the pair", target_project="geardoor")
        notes.note(self.ws, "second of the pair", target_project="geardoor")
        with pressing("k"):
            self.approve()
        events, _ = journal.read(self.ws)
        digest = [e for e in events if e.get("body") == "first of the pair"][0]["shown"]
        rode = notes.shown(self.ws, digest[:8])
        self.assertEqual(rode, ["[claimed] [machine] first of the pair",
                                "[claimed] [machine] second of the pair"])
        self.assertEqual(notes.shown(self.ws, "deadbeef"), [])

    def test_why_on_nothing_says_so(self):
        out = notes.why(self.ws, "ghost")
        self.assertIn("nothing landed", out[0])

    def test_recall_verb_refuses_unknown_flags(self):
        import contextlib
        import io
        from engine import verbs
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = verbs.dispatch(self.ws, "recall", ["--recent"])
        self.assertEqual(rc, 2)
        self.assertIn("recall doesn't know --recent", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
