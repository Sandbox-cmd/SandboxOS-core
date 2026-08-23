# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""placement provenance: every edge the challenge named, proven."""
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

    def test_kept_file_drift_named(self):
        """the 08-09 scar, as a check (scars row 27).

        `update` said "kept (yours, never placed by me)", doctor said "placed
        files current", and the copy nobody had recorded sat three releases
        behind what shipped. the point of this test is the naming: doctor's
        line carries the file's own name, and it goes when the file is back.
        """
        from engine import onboard, status
        from engine.tests import elsewhere_home
        payload = onboard.shipped_payload(self.ws)
        stale = sorted(payload)[0]
        with open(stale, "w", encoding="utf-8") as f:
            f.write("three releases old\n")
        report = placement.sync(self.ws, payload)
        self.assertTrue(any("never placed by me" in r and stale in r
                            for r in report), report)
        self.assertEqual(placement.unrecorded_drift(self.ws, payload), [stale])

        with elsewhere_home():
            ok, lines = status.doctor(self.ws)
        self.assertFalse(ok)
        named = [l for l in lines
                 if "kept files" in l and os.path.basename(stale) in l]
        self.assertEqual(len(named), 1,
                         "doctor never named the drifted file: %s" % lines)

        placement.reset(self.ws, stale, payload[stale])
        self.assertEqual(placement.unrecorded_drift(self.ws, payload), [])
        with elsewhere_home():
            _ok, lines = status.doctor(self.ws)
        self.assertEqual([l for l in lines if "kept files" in l
                          and os.path.basename(stale) in l], [])

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
        # The crew is loaded from the plugin now: init places the contract and
        # copies nothing a second tree already carries.
        self.assertFalse(os.path.exists(os.path.join(ws, ".claude", "agents")))
        import json
        with open(os.path.join(ws, ".claude", "settings.json")) as f:
            settings = json.load(f)
        # Claude Code matches file-permission rules on Edit() alone, and
        # Edit(path) already covers every file-editing tool. One rule per
        # fenced place, no dead tool names — a Write() rule earns a warning.
        deny = settings["permissions"]["deny"]
        self.assertEqual(deny, ["Edit(//%s/**)"
                                % os.path.join(os.path.abspath(ws), ".sandbox").lstrip("/"),
                                onboard.TRANSCRIPT_DENY])

    def test_init_writes_the_plugin_source_and_turns_it_on(self):
        """rule R14: this core's own tree is the marketplace, so the plugin is read
        from the tree it ships in and cannot point at a stale copy.

        The entry it replaced said `{"source": "command", …}`, which is a
        source a marketplace gives a PLUGIN and never a source a marketplace
        has: the host reads github, git, url, file, directory or settings
        there, dropped the entry, and the plugin never loaded.
        """
        import json
        from engine import onboard, vessel
        ws = tempfile.mkdtemp(prefix="sbx8-")
        ok, text = onboard.run(ws)
        self.assertTrue(ok, text)
        self.assertIn("plugin: sandbox-os", text)
        with open(os.path.join(ws, ".claude", "settings.json")) as f:
            settings = json.load(f)
        source = settings["extraKnownMarketplaces"]["sandbox"]["source"]
        self.assertEqual(source["source"], "directory")
        self.assertEqual(settings["enabledPlugins"], {"sandbox-os@sandbox": True})
        # the directory named is the tree this core runs from, and it carries
        # the marketplace file whose one plugin entry is the plugin's own dir
        market = os.path.join(source["path"], ".claude-plugin", "marketplace.json")
        self.assertTrue(os.path.exists(market), market)
        with open(market, encoding="utf-8") as f:
            entry = json.load(f)["plugins"][0]
        self.assertEqual(os.path.realpath(os.path.join(source["path"],
                                                       entry["source"])),
                         os.path.realpath(vessel.PLUGIN))

    def test_init_names_the_skill_copies_it_will_never_delete(self):
        """rule R13: the three skills ship in the plugin and the owner's copies
        retire — by his hand, because ~/.claude is his directory."""
        import os as _os
        from unittest import mock
        from engine import onboard
        ws = tempfile.mkdtemp(prefix="sbx8-")
        home = tempfile.mkdtemp(prefix="sbx8home-")
        _os.makedirs(_os.path.join(home, ".claude", "skills", "backlog-sync"))
        old = _os.environ.get("HOME")
        _os.environ["HOME"] = home
        try:
            _ok, text = onboard.run(ws)
        finally:
            if old is None:
                _os.environ.pop("HOME", None)
            else:
                _os.environ["HOME"] = old
        self.assertIn("backlog-sync", text)
        self.assertIn("rm -r ~/.claude/skills/NAME", text)
        # named, never removed
        self.assertTrue(_os.path.isdir(
            _os.path.join(home, ".claude", "skills", "backlog-sync")))

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


