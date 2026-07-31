# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Ship: real checks, the owner's hash, and fences that hold."""
import os
import tempfile
import unittest

from engine import gate, journal, project, provisional, ship


def key():
    return gate.mint_consent(is_real_tty=True, keychar="k")


class TestShip(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self._set_checks(["true"])

    def _set_checks(self, checks):
        cpath = project.contract_path(self.ws, "geardoor")
        base = open(cpath).read().split("## checks")[0]
        with open(cpath, "w") as f:
            f.write(base + "## checks\n" + "\n".join(checks) + "\n\n## notes\n")

    def test_new_checks_need_the_key_then_headless_reship_is_legal(self):
        ok, msg = ship.ship(self.ws, "geardoor")  # headless, unratified
        self.assertFalse(ok)
        self.assertIn("new or changed", msg)
        ok, msg = ship.ship(self.ws, "geardoor", key())
        self.assertTrue(ok)
        ok, msg = ship.ship(self.ws, "geardoor")  # ratified now — headless legal
        self.assertTrue(ok)
        events, _ = journal.read(self.ws)
        ships = [e for e in events if e.get("op") == "ship"]
        self.assertEqual(ships[-1]["triggered"], "session")

    def test_changed_checks_reask_the_key(self):
        ship.ship(self.ws, "geardoor", key())
        self._set_checks(["true", "echo more"])
        ok, msg = ship.ship(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertIn("new or changed", msg)

    def test_red_checks_refuse_with_the_output(self):
        self._set_checks(["false"])
        ok, msg = ship.ship(self.ws, "geardoor", key())
        self.assertFalse(ok)
        self.assertIn("red", msg)
        self.assertIn("FAIL false", msg)

    def test_no_checks_refuses_the_costume(self):
        """The refusal a stranger is most likely to meet says the loud thing,
        and still names its door."""
        self._set_checks([])
        ok, msg = ship.ship(self.ws, "geardoor", key())
        self.assertFalse(ok)
        self.assertIn("costume", msg)
        self.assertIn("PROJECT.md", msg)

    def test_provisional_fence_holds(self):
        ship.ship(self.ws, "geardoor", key())  # ratified + green
        f = os.path.join(project.dirpath(self.ws, "geardoor"), "notes.md")
        with open(f, "w") as fh:
            fh.write("x\n")
        provisional.act(self.ws, f, "corrected\n", "a correction", project="geardoor")
        ok, msg = ship.ship(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertIn("provisional", msg)
        acts = provisional.pending(self.ws, "geardoor")
        provisional.confirm(self.ws, acts[0]["id"], key())
        ok, msg = ship.ship(self.ws, "geardoor")
        self.assertTrue(ok)

    def test_synthetic_hand_marks_the_ratify(self):
        os.environ[gate.SYNTHETIC_ENV] = "1"
        try:
            ship.ship(self.ws, "geardoor", key())
        finally:
            del os.environ[gate.SYNTHETIC_ENV]
        events, _ = journal.read(self.ws)
        rat = [e for e in events if e.get("op") == "ratify"][0]
        self.assertEqual(rat.get("hand"), "synthetic")


if __name__ == "__main__":
    unittest.main()
