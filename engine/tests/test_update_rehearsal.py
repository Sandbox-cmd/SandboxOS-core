# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the update rehearsal: a workshop at N meets core N+1 and everything opens."""
import json
import os
import tempfile
import unittest

from engine import journal, notes, onboard, project, ship, update

from . import key, no_terminal, pressing, quiet


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
        n = max([m[0] for m in update.MIGRATIONS] or [0]) + 1
        update.MIGRATIONS.append((n, "test move", lambda ws: calls.append(ws) or "done"))
        try:
            lines = update.migrate(self.ws)
            self.assertTrue(any("migration %d" % n in l for l in lines))
            lines = update.migrate(self.ws)
            self.assertTrue(any("no migrations pending" in l for l in lines))
            self.assertEqual(len(calls), 1)  # idempotent by high-water
            self.assertEqual(update.recorded(self.ws)["migration"], n)
        finally:
            update.MIGRATIONS.pop()

    def test_rehearsal_workshop_at_n_meets_n_plus_one(self):
        """the suite's standing promise: after an update pass, everything
        the workshop held still opens."""
        project.new(self.ws, "geardoor", "the store")
        notes.note(self.ws, "a landed fact", target_project="geardoor")
        with pressing("k"):
            notes.approve(self.ws, out=lambda _line: None)
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


class TestMigrationTwo(unittest.TestCase):
    """a workshop 8.2.3 onboarded, meeting the one-plugin core.

    8.2.3 copied the guard beside the record, the six briefs and the style
    into the workshop, wrote an `engine-root` pointer for the guard to read,
    and wired the guard from the workshop's own settings. 9.0 loads all of it
    from the plugin, so migration 2 takes the copies back out — the ones it
    placed and nobody touched — and leaves an edited one where it is.
    """

    BRIEFS = ("challenger.md", "checker.md", "keeper.md",
              "producer.md", "surveyor.md", "voicer.md")

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx823-")
        onboard.run(self.ws)
        self.planted = self._plant_823()
        # the workshop's high-water is 8.2.3's: migration 2 has not run
        update.record_version(self.ws, migration=1)

    def _plant(self, dest, text):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)
        return dest

    def _plant_823(self):
        """what 8.2.3 put in a workshop, back on disk and back in the book."""
        from engine import placement
        state = os.path.join(self.ws, journal.STATE_DIR)
        placed = [self._plant(os.path.join(state, "vessel", "guard.py"),
                              "the 8.2.3 fence\n"),
                  self._plant(os.path.join(self.ws, ".claude", "output-styles",
                                           "across-the-desk.md"),
                              "the 8.2.3 style\n")]
        for name in self.BRIEFS:
            placed.append(self._plant(
                os.path.join(self.ws, ".claude", "agents", name),
                "the 8.2.3 brief for %s\n" % name))
        self._plant(os.path.join(state, "vessel", "engine-root"), "/old/eighth/core")
        b = placement.book(self.ws)
        for dest in placed:
            b[dest] = {"sha": placement.file_sha(dest)}
        placement.write_book(self.ws, b)
        sp = os.path.join(self.ws, ".claude", "settings.json")
        with open(sp, "w", encoding="utf-8") as f:
            json.dump({"hooks": {"PreToolUse": [
                {"matcher": "Edit|Write|NotebookEdit|Bash",
                 "hooks": [{"type": "command", "command":
                            'python3 "%s/vessel/guard.py"' % state}]}]},
                "permissions": {"deny": onboard.deny_floor_rules(self.ws)},
                "outputStyle": "across-the-desk"}, f)
        return placed

    def test_pristine_copies_are_removed_and_the_pointer_goes(self):
        lines = update.migrate(self.ws)
        text = "\n".join(lines)
        self.assertIn("migration 2: one plugin — the placed copies retire", text)
        for dest in self.planted:
            self.assertFalse(os.path.exists(dest), dest)
            self.assertIn("removed %s" % os.path.basename(dest), text)
        self.assertFalse(os.path.exists(
            os.path.join(self.ws, journal.STATE_DIR, "vessel")))
        self.assertIn("removed engine-root", text)
        self.assertIn("read-back: the wiring took", text)
        self.assertEqual(update.recorded(self.ws)["migration"], 2)

    def test_an_edited_copy_is_kept_and_named(self):
        edited = os.path.join(self.ws, ".claude", "agents", "checker.md")
        with open(edited, "a", encoding="utf-8") as f:
            f.write("my own line\n")
        text = "\n".join(update.migrate(self.ws))
        self.assertTrue(os.path.exists(edited))
        self.assertIn("kept checker.md — you changed it, so it stays", text)
        self.assertFalse(os.path.exists(
            os.path.join(self.ws, ".claude", "agents", "voicer.md")))

    def test_the_settings_come_out_wired_to_the_plugin(self):
        update.migrate(self.ws)
        sp = os.path.join(self.ws, ".claude", "settings.json")
        with open(sp, encoding="utf-8") as f:
            back = json.load(f)
        self.assertNotIn("hooks", back)
        self.assertEqual(back["enabledPlugins"], {"sandbox-os@sandbox": True})
        self.assertEqual(
            back["extraKnownMarketplaces"]["sandbox"]["source"]["source"],
            "directory")
        self.assertIn(onboard.TRANSCRIPT_DENY, back["permissions"]["deny"])

    def test_it_runs_once_and_says_so_the_second_time(self):
        update.migrate(self.ws)
        again = update.migrate(self.ws)
        self.assertEqual(again, ["no migrations pending"])

    def test_a_workshop_with_nothing_of_8x_left_says_that_plainly(self):
        update.migrate(self.ws)
        fresh = tempfile.mkdtemp(prefix="sbx9-")
        onboard.run(fresh)
        update.record_version(fresh, migration=1)
        text = "\n".join(update.migrate(fresh))
        self.assertIn("migration 2", text)
        self.assertIn("nothing 8.x placed is left in this workshop", text)
        self.assertIn("settings already carry the plugin's entry", text)
        self.assertNotIn("removed", text)


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
                    key())
        msg = update.void_ratifications(self.ws, "paths changed in the move")
        self.assertIn("geardoor", msg)
        self.assertIn("await your k again", msg)
        with no_terminal():                    # headless, and now unratified
            ok, ship_msg = ship.ship(self.ws, "geardoor", quiet)
        self.assertFalse(ok)
        self.assertIn("ratifying checks needs your 'k' at a real terminal", ship_msg)


if __name__ == "__main__":
    unittest.main()
