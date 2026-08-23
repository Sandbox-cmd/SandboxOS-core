# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the provisional lane: correct now, confirm later — with real teeth."""
import os
import tempfile
import unittest

from engine import journal, provisional

from . import key, no_terminal, pressing


class TestProvisional(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        self.work = tempfile.mkdtemp(prefix="sbx8w-")
        self.f = os.path.join(self.work, "notes.md")
        with open(self.f, "w") as fh:
            fh.write("original\n")

    def test_act_snapshots_then_writes(self):
        e = provisional.act(self.ws, self.f, "corrected\n", "his correction", "geardoor")
        self.assertEqual(open(self.f).read(), "corrected\n")
        self.assertEqual(open(e["snapshot"], "rb").read(), b"original\n")
        self.assertEqual(len(provisional.pending(self.ws)), 1)
        self.assertEqual(len(provisional.pending(self.ws, "other")), 0)

    def test_clean_revert_restores(self):
        e = provisional.act(self.ws, self.f, "corrected\n", "why", None)
        ok, msg = provisional.revert(self.ws, e["id"])
        self.assertTrue(ok)
        self.assertEqual(open(self.f).read(), "original\n")
        self.assertEqual(provisional.pending(self.ws), [])

    def test_moved_on_file_needs_the_hand(self):
        e = provisional.act(self.ws, self.f, "corrected\n", "why", None)
        with open(self.f, "a") as fh:
            fh.write("later work built on it\n")
        ok, msg = provisional.revert(self.ws, e["id"])
        self.assertFalse(ok)
        self.assertIn("needs your hand", msg)
        self.assertIn("later work", open(self.f).read())  # nothing destroyed
        self.assertEqual(len(provisional.pending(self.ws)), 1)  # still waiting

    def test_confirm_needs_key_then_lands_with_receipt(self):
        e = provisional.act(self.ws, self.f, "corrected\n", "his correction", None)
        with no_terminal():
            ok, why = provisional.confirm(self.ws, e["id"], None)
        self.assertFalse(ok)
        self.assertIn("real terminal", why)
        ok, _ = provisional.confirm(self.ws, e["id"], key())
        self.assertTrue(ok)
        events, _ = journal.read(self.ws)
        hit = [ev for ev in events if ev.get("cls") == "provisional-confirmed"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(provisional.pending(self.ws), [])

    def test_confirm_reads_the_key_itself_when_it_is_handed_none(self):
        """the K8 case: the same gate, the same one keypress — no caller mints for it."""
        e = provisional.act(self.ws, self.f, "corrected\n", "read it yourself", None)
        with pressing("k"):
            ok, msg = provisional.confirm(self.ws, e["id"])
        self.assertTrue(ok, msg)
        self.assertEqual(provisional.pending(self.ws), [])

    def test_a_confirmed_act_carries_what_was_shown(self):
        e = provisional.act(self.ws, self.f, "corrected\n", "rode a hash", None)
        ok, _ = provisional.confirm(self.ws, e["id"], key(shown="deadbeef" * 8))
        self.assertTrue(ok)
        events, _ = journal.read(self.ws)
        hit = [ev for ev in events if ev.get("body") == "rode a hash"][0]
        self.assertEqual(hit["shown"], "deadbeef" * 8)
        self.assertEqual(hit["hand"], "synthetic")

    def test_act_on_new_file_reverts_to_absence(self):
        g = os.path.join(self.work, "new.md")
        e = provisional.act(self.ws, g, "born provisional\n", "why", None)
        ok, _ = provisional.revert(self.ws, e["id"])
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(g))


if __name__ == "__main__":
    unittest.main()
