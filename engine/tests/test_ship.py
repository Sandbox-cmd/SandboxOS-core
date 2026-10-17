# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""ship: the lines you were shown, the key you spend once, the fences.

9.0's ship shows the `## checks` lines and their fingerprint on every run
(R17) and reads one real key only when that text moved since the last
ratification (R10). The pty class below is the whole ruling in one place:
two ships in a row, the first asking, the second silent.
"""
import os
import signal
import sys
import tempfile
import threading
import time
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


class TestALineSaysItsOwnTime(TestShip):
    """a slow honest check names its limit on its own line, where the key
    reads it; every other line keeps the runner's default."""

    def setUp(self):
        super().setUp()
        self._default = ship.TIMEOUT
        ship.TIMEOUT = 1

    def tearDown(self):
        ship.TIMEOUT = self._default

    def test_the_limit_is_read_from_the_end_of_the_line(self):
        self.assertEqual(ship.line_timeout("node --test a.mjs # timeout 300s"), 300)
        self.assertEqual(ship.line_timeout("node --test a.mjs  #timeout 90"), 90)
        self.assertEqual(ship.line_timeout("node --test a.mjs"), 1)
        self.assertEqual(ship.line_timeout("echo '# timeout 300s' > f"), 1)
        self.assertEqual(ship.line_timeout("x # timeout 3600s"), 3600)

    def test_a_slow_line_with_its_limit_runs_green(self):
        self._set_checks(["sleep 2 # timeout 10s"])
        ok, results = ship.run_checks(self.ws, "geardoor")
        self.assertTrue(ok, results)

    def test_a_slow_line_without_one_still_times_out_and_says_its_limit(self):
        self._set_checks(["sleep 2"])
        ok, results = ship.run_checks(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertEqual(results[0][1:], ("timed out after 1s", 124))

    def test_a_limit_that_does_not_read_is_red_and_says_so(self):
        for line in ("true # Timeout 300s", "true # timeout 5m",
                     "true # timeout 300 s", "true # timeout 0s",
                     "true # timeout 7200s", "true # timeout %ss" % ("9" * 5000),
                     "true # timeout ٣٠s"):
            self._set_checks([line])
            ok, results = ship.run_checks(self.ws, "geardoor")
            self.assertFalse(ok, line)
            self.assertEqual(results[0][1:], (ship.UNREAD_LIMIT, 2), line)

    def test_changing_the_limit_changes_what_the_key_reads(self):
        self.assertNotEqual(ship.checks_hash(["true # timeout 60s"]),
                            ship.checks_hash(["true # timeout 600s"]))


class TestATimedOutLineLeavesNothingRunning(TestShip):
    """a line that runs out of time takes down everything it started, not
    only its shell: on 2026-10-17 a dev server outlived its timed-out check,
    held its port, and every later run of that check hung on it."""

    def setUp(self):
        super().setUp()
        self._default, self._grace = ship.TIMEOUT, ship.KILL_GRACE
        ship.TIMEOUT, ship.KILL_GRACE = 1, 1
        self.pidfile = os.path.join(self.ws, "child.pid")

    def tearDown(self):
        ship.TIMEOUT, ship.KILL_GRACE = self._default, self._grace

    def _child_is_gone(self):
        with open(self.pidfile, encoding="utf-8") as f:
            pid = int(f.read().strip())
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.05)
        os.kill(pid, signal.SIGKILL)   # never leave the test's own orphan behind
        return False

    def test_a_child_the_line_started_is_stopped_with_it(self):
        self._set_checks(["sleep 30 & echo $! > %s; wait" % self.pidfile])
        ok, results = ship.run_checks(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertEqual(results[0][1:], ("timed out after 1s", 124))
        self.assertTrue(self._child_is_gone())

    def test_a_child_that_ignores_the_stop_signal_is_killed_after_the_grace(self):
        self._set_checks(["sh -c 'trap \"\" TERM; sleep 30' & echo $! > %s; wait"
                          % self.pidfile])
        started = time.monotonic()
        ok, results = ship.run_checks(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertLess(time.monotonic() - started, 10)
        self.assertTrue(self._child_is_gone())

    def _detached_child_line(self, then="time.sleep(60)"):
        """a line whose child starts its own session, the way node's
        `detached: true` starts a dev server: it leaves the line's group."""
        return ("%s -c \"import subprocess, sys, time; "
                "c = subprocess.Popen(['sleep', '30'], start_new_session=True); "
                "open(sys.argv[1], 'w').write(str(c.pid)); %s\" %s"
                % (sys.executable, then, self.pidfile))

    def test_a_child_that_started_its_own_session_is_stopped_too(self):
        self._set_checks([self._detached_child_line()])
        ok, results = ship.run_checks(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertTrue(self._child_is_gone())

    def _interrupt_soon(self, sig):
        def fire():
            deadline = time.monotonic() + 5
            while not os.path.exists(self.pidfile) and time.monotonic() < deadline:
                time.sleep(0.05)
            os.kill(os.getpid(), sig)
        threading.Thread(target=fire, daemon=True).start()

    def test_ctrl_c_stops_the_line_and_what_it_started(self):
        ship.TIMEOUT = 60
        self._set_checks([self._detached_child_line()])
        self._interrupt_soon(signal.SIGINT)
        with self.assertRaises(KeyboardInterrupt):
            ship.run_checks(self.ws, "geardoor")
        self.assertTrue(self._child_is_gone())

    def test_a_stop_signal_to_sandbox_stops_the_line_and_leaves_handlers_as_they_were(self):
        ship.TIMEOUT = 60
        before = signal.getsignal(signal.SIGTERM)
        self._set_checks([self._detached_child_line()])
        self._interrupt_soon(signal.SIGTERM)
        with self.assertRaises(SystemExit):
            ship.run_checks(self.ws, "geardoor")
        self.assertTrue(self._child_is_gone())
        self.assertIs(signal.getsignal(signal.SIGTERM), before)

    def test_a_group_member_that_lost_its_parent_is_killed_after_the_grace(self):
        """a launcher backgrounds a server that ignores SIGTERM and exits: the
        server keeps the line's group and loses its parent link."""
        self._set_checks(["(sh -c 'trap \"\" TERM; exec sleep 30' & echo $! > %s); "
                          "sleep 60" % self.pidfile])
        ok, results = ship.run_checks(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertTrue(self._child_is_gone())

    def test_without_ps_a_timed_out_line_still_stops(self):
        saved = ship.PS
        ship.PS = ["no-such-ps-on-this-machine"]
        try:
            self._set_checks(["sleep 30 & echo $! > %s; wait" % self.pidfile])
            started = time.monotonic()
            ok, results = ship.run_checks(self.ws, "geardoor")
        finally:
            ship.PS = saved
        self.assertEqual(results[0][1:], ("timed out after 1s", 124))
        self.assertLess(time.monotonic() - started, 6)
        self.assertTrue(self._child_is_gone())

    def test_a_second_ctrl_c_during_the_stop_still_kills(self):
        ship.TIMEOUT = 60
        self._set_checks(["sh -c 'trap \"\" TERM; sleep 30' & echo $! > %s; wait"
                          % self.pidfile])

        def fire():
            deadline = time.monotonic() + 5
            while not os.path.exists(self.pidfile) and time.monotonic() < deadline:
                time.sleep(0.05)
            os.kill(os.getpid(), signal.SIGINT)
            time.sleep(0.3)
            os.kill(os.getpid(), signal.SIGINT)
        threading.Thread(target=fire, daemon=True).start()
        with self.assertRaises(KeyboardInterrupt):
            ship.run_checks(self.ws, "geardoor")
        self.assertTrue(self._child_is_gone())

    def test_an_ignored_hangup_stays_ignored(self):
        """`nohup sandbox check` keeps running when its terminal closes."""
        before = signal.signal(signal.SIGHUP, signal.SIG_IGN)
        try:
            self._set_checks(["kill -HUP $PPID; sleep 0.2; echo still here"])
            ok, results = ship.run_checks(self.ws, "geardoor")
        finally:
            signal.signal(signal.SIGHUP, before)
        self.assertTrue(ok, results)

    def test_a_line_that_finishes_in_time_is_untouched(self):
        self._set_checks(["echo out; echo err >&2; exit 3"])
        ok, results = ship.run_checks(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertEqual(results[0][1:], ("out\nerr", 3))


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
