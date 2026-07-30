# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The update rehearsal: a workshop at N meets core N+1 and everything opens."""
import os
import tempfile
import unittest

from engine import journal, notes, onboard, project, ship, update


class TestSkewAndMigrations(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        onboard.run(self.ws)
        update.record_version(self.ws)

    def test_current_workshop_reports_no_skew(self):
        self.assertIsNone(update.skew(self.ws))

    def test_stale_version_named_plainly(self):
        p = update._version_path(self.ws)
        import json
        with open(p, "w") as f:
            json.dump({"version": "7.9.0", "migration": 0}, f)
        msg = update.skew(self.ws)
        self.assertIn("7.9.0", msg)
        self.assertIn("sandbox update", msg)

    def test_migrations_apply_once_and_record_high_water(self):
        calls = []
        update.MIGRATIONS.append((1, "test move", lambda ws: calls.append(ws) or "done"))
        try:
            lines = update.migrate(self.ws)
            self.assertTrue(any("migration 1" in l for l in lines))
            lines = update.migrate(self.ws)
            self.assertTrue(any("no migrations pending" in l for l in lines))
            self.assertEqual(len(calls), 1)  # idempotent by high-water
            self.assertEqual(update.recorded(self.ws)["migration"], 1)
        finally:
            update.MIGRATIONS.pop()

    def test_rehearsal_workshop_at_n_meets_n_plus_one(self):
        """The suite's standing promise: after an update pass, everything
        the workshop held still opens."""
        project.new(self.ws, "geardoor", "the store")
        notes.note(self.ws, "a landed fact", target_project="geardoor")
        notes.approve(self.ws, is_real_tty=True, keychar="k")
        update.MIGRATIONS.append((1, "rehearsal move", lambda ws: "moved nothing"))
        try:
            ok, text = update.run(self.ws)
            self.assertTrue(ok, text)
            self.assertIn("workshop now current", text)
            events, scars = journal.read(self.ws)
            self.assertEqual(scars, [])
            self.assertTrue(any(e.get("body") == "a landed fact" for e in events))
            hits = notes.recall(self.ws, "landed fact")
            self.assertEqual(len(hits), 1)
        finally:
            update.MIGRATIONS.pop()


class TestSeventhBodySeams(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        onboard.run(self.ws)

    def test_path_map_resolves_old_receipts(self):
        update.set_path_map(self.ws, [("/old/Sandbox/channels",
                                       os.path.join(self.ws, "projects"))])
        old = "/old/Sandbox/channels/geardoor/CANON.md"
        resolved = update.resolve(self.ws, old)
        self.assertTrue(resolved.startswith(self.ws))
        self.assertTrue(resolved.endswith("geardoor/CANON.md"))
        self.assertEqual(update.resolve(self.ws, "/unmapped/x"), "/unmapped/x")

    def test_void_ratifications_says_it_out_loud(self):
        from engine import gate
        project.new(self.ws, "geardoor")
        cpath = project.contract_path(self.ws, "geardoor")
        base = open(cpath).read().split("## checks")[0]
        open(cpath, "w").write(base + "## checks\ntrue\n")
        ship.ratify(self.ws, "geardoor",
                    gate.mint_consent(is_real_tty=True, keychar="k"))
        msg = update.void_ratifications(self.ws, "paths changed in the move")
        self.assertIn("geardoor", msg)
        self.assertIn("await your k again", msg)
        ok, ship_msg = ship.ship(self.ws, "geardoor")  # headless, now unratified
        self.assertFalse(ok)
        self.assertIn("new or changed", ship_msg)


if __name__ == "__main__":
    unittest.main()
