# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The gate and the desk: consent is a keystroke, ink is computed, nothing
lands headless."""
import os
import tempfile
import unittest

from engine import desk, gate, journal


def key():
    return gate.mint_consent(is_real_tty=True, keychar="k")


class TestGate(unittest.TestCase):
    def test_headless_mints_nothing(self):
        self.assertIsNone(gate.mint_consent(is_real_tty=False, keychar="k"))

    def test_wrong_key_mints_nothing(self):
        self.assertIsNone(gate.mint_consent(is_real_tty=True, keychar="y"))

    def test_smuggled_consent_refused(self):
        verdict, why = gate.decide({"target": "rules", "approved": True}, key())
        self.assertEqual(verdict, "REFUSE")
        self.assertIn("tampering", why)

    def test_ungated_passes_gated_needs_key(self):
        self.assertEqual(gate.decide({"target": "note"})[0], "PASS")
        self.assertEqual(gate.decide({"target": "rules"})[0], "REFUSE")
        self.assertEqual(gate.decide({"target": "rules"}, key())[0], "PROMOTE")

    def test_synthetic_hand_says_its_name(self):
        os.environ[gate.SYNTHETIC_ENV] = "1"
        try:
            c = gate.mint_consent(is_real_tty=True, keychar="k")
            self.assertTrue(c.get("synthetic"))
        finally:
            del os.environ[gate.SYNTHETIC_ENV]


class TestDesk(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def test_machine_origin_stages(self):
        disp, msg = desk.submit(self.ws, {"body": "a finding", "origin": "machine"})
        self.assertEqual(disp, "staged")
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(len(pile), 1)

    def test_self_inked_claim_refused(self):
        disp, why = desk.submit(self.ws, {"body": "x", "ink": "checked"})
        self.assertEqual(disp, "refused")
        self.assertIn("ink", why)

    def test_smuggled_consent_refused_at_the_desk(self):
        disp, _ = desk.submit(self.ws, {"body": "x", "approved": True})
        self.assertEqual(disp, "refused")

    def test_human_at_tty_lands_with_computed_ink(self):
        disp, _ = desk.submit(self.ws, {"body": "ruled", "origin": "human",
                                        "receipt": "journal:eid-x"}, key())
        self.assertEqual(disp, "landed")
        events, _ = journal.read(self.ws)
        landed = [e for e in events if e.get("body") == "ruled"]
        self.assertEqual(landed[0]["ink"], "receipted")

    def test_land_all_needs_the_key_and_empties_staging(self):
        desk.submit(self.ws, {"body": "one", "origin": "machine"})
        desk.submit(self.ws, {"body": "two", "origin": "machine"})
        n, msg = desk.land_all(self.ws, None)
        self.assertEqual(n, 0)
        n, msg = desk.land_all(self.ws, key())
        self.assertEqual(n, 2)
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(pile, [])


if __name__ == "__main__":
    unittest.main()