class TestHookPruning(unittest.TestCase):
    def test_the_8x_guard_wiring_is_pruned_and_foreign_hooks_stand(self):
        """8.x wired the guard from the workshop's own settings at an absolute
        path. The plugin's hooks.json wires it now, so the settings copy is a
        second wiring of a file this core no longer places — it goes, and a
        hook that is nobody's business here stays."""
        import json
        from engine import onboard
        ws = tempfile.mkdtemp(prefix="sbx8-")
        sp = os.path.join(ws, ".claude", "settings.json")
        os.makedirs(os.path.dirname(sp))
        old = {"matcher": "Edit|Write|Bash", "hooks": [{"type": "command",
               "command": 'python3 "%s/.sandbox/vessel/guard.py"' % ws}]}
        mine = {"matcher": "Bash", "hooks": [{"type": "command",
                "command": "echo hello"}]}
        with open(sp, "w") as f:
            json.dump({"hooks": {"PreToolUse": [old, mine]}}, f)
        ok, lines = onboard.emit_settings(ws)
        self.assertTrue(ok)
        self.assertTrue(any("pruned 1 hook" in l for l in lines), lines)
        with open(sp) as f:
            back = json.load(f)
        cmds = [hk["command"] for h in back["hooks"]["PreToolUse"] for hk in h["hooks"]]
        self.assertEqual(cmds, ["echo hello"])

    def test_the_last_placed_guard_hook_takes_the_empty_block_with_it(self):
        import json
        from engine import onboard
        ws = tempfile.mkdtemp(prefix="sbx8-")
        sp = os.path.join(ws, ".claude", "settings.json")
        os.makedirs(os.path.dirname(sp))
        with open(sp, "w") as f:
            json.dump({"hooks": {"PreToolUse": [
                {"matcher": "Edit", "hooks": [{"type": "command",
                 "command": 'python3 "%s/.sandbox/vessel/guard.py"' % ws}]}]}}, f)
        onboard.emit_settings(ws)
        with open(sp) as f:
            back = json.load(f)
        self.assertNotIn("hooks", back)

    def test_dead_deny_rules_pruned_foreign_ones_kept(self):
        """a workshop onboarded under the old floor carried a rule per write
        tool. Claude Code retired MultiEdit and matches file rules on Edit()
        alone, so three of the four became launch warnings. Re-init heals it.
        """
        import json
        from engine import onboard
        ws = tempfile.mkdtemp(prefix="sbx8-")
        sp = os.path.join(ws, ".claude", "settings.json")
        os.makedirs(os.path.dirname(sp))
        tail = onboard.deny_floor_target(ws)
        old = ["%s%s" % (t, tail)
               for t in ("Edit", "Write", "MultiEdit", "NotebookEdit")]
        keep = "Edit(//somewhere/else/**)"  # not ours — never swept
        with open(sp, "w") as f:
            json.dump({"permissions": {"deny": old + [keep]}}, f)
        ok, lines = onboard.emit_settings(ws)
        self.assertTrue(ok)
        self.assertTrue(any("pruned 3 dead deny rule" in l for l in lines))
        with open(sp) as f:
            deny = json.load(f)["permissions"]["deny"]
        self.assertEqual(sorted(deny),
                         sorted(onboard.deny_floor_rules(ws)
                                + [keep, onboard.TRANSCRIPT_DENY]))
