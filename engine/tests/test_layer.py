# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the instruction layer, tested like code.

Every file a workshop's Claude reads ships from this repo. These tests hold
the layer's mechanical promises: budgets, no banned words, no dead paths,
every seat pinned, placed copies byte-identical, soul never placed. The
prose promises (a page reads right) stay the owner's cold read — a green
run here says nothing about those, on purpose.
"""
import json
import os
import re
import tempfile
import unittest

from engine import onboard, voicelint

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _vessel(*parts):
    return os.path.join(REPO, "vessel", *parts)


def _shipped_instruction_files():
    """the files a workshop's Claude actually reads, derived from the manifest
    rather than a second hand-typed list: the one file init places, plus the
    briefs and the style the plugin loads into every session. The three skills
    have their own two checks in test_plugin_payload, where the ceiling they
    are held to is the skills' own."""
    from engine import vessel
    ws = tempfile.mkdtemp(prefix="layer-")
    out = set(onboard.shipped_payload(ws).values())
    ships = vessel.payload()
    out |= {os.path.join(ships["root"], rel) for rel in ships["ships"]
            if rel.endswith(".md")
            and rel.startswith(("agents/", "output-styles/"))}
    return sorted(out)


class TestLayerPlacement(unittest.TestCase):
    def test_the_crew_ships_in_the_plugin_and_init_places_none_of_it(self):
        """9.0: the six briefs are loaded from the plugin, so nothing copies
        them into a workshop where a second version could go stale."""
        from engine import vessel
        ws = tempfile.mkdtemp(prefix="layer-")
        ships = vessel.payload()["ships"]
        briefs = [r for r in ships if r.startswith("agents/")]
        self.assertEqual(sorted(briefs),
                         sorted("agents/" + n for n in
                                os.listdir(_vessel("plugin", "agents"))))
        self.assertEqual(len(briefs), 6)
        placed = onboard.shipped_payload(ws)
        self.assertEqual([os.path.basename(d) for d in placed], ["CLAUDE.md"])
        for dest in placed:
            self.assertNotIn(os.sep + "agents" + os.sep, dest)

    def test_init_leaves_no_second_copy_of_what_the_plugin_serves(self):
        ws = tempfile.mkdtemp(prefix="layer-")
        onboard.run(ws)
        for gone in (os.path.join(ws, ".claude", "agents"),
                     os.path.join(ws, ".claude", "output-styles"),
                     os.path.join(ws, ".sandbox", "vessel")):
            self.assertFalse(os.path.exists(gone), gone)

    def test_soul_never_lands_in_a_workshop(self):
        ws = tempfile.mkdtemp(prefix="layer-")
        ok, _ = onboard.run(ws)
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(os.path.join(ws, "soul")))
        for dest, src in onboard.shipped_payload(ws).items():
            self.assertNotIn(os.sep + "soul" + os.sep, dest)
            self.assertNotIn(os.sep + "soul" + os.sep, src)


class TestLayerBudget(unittest.TestCase):
    CEILINGS = {
        _vessel("claude-code", "CLAUDE.md"): 90,
        _vessel("plugin", "output-styles", "across-the-desk.md"): 65,
    }
    BRIEF_CEILING = 90
    BRIEF_EXCEPTIONS = {"producer.md": 115}

    def test_charter_and_style_within_budget(self):
        for path, ceiling in self.CEILINGS.items():
            n = len(open(path, encoding="utf-8").read().splitlines())
            self.assertLessEqual(n, ceiling, "%s is %d lines (ceiling %d)"
                                 % (os.path.relpath(path, REPO), n, ceiling))

    def test_briefs_within_budget(self):
        adir = _vessel("plugin", "agents")
        for name in sorted(os.listdir(adir)):
            ceiling = self.BRIEF_EXCEPTIONS.get(name, self.BRIEF_CEILING)
            n = len(open(os.path.join(adir, name), encoding="utf-8").read().splitlines())
            self.assertLessEqual(n, ceiling, "%s is %d lines (ceiling %d)"
                                 % (name, n, ceiling))


class TestLayerBanned(unittest.TestCase):
    """the list comes from soul/voice.md, parsed — never a second tuple here."""

    def test_no_banned_word_in_shipped_text(self):
        phrases = voicelint.forbidden_phrases()
        self.assertGreaterEqual(len([p for p in phrases if p.scope == "all"]), 23)
        for path in _shipped_instruction_files():
            if path.endswith("guard.py"):
                continue
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            text = voicelint.blanked(
                open(path, encoding="utf-8").read(), rel, "forbidden")
            for lineno, phrase, _ in voicelint.phrase_hits(text, phrases):
                self.fail("%s:%d says %r" % (rel, lineno, phrase))


