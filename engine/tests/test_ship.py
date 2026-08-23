# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""ship: the lines you were shown, the key you spend once, the fences.

9.0's ship shows the `## checks` lines and their fingerprint on every run
(R17) and reads one real key only when that text moved since the last
ratification (R10). The pty class below is the whole ruling in one place:
two ships in a row, the first asking, the second silent.
"""
import os
import tempfile
import unittest

from engine import check, gate, journal, project, provisional, ship

from . import key, no_terminal, pressing, quiet
from .test_gate_pty import run


class TestShip(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self._set_checks(["true"])

    def _set_checks(self, checks, heading="checks"):
        cpath = project.contract_path(self.ws, "geardoor")
        with open(cpath, encoding="utf-8") as f:
            base = f.read().split("## checks")[0]
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(base + "## %s\n" % heading + "\n".join(checks) + "\n\n## notes\n")

    def _ship(self, said=None):
        return ship.ship(self.ws, "geardoor",
                         said.append if said is not None else quiet)

    def events(self, op):
        events, _ = journal.read(self.ws)
        return [e for e in events if e.get("op") == op]


class TestTheKeyOnce(TestShip):
    def test_new_checks_need_the_key_then_headless_reship_is_legal(self):
        with no_terminal():
            ok, msg = self._ship()                     # headless, unratified
        self.assertFalse(ok)
        self.assertEqual(
            msg,
            "ratifying checks needs your 'k' at a real terminal — run: sandbox ship geardoor")
        with pressing():
            ok, msg = self._ship()
        self.assertTrue(ok, msg)
        with no_terminal():
            ok, msg = self._ship()      # ratified now — headless is legal
        self.assertTrue(ok, msg)
        ships = self.events("ship")
        self.assertEqual(ships[0]["triggered"], "owner")
        self.assertEqual(ships[-1]["triggered"], "session")

    def test_changed_checks_reask_the_key(self):
        with pressing():
            self._ship()
        self._set_checks(["true", "echo more"])
        with no_terminal():
            ok, msg = self._ship()
        self.assertFalse(ok)
        self.assertIn("ratifying checks needs your", msg)

    def test_the_digest_and_the_lines_print_on_every_run(self):
        """rule R17: what will run is on the screen before anything else happens,
        whether or not a key is read this time."""
        said = []
        with pressing():
            self._ship(said)
        self.assertEqual(said[0], " 1. true")
        self.assertTrue(said[1].startswith("shown: "), said)
        self.assertEqual(said[3], "ratified — your k is on these exact checks "
                                  "(%s)" % said[1][len("shown: "):])
        again = []
        with no_terminal():
            ok, msg = self._ship(again)
        self.assertTrue(ok, msg)
        self.assertEqual(again, [" 1. true", said[1]])   # the digest, and no key

    def test_another_key_cancels_and_ships_nothing(self):
        with pressing("x"):
            ok, msg = self._ship()
        self.assertFalse(ok)
        self.assertEqual(msg, "cancelled — nothing shipped")
        self.assertEqual(self.events("ship"), [])
        self.assertEqual(self.events("ratify"), [])

    def test_synthetic_hand_marks_the_ratify(self):
        os.environ[gate.SYNTHETIC_ENV] = "1"
        try:
            with pressing():
                self._ship()
        finally:
            del os.environ[gate.SYNTHETIC_ENV]
        rat = self.events("ratify")[0]
        self.assertEqual(rat.get("hand"), "synthetic")
        self.assertTrue(rat.get("shown"))   # the key landed on what was shown


class TestTheFences(TestShip):
    def test_red_checks_refuse_with_the_output(self):
        self._set_checks(["false"])
        with pressing():
            ok, msg = self._ship()
        self.assertFalse(ok)
        self.assertEqual(msg.splitlines()[0], "FAIL false")
        self.assertEqual(msg.splitlines()[-1], "the checks are red — no ship")
        self.assertEqual(self.events("ship"), [])

    def test_no_checks_refuses_the_costume(self):
        """the refusal a stranger is most likely to meet says the loud thing,
        and still names its door."""
        self._set_checks([])
        with pressing():
            ok, msg = self._ship()
        self.assertFalse(ok)
        self.assertIn("costume", msg)
        self.assertIn("PROJECT.md", msg)

    def test_a_check_under_the_wrong_heading_is_named(self):
        """5a: a runnable line under `## notes` is invisible to the contract
        reader, and the refusal says which heading it is sitting under."""
        self._set_checks([], heading="notes")
        cpath = project.contract_path(self.ws, "geardoor")
        with open(cpath, "a", encoding="utf-8") as f:
            f.write("python3 -m unittest discover\n")
        with pressing():
            ok, msg = self._ship()
        self.assertFalse(ok)
        self.assertEqual(msg, "a line under ## notes looks like a check — "
                              "move it under ## checks")

    def test_prose_under_another_heading_is_not_called_a_check(self):
        self._set_checks([], heading="notes")
        cpath = project.contract_path(self.ws, "geardoor")
        with open(cpath, "a", encoding="utf-8") as f:
            f.write("the tax rule is five percent, ruled on the 22nd.\n")
        with pressing():
            ok, msg = self._ship()
        self.assertFalse(ok)
        self.assertIn("costume", msg)

    def test_provisional_fence_holds(self):
        with pressing():
            self._ship()                                  # ratified + green
        f = os.path.join(project.dirpath(self.ws, "geardoor"), "notes.md")
        with open(f, "w") as fh:
            fh.write("x\n")
        provisional.act(self.ws, f, "corrected\n", "a correction", project="geardoor")
        ok, msg = self._ship()
        self.assertFalse(ok)
        self.assertIn("provisional", msg)
        acts = provisional.pending(self.ws, "geardoor")
        provisional.confirm(self.ws, acts[0]["id"], key())
        ok, msg = self._ship()
        self.assertTrue(ok, msg)


class TestTheGreenProof(TestShip):
    def test_a_green_ship_mints_the_check_event_too(self):
        """the celebration leaves the same proof the quiet run leaves, so a
        claim a ship proved reads the same as one `sandbox check` proved."""
        claim = journal.append(self.ws, {
            "op": "assert", "cls": "note", "project": "geardoor",
            "body": "the tax rule is 5 percent", "ink": "claimed",
            "origin": "machine"})
        with pressing():
            ok, msg = self._ship()
        self.assertTrue(ok, msg)
        minted = self.events("check")
        self.assertEqual(len(minted), 1)
        self.assertEqual(minted[0]["proves"], [claim["id"]])
        self.assertEqual(minted[0]["hash"], ship.checks_hash(["true"]))
        self.assertEqual(msg, "shipped — 1 check(s) green, on the record "
                              "(journal:%s)" % self.events("ship")[0]["id"])

    def test_the_runner_and_the_minter_are_the_ones_check_uses(self):
        self.assertIs(check.run_checks(self.ws, "geardoor")[0], True)
        self.assertIs(check.ship, ship)


class TestClosesSinceShip(TestShip):
    def test_the_count_is_the_closes_after_the_last_ship(self):
        from engine import make, status
        for i in range(2):
            make.open_session(self.ws, "geardoor", "pass %d" % i)
            make.close_session(self.ws, "geardoor")
        self.assertEqual(ship.closes_since_ship(self.ws), [("geardoor", 2)])
        self.assertEqual(status.closes_row("geardoor", 2),
                         "2 close(s) since the last ship on geardoor "
                         "— sandbox ship geardoor")
        self.assertIn("close(s) since the last ship on", status.status(self.ws))
        with pressing():
            self._ship()
        self.assertEqual(ship.closes_since_ship(self.ws), [])
        self.assertNotIn("close(s) since the last ship", status.status(self.ws))


class TestAtATerminal(unittest.TestCase):
    """the door itself, at a pty: two ships in a row, and a pipe."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="sbx9ship-")
        run(["init"], self.home)
        run(["project", "new", "geardoor", "the store's data"], self.home)
        cpath = os.path.join(self.home, "projects", "geardoor", "PROJECT.md")
        with open(cpath, encoding="utf-8") as f:
            base = f.read().split("## checks")[0]
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(base + "## checks\ntrue\n\n## notes\n")

    def test_the_first_ship_reads_the_key_and_the_second_only_shows_the_digest(self):
        first = run(["ship", "geardoor"], self.home, key="k")
        self.assertEqual(first.returncode, 0, first.stdout)
        lines = first.stdout.splitlines()
        self.assertEqual(lines[0], " 1. true")
        self.assertTrue(lines[1].startswith("shown: "), first.stdout)
        self.assertEqual(lines[2], "press k to land this one · any other key cancels")
        self.assertEqual(lines[3], "ratified — your k is on these exact checks "
                                   "(%s)" % lines[1][len("shown: "):])
        self.assertTrue(lines[4].startswith("shipped — 1 check(s) green, on the record"),
                        first.stdout)

        second = run(["ship", "geardoor"], self.home, key="k")
        self.assertEqual(second.returncode, 0, second.stdout)
        again = second.stdout.splitlines()
        self.assertEqual(again[0], " 1. true")
        self.assertEqual(again[1], lines[1])          # the same digest
        self.assertEqual(len(again), 3, second.stdout)  # no prompt, no ratified line
        self.assertNotIn("press k", second.stdout)
        self.assertNotIn("ratified", second.stdout)

    def test_a_pipe_refuses_when_the_key_is_needed_and_exits_one(self):
        got = run(["ship", "geardoor"], self.home, pipe=True)
        self.assertEqual(got.returncode, 1)
        self.assertEqual(
            got.stdout.splitlines()[-1],
            "ratifying checks needs your 'k' at a real terminal — run: sandbox ship geardoor")
        events, _ = journal.read(self.home)
        self.assertEqual([e for e in events if e.get("op") == "ship"], [])


if __name__ == "__main__":
    unittest.main()
