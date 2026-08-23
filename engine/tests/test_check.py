# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""check: the run that reaches the third rung, and never ships anything.

`ship` is the celebration and it costs a key. `check` is the same lines run
without one, so a person can find out where they stand for free — and a
green run is the only thing in the system that lets a claim read `checked`.
"""
import contextlib
import io
import json
import os
import tempfile
import unittest

from engine import check, journal, project, registry, ship, verbs


def _contract(ws, name, checks):
    with open(project.contract_path(ws, name), "a", encoding="utf-8") as f:
        f.write("\n## checks\n" + "\n".join(checks) + "\n")


def _run(ws, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = verbs.dispatch(ws, "check", argv)
    return rc, buf.getvalue()


class TestCheck(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor", "the door work")

    def claim(self, body, name="geardoor"):
        return journal.append(self.ws, {"op": "assert", "cls": "note", "project": name,
                                        "body": body, "ink": "claimed", "origin": "machine"})

    def events(self, op):
        events, _ = journal.read(self.ws)
        return [e for e in events if e.get("op") == op]

    def test_the_runner_is_ships_own(self):
        """imported, never copied: a check and a ship read the same lines the
        same way, or one of them is lying about the project."""
        self.assertIs(check.ship.run_checks, ship.run_checks)

    def test_a_project_with_no_checks_says_where_to_put_them(self):
        rc, out = _run(self.ws, ["geardoor"])
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip(), "nothing under ## checks in PROJECT.md — "
                                      "put one command per line there")
        self.assertEqual(self.events("check"), [])

    def test_green_prints_a_line_per_check_and_mints_one_event(self):
        _contract(self.ws, "geardoor", ["true", "test 1 = 1"])
        self.claim("the tax rule is 5 percent")
        self.claim("the prefix is per brand")
        rc, out = _run(self.ws, ["geardoor"])
        self.assertEqual(rc, 0, out)
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], "ok   true")
        self.assertEqual(lines[1], "ok   test 1 = 1")
        minted = self.events("check")
        self.assertEqual(len(minted), 1)
        e = minted[0]
        self.assertEqual(lines[2], "2 check(s) green on geardoor — 2 claim(s) now "
                                   "read [checked] (journal:%s)" % e["id"])
        self.assertEqual(e["green"], 2)
        self.assertEqual(e["project"], "geardoor")
        self.assertEqual(e["hash"], ship.checks_hash(["true", "test 1 = 1"]))
        self.assertEqual(len(e["proves"]), 2)

    def test_red_refuses_with_the_fail_lines_and_mints_nothing(self):
        _contract(self.ws, "geardoor", ["true", "false"])
        rc, out = _run(self.ws, ["geardoor"])
        self.assertEqual(rc, 1)
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], "ok   true")
        self.assertEqual(lines[1], "FAIL false")
        self.assertEqual(lines[2], "     (no output)")
        self.assertEqual(lines[3], "1 red on geardoor — fix them, then: sandbox check geardoor")
        self.assertEqual(self.events("check"), [])

    def test_check_never_ships_and_never_ratifies(self):
        """the key belongs to ship. A green check leaves no ratification, no
        ship event, and asks for nothing at a terminal."""
        _contract(self.ws, "geardoor", ["true"])
        rc, _ = _run(self.ws, ["geardoor"])
        self.assertEqual(rc, 0)
        self.assertEqual(self.events("ratify"), [])
        self.assertEqual(self.events("ship"), [])
        self.assertFalse(os.path.exists(
            os.path.join(self.ws, journal.STATE_DIR, "ratified.json")))

    def test_proves_reaches_back_to_the_previous_green_run(self):
        _contract(self.ws, "geardoor", ["true"])
        old = self.claim("landed before the first run")
        check.run(self.ws, "geardoor")
        fresh = self.claim("landed after it")
        second = check.run(self.ws, "geardoor")
        self.assertTrue(second[0], second[1])
        runs = self.events("check")
        self.assertEqual(runs[0]["proves"], [old["id"]])
        self.assertEqual(runs[1]["proves"], [fresh["id"]])

    def test_with_no_previous_run_the_window_opens_at_the_first_make(self):
        _contract(self.ws, "geardoor", ["true"])
        before = self.claim("said before any make opened")
        journal.append(self.ws, {"op": "make", "phase": "open", "project": "geardoor",
                                 "body": "the door work"})
        after = self.claim("said inside the work")
        check.run(self.ws, "geardoor")
        proved = self.events("check")[0]["proves"]
        self.assertEqual(proved, [after["id"]])
        self.assertNotIn(before["id"], proved)

    def test_a_receipt_and_a_ruling_are_not_this_verbs_business(self):
        """a run raises claims. A receipt already rests on a file that opens,
        and a ruling is a decision no command can be right or wrong about."""
        _contract(self.ws, "geardoor", ["true"])
        journal.append(self.ws, {"op": "assert", "cls": "ruling", "project": "geardoor",
                                 "body": "the prefix is per brand", "stratum": "taste"})
        claim = self.claim("a claim with nothing under it")
        check.run(self.ws, "geardoor")
        self.assertEqual(self.events("check")[0]["proves"], [claim["id"]])

    def test_another_projects_claims_stay_where_they_are(self):
        project.new(self.ws, "other")
        _contract(self.ws, "geardoor", ["true"])
        mine = self.claim("on geardoor")
        self.claim("on other", name="other")
        check.run(self.ws, "geardoor")
        self.assertEqual(self.events("check")[0]["proves"], [mine["id"]])

    def test_the_verb_refuses_without_a_project(self):
        rc, out = _run(self.ws, [])
        self.assertEqual(rc, 2)
        self.assertIn("check needs a project", out)

    def test_the_event_is_readable_as_json_on_the_record(self):
        _contract(self.ws, "geardoor", ["true"])
        check.run(self.ws, "geardoor")
        with open(journal.path(self.ws), encoding="utf-8") as f:
            last = json.loads(f.read().strip().splitlines()[-1])
        self.assertEqual(last["op"], "check")
        self.assertNotIn("ink", last)
        world = registry.project(self.ws)
        self.assertTrue(world["check"])


if __name__ == "__main__":
    unittest.main()
