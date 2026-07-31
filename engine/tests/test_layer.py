# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The instruction layer, tested like code.

Every file a workshop's Claude reads ships from this repo. These tests hold
the layer's mechanical promises: budgets, no banned words, no dead paths,
every seat pinned, placed copies byte-identical, soul never placed. The
prose promises (a page reads right) stay the owner's cold read — a green
run here says nothing about those, on purpose.
"""
import os
import re
import tempfile
import unittest

from engine import onboard
from engine.tests.test_voice import CUT, TestVoice

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _vessel(*parts):
    return os.path.join(REPO, "vessel", *parts)


def _shipped_instruction_files():
    """The files a workshop's Claude actually reads, derived from the same
    payload init places — never a second hand-typed list."""
    ws = tempfile.mkdtemp(prefix="layer-")
    return sorted(set(onboard.shipped_payload(ws).values()))


class TestLayerPlacement(unittest.TestCase):
    def test_agent_count_is_whatever_vessel_ships(self):
        ws = tempfile.mkdtemp(prefix="layer-")
        payload = onboard.shipped_payload(ws)
        shipped = [s for s in payload.values() if os.sep + "agents" + os.sep in s]
        on_disk = [n for n in os.listdir(_vessel("claude-code", "agents"))]
        self.assertEqual(len(shipped), len(on_disk))

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
        _vessel("claude-code", "CLAUDE.md"): 60,
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
        adir = _vessel("claude-code", "agents")
        for name in sorted(os.listdir(adir)):
            ceiling = self.BRIEF_EXCEPTIONS.get(name, self.BRIEF_CEILING)
            n = len(open(os.path.join(adir, name), encoding="utf-8").read().splitlines())
            self.assertLessEqual(n, ceiling, "%s is %d lines (ceiling %d)"
                                 % (name, n, ceiling))


class TestLayerBanned(unittest.TestCase):
    def test_no_banned_word_in_shipped_text(self):
        exempt = {os.path.join(REPO, p) for p in TestVoice.EXEMPT}
        for path in _shipped_instruction_files():
            if path in exempt or path.endswith("guard.py"):
                continue
            text = open(path, encoding="utf-8").read().lower()
            for w in CUT:
                self.assertNotIn(w, text, "%s says %r"
                                 % (os.path.relpath(path, REPO), w))


class TestLayerDeadPath(unittest.TestCase):
    # Created later by `sandbox project new`, not by init — absence right
    # after a bare init is not a defect. Hand-picked; grows by hand.
    ALLOW = {"CANON.md", "PROJECT.md", "projects/"}
    TOKEN = re.compile(r"`([^`\n]+)`")

    def _looks_like_path(self, t):
        if t.startswith("sandbox ") or t.startswith("--"):
            return False
        return ("/" in t or t.startswith("~")
                or t.endswith((".md", ".py", ".json", ".txt")))

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
        adir = _vessel("claude-code", "agents")
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
    """A hand-typed number rots exactly like the verb table used to.
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
