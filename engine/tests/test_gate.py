# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the gate and the desk: consent is a keystroke read from the terminal, ink
is computed, everything stages, and a landing carries what it was shown."""
import os
import tempfile
import unittest

from engine import desk, gate, journal

from . import key, no_terminal, pressing


class TestGate(unittest.TestCase):
    def test_headless_mints_nothing(self):
        with no_terminal():
            self.assertIsNone(gate.mint_consent())

    def test_wrong_key_mints_nothing(self):
        with pressing("x"):
            self.assertIsNone(gate.mint_consent())

    def test_the_rig_key_is_always_stamped_synthetic(self):
        """set on its own, with no synthetic-tty variable in sight: no rig
        path can mint a hand that reads as a person's."""
        self.assertNotIn(gate.SYNTHETIC_ENV, os.environ)
        with pressing("k"):
            c = gate.mint_consent()
        self.assertTrue(c.get("synthetic"))

    def test_the_synthetic_terminal_still_says_its_name(self):
        os.environ[gate.SYNTHETIC_ENV] = "1"
        try:
            self.assertTrue(key().get("synthetic"))
        finally:
            del os.environ[gate.SYNTHETIC_ENV]

    def test_read_key_says_why_it_could_not(self):
        with no_terminal():
            char, why = gate.read_key()
        self.assertIsNone(char)
        self.assertEqual(why, "no terminal")

    def test_the_key_parameters_are_gone(self):
        """the scar: five call sites handed the gate a key nobody pressed."""
        import inspect
        params = list(inspect.signature(gate.mint_consent).parameters)
        self.assertEqual(params, ["shown"])

    def test_smuggled_consent_refused(self):
        verdict, why = gate.decide({"target": "rules", "approved": True}, key())
        self.assertEqual(verdict, "REFUSE")
        self.assertIn("tampering", why)

    def test_ungated_passes_gated_needs_key(self):
        self.assertEqual(gate.decide({"target": "note"})[0], "PASS")
        self.assertEqual(gate.decide({"target": "rules"})[0], "REFUSE")
        self.assertEqual(gate.decide({"target": "rules"}, key())[0], "PROMOTE")


class TestShownDigest(unittest.TestCase):
    def test_the_digest_is_stable_over_the_same_block(self):
        lines = [" 1. [note] one", " 2. [note] two"]
        self.assertEqual(gate.shown_digest(lines), gate.shown_digest(list(lines)))
        self.assertNotEqual(gate.shown_digest(lines),
                            gate.shown_digest(lines + [" 3. [note] three"]))

    def test_show_prints_the_block_then_its_first_eight(self):
        out = []
        n, digest = gate.show(["[note] one", "[note] two"], out.append)
        self.assertEqual(n, 2)
        self.assertEqual(out[:2], [" 1. [note] one", " 2. [note] two"])
        self.assertEqual(out[2], "shown: %s" % digest[:8])
        self.assertEqual(digest, gate.shown_digest(out[:2]))

    def test_a_long_pile_is_paged_and_the_hash_covers_the_page(self):
        out = []
        n, digest = gate.show(["[note] %d" % i for i in range(50)], out.append)
        self.assertEqual(n, gate.PAGE)
        self.assertEqual(out[gate.PAGE], "20 of 50 shown — land these, or "
                         "narrow with: sandbox approve --project NAME")
        self.assertEqual(digest, gate.shown_digest(out[:gate.PAGE + 1]))

    def test_the_prompt_counts_what_it_shows(self):
        one, many = [], []
        gate.ask(1, one.append)
        gate.ask(3, many.append)
        self.assertEqual(one, ["press k to land this one · any other key cancels"])
        self.assertEqual(many, ["press k to land these 3 · any other key cancels"])


class TestDesk(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)

    def test_machine_origin_stages(self):
        disp, msg = desk.submit(self.ws, {"body": "a finding", "origin": "machine"})
        self.assertEqual(disp, "staged")
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(len(pile), 1)

    def test_human_origin_stages_too(self):
        """rule R3, stage-first everywhere: the hand that typed it is one fact, the
        key that lands it is another."""
        disp, msg = desk.submit(self.ws, {"body": "ruled", "origin": "human",
                                          "receipt": "journal:eid-x"})
        self.assertEqual(disp, "staged")
        self.assertIn("waiting for your approval", msg)
        events, _ = journal.read(self.ws)
        self.assertEqual([e for e in events if e.get("body") == "ruled"], [])

    def test_self_inked_claim_refused(self):
        disp, why = desk.submit(self.ws, {"body": "x", "ink": "checked"})
        self.assertEqual(disp, "refused")
        self.assertIn("the mark is computed at landing", why)

    def test_smuggled_consent_refused_at_the_desk(self):
        disp, _ = desk.submit(self.ws, {"body": "x", "approved": True})
        self.assertEqual(disp, "refused")

    def test_land_all_needs_the_key_and_empties_staging(self):
        desk.submit(self.ws, {"body": "one", "origin": "machine"})
        desk.submit(self.ws, {"body": "two", "origin": "machine"})
        n, msg = desk.land_all(self.ws, None)
        self.assertEqual(n, 0)
        self.assertIn("real terminal", msg)
        n, msg = desk.land_all(self.ws, key())
        self.assertEqual(n, 2)
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(pile, [])

    def test_the_landed_line_carries_what_was_shown(self):
        desk.submit(self.ws, {"body": "one", "origin": "machine"})
        pile, _ = desk.drafts(self.ws)
        digest = gate.shown_digest([desk.row(d) for d in pile])
        n, _ = desk.land_all(self.ws, key(shown=digest), shown=pile)
        self.assertEqual(n, 1)
        events, _ = journal.read(self.ws)
        landed = [e for e in events if e.get("body") == "one"][0]
        self.assertEqual(landed["shown"], digest)
        self.assertEqual(landed["hand"], "synthetic")

    def test_a_line_that_arrived_while_you_read_stays(self):
        desk.submit(self.ws, {"body": "shown to you", "origin": "machine"})
        shown, _ = desk.drafts(self.ws)
        desk.submit(self.ws, {"body": "arrived after", "origin": "machine"})
        n, _ = desk.land_all(self.ws, key(), shown=shown)
        self.assertEqual(n, 1)
        left, _ = desk.drafts(self.ws)
        self.assertEqual([d["body"] for d in left], ["arrived after"])

    def test_a_shown_line_that_moved_fails_the_whole_pile_closed(self):
        desk.submit(self.ws, {"body": "one", "origin": "machine"})
        desk.submit(self.ws, {"body": "two", "origin": "machine"})
        shown, _ = desk.drafts(self.ws)
        desk.drop(self.ws, 1)
        n, msg = desk.land_all(self.ws, key(), shown=shown)
        self.assertIsNone(n)
        self.assertIn("staging moved under you", msg)
        events, _ = journal.read(self.ws)
        self.assertEqual([e for e in events if e.get("op") == "assert"], [])
        self.assertEqual(len(desk.drafts(self.ws)[0]), 1)

    def test_a_torn_line_survives_the_landing(self):
        desk.submit(self.ws, {"body": "one", "origin": "machine"})
        with open(desk.staging_path(self.ws), "ab") as f:
            f.write(b"{torn json\n")
        n, msg = desk.land_all(self.ws, key())
        self.assertEqual(n, 1)
        self.assertIn("unreadable line(s) kept on disk", msg)
        with open(desk.staging_path(self.ws), "rb") as f:
            self.assertIn(b"{torn json", f.read())


if __name__ == "__main__":
    unittest.main()
