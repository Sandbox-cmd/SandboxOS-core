# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Placement provenance: every edge the challenge named, proven."""
import os
import tempfile
import unittest

from engine import journal, placement


class TestPlacement(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        self.srcdir = tempfile.mkdtemp(prefix="sbx8s-")
        self.src = os.path.join(self.srcdir, "contract.md")
        open(self.src, "w").write("v1\n")
        self.dest = os.path.join(self.ws, "CLAUDE.md")

    def test_place_refresh_untouched(self):
        placement.sync(self.ws, {self.dest: self.src})
        self.assertEqual(open(self.dest).read(), "v1\n")
        open(self.src, "w").write("v2\n")
        report = placement.sync(self.ws, {self.dest: self.src})
        self.assertEqual(open(self.dest).read(), "v2\n")
        self.assertTrue(any("refreshed" in r for r in report))

    def test_diverged_left_alone_and_named(self):
        placement.sync(self.ws, {self.dest: self.src})
        open(self.dest, "w").write("my own words\n")
        open(self.src, "w").write("v2\n")
        report = placement.sync(self.ws, {self.dest: self.src})
        self.assertEqual(open(self.dest).read(), "my own words\n")
        self.assertTrue(any("left alone" in r for r in report))
        self.assertIn(self.dest, placement.diverged(self.ws))

    def test_convergent_edit_rebaselines(self):
        placement.sync(self.ws, {self.dest: self.src})
        open(self.dest, "w").write("v2\n")   # user edits to exactly the next version
        open(self.src, "w").write("v2\n")
        report = placement.sync(self.ws, {self.dest: self.src})
        self.assertTrue(any("re-baselined" in r for r in report))
        self.assertNotIn(self.dest, placement.diverged(self.ws))

    def test_deletion_pristine_removed_diverged_kept(self):
        other_src = os.path.join(self.srcdir, "hook.py")
        open(other_src, "w").write("hook v1\n")
        other_dest = os.path.join(self.ws, "hook.py")
        placement.sync(self.ws, {self.dest: self.src, other_dest: other_src})
        report = placement.sync(self.ws, {self.dest: self.src})  # hook dropped from payload
        self.assertFalse(os.path.exists(other_dest))
        self.assertTrue(any("removed" in r for r in report))
        placement.sync(self.ws, {self.dest: self.src, other_dest: other_src})
        open(other_dest, "a").write("my tweak\n")
        report = placement.sync(self.ws, {self.dest: self.src})
        self.assertTrue(os.path.exists(other_dest))
        self.assertTrue(any("no longer shipped, but you changed it" in r for r in report))

    def test_never_recorded_never_touched(self):
        yours = os.path.join(self.ws, "CLAUDE.md")
        open(yours, "w").write("mine before any init\n")
        report = placement.sync(self.ws, {self.dest: self.src})
        self.assertEqual(open(yours).read(), "mine before any init\n")
        self.assertTrue(any("never placed by me" in r for r in report))

    def test_reset_rebaselines_on_the_owners_word(self):
        placement.sync(self.ws, {self.dest: self.src})
        open(self.dest, "w").write("drifted\n")
        placement.sync(self.ws, {self.dest: self.src})
        self.assertIn(self.dest, placement.diverged(self.ws))
        placement.reset(self.ws, self.dest, self.src)
        self.assertEqual(open(self.dest).read(), "v1\n")
        self.assertNotIn(self.dest, placement.diverged(self.ws))

    def test_every_move_minted_an_event(self):
        placement.sync(self.ws, {self.dest: self.src})
        events, _ = journal.read(self.ws)
        self.assertTrue(any(e.get("op") == "place" and e.get("action") == "placed"
                            for e in events))


class TestInit(unittest.TestCase):
    def test_init_opens_places_wires_and_reads_back(self):
        from engine import onboard
        ws = tempfile.mkdtemp(prefix="sbx8-")
        ok, text = onboard.run(ws)
        self.assertTrue(ok, text)
        self.assertIn("read-back: the wiring took", text)
        self.assertTrue(os.path.exists(os.path.join(ws, "CLAUDE.md")))
        self.assertTrue(os.path.exists(os.path.join(ws, ".claude", "settings.json")))
        # The crew boots with every fresh instance.
        self.assertTrue(os.path.exists(os.path.join(ws, ".claude", "agents", "checker.md")))
        self.assertTrue(os.path.exists(os.path.join(ws, ".claude", "agents", "challenger.md")))
        import json
        with open(os.path.join(ws, ".claude", "settings.json")) as f:
            settings = json.load(f)
        self.assertEqual(len([r for r in settings["permissions"]["deny"]]), 4)

    def test_init_idempotent_never_touches_the_living(self):
        from engine import journal as j, onboard
        ws = tempfile.mkdtemp(prefix="sbx8-")
        onboard.run(ws)
        j.append(ws, {"op": "assert", "body": "precious", "cls": "note"})
        ok, text = onboard.run(ws)
        self.assertTrue(ok)
        self.assertIn("nothing that lives is touched", text)
        events, _ = j.read(ws)
        self.assertTrue(any(e.get("body") == "precious" for e in events))


if __name__ == "__main__":
    unittest.main()