class TestPluginDescription(unittest.TestCase):
    """one description, in two files a stranger meets in the picker."""

    def _market(self):
        with open(os.path.join(REPO, ".claude-plugin", "marketplace.json"),
                  encoding="utf-8") as f:
            return json.load(f)

    def test_marketplace_matches_the_plugin(self):
        market = json.load(open(os.path.join(REPO, ".claude-plugin",
                                             "marketplace.json"), encoding="utf-8"))
        plugin = json.load(open(_vessel("plugin", ".claude-plugin", "plugin.json"),
                                encoding="utf-8"))
        entries = [p for p in market["plugins"] if p["name"] == plugin["name"]]
        self.assertEqual(len(entries), 1, market["plugins"])
        self.assertEqual(entries[0]["description"], plugin["description"],
                         "the two descriptions drifted; one voice, one sentence")

    def test_the_marketplace_names_itself_the_way_the_settings_file_does(self):
        """`enabledPlugins` files the plugin under `<plugin>@<marketplace>`,
        and the marketplace half is the key init writes into
        extraKnownMarketplaces. one name, so the two cannot disagree."""
        from engine import onboard
        market = self._market()
        self.assertEqual(market["name"], onboard.MARKETPLACE)
        self.assertEqual(onboard.plugin_key(),
                         "%s@%s" % (market["plugins"][0]["name"], market["name"]))

    def test_the_plugin_entry_points_at_the_plugin_in_this_tree(self):
        """the source is a path relative to the marketplace, and the
        marketplace is this core's own root — so the plugin follows the tree
        and no absolute path is written down twice."""
        from engine import onboard, vessel
        source = self._market()["plugins"][0]["source"]
        self.assertIsInstance(source, str, source)
        self.assertEqual(os.path.realpath(os.path.join(REPO, source)),
                         os.path.realpath(vessel.PLUGIN))
        self.assertEqual(os.path.realpath(onboard.marketplace_source()["path"]),
                         os.path.realpath(REPO))


class TestLayerDeadPath(unittest.TestCase):
    # Created later by `sandbox project new`, not by init — absence right
    # after a bare init is not a defect. Hand-picked; grows by hand.
    ALLOW = {"CANON.md", "PROJECT.md", "projects/"}
    # Retired organs, named so they cannot come back by hand. The catalog
    # reader went out in 9.0: the shelf's own marketplace file is the index,
    # the host does the pinning, and `shelf.verify_entry` is the one check
    # a build and an app both run (shelf.md check 6).
    GONE = {"engine/catalog.py"}
    TOKEN = re.compile(r"`([^`\n]+)`")

    def _looks_like_path(self, t):
        if t.startswith("sandbox ") or t.startswith("--"):
            return False
        return ("/" in t or t.startswith("~")
                or t.endswith((".md", ".py", ".json", ".txt")))

    def test_a_retired_organ_stays_retired(self):
        for rel in sorted(self.GONE):
            self.assertFalse(os.path.exists(os.path.join(REPO, rel)),
                             "%s came back; it retired in 9.0" % rel)
        for path in _shipped_instruction_files():
            text = open(path, encoding="utf-8").read()
            for rel in self.GONE:
                self.assertNotIn(rel, text, "%s names %s"
                                 % (os.path.relpath(path, REPO), rel))

    def test_no_dead_path_in_shipped_text(self):
        ws = tempfile.mkdtemp(prefix="layer-")
        onboard.run(ws)
        hits = []
        for path in _shipped_instruction_files():
            if path.endswith("guard.py"):
                continue
            for t in self.TOKEN.findall(open(path, encoding="utf-8").read()):
                t = t.strip()
                if not self._looks_like_path(t) or t in self.ALLOW:
                    continue
                cand = t.replace("~", os.path.expanduser("~"))
                if os.path.isabs(cand):
                    ok = os.path.exists(cand)
                else:
                    ok = (os.path.exists(os.path.join(REPO, t))
                          or os.path.exists(os.path.join(ws, t)))
                if not ok:
                    hits.append("%s -> %s" % (os.path.relpath(path, REPO), t))
        self.assertEqual(hits, [])


class TestLayerFrontmatter(unittest.TestCase):
    def test_every_agent_has_model_and_effort(self):
        adir = _vessel("plugin", "agents")
        for name in sorted(os.listdir(adir)):
            text = open(os.path.join(adir, name), encoding="utf-8").read()
            front = text.split("---", 2)[1]
            keys = dict(line.split(":", 1) for line in front.strip().splitlines()
                        if ":" in line)
            self.assertIn("model", keys, name)
            self.assertIn("effort", keys, name)
            self.assertIn(keys["model"].strip(), ("sonnet", "opus"), name)
            for dead in ("disallowedTools", "memory", "skills"):
                self.assertNotIn(dead, keys, "%s declares %s" % (name, dead))


class TestHandCarriedVersions(unittest.TestCase):
    """a hand-typed number rots exactly like the verb table used to.
    OPEN.md's header and the plugin manifest both carry the version by hand;
    this pins them to VERSION so the release commit must move all three."""

    def test_open_md_header_equals_version(self):
        v = open(os.path.join(REPO, "VERSION"), encoding="utf-8").read().strip()
        head = open(os.path.join(REPO, "docs", "OPEN.md"), encoding="utf-8").read(200)
        self.assertIn(v, head, "docs/OPEN.md header drifted from VERSION %s" % v)

    def test_plugin_manifest_equals_version(self):
        import json
        v = open(os.path.join(REPO, "VERSION"), encoding="utf-8").read().strip()
        p = json.load(open(_vessel("plugin", ".claude-plugin", "plugin.json"),
                           encoding="utf-8"))
        self.assertEqual(p.get("version"), v)
