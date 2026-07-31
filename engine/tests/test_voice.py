# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The voice lint: the cut-list bites every string the engine speaks, and
the living page keeps its promises."""
import os
import re
import tempfile
import unittest

from engine import journal, page, project
from engine.tests import REPO

# Law 15's cut-list — the discovery format's closed banned list, minus
# "harness" (this repo's honest name for Claude Code, the named exception).
CUT = ("seamless", "seamlessly", "effortless", "effortlessly", "robust",
       "leverage", "empower", "unlock", "elevate", "cutting-edge",
       "game-changing", "revolutionary", "delve", "unleash", "supercharge",
       "foster", "realm", "tapestry", "comprehensive", "ultimately",
       "it's worth noting", "in essence", "at its core", "simply put")


class TestVoice(unittest.TestCase):
    # The one exemption: the ban itself names the banned words.
    EXEMPT = (os.path.join("vessel", "plugin", "output-styles", "across-the-desk.md"),
              os.path.join("vessel", "claude-code", "agents", "voicer.md"))

    def test_no_cut_word_in_any_engine_or_vessel_file(self):
        hits = []
        for base in ("engine", "vessel"):
            for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, base)):
                dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tests")]
                for name in filenames:
                    path = os.path.join(dirpath, name)
                    if os.path.relpath(path, REPO) in self.EXEMPT:
                        continue
                    try:
                        text = open(path, encoding="utf-8").read().lower()
                    except (UnicodeDecodeError, OSError):
                        continue
                    for w in CUT:
                        if re.search(r"\b" + w + r"\b", text):
                            hits.append("%s: %s" % (os.path.relpath(path, REPO), w))
        self.assertEqual(hits, [], hits)

    def test_the_lint_fires(self):
        self.assertTrue(re.search(r"\bdelve\b", "let us delve into this"))


class TestPage(unittest.TestCase):
    def test_page_renders_self_contained_with_asof(self):
        ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(ws)
        project.new(ws, "geardoor", "the store")
        out = page.render(ws)
        text = open(out, encoding="utf-8").read()
        self.assertIn("geardoor", text)
        self.assertIn("as of", text)
        self.assertIn("nothing needs you.", text)
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)  # asks the network for nothing

    def test_page_escapes_what_it_renders(self):
        ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(ws)
        project.new(ws, "xss", "<script>alert(1)</script>")
        text = open(page.render(ws), encoding="utf-8").read()
        self.assertNotIn("<script>alert", text)


if __name__ == "__main__":
    unittest.main()
