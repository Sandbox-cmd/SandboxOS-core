# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""soul/, held to its own promises.

Five files, each wearing its lineage; every organ path real; the anchors on
one page and no other; every conviction carried by at least one projection
that exists. What no test here can prove: that a projection's prose agrees
with its parent — that stays the owner's cold read, said in soul/values.md
itself rather than pretended away.
"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOUL = os.path.join(REPO, "soul")
FILES = ("ground-truth.md", "values.md", "voice.md", "partner.md", "lineage.md")
ANCHORS = ("54:17", "96:6-7", "33:72", "21:22", "55:7-9",
           "2:222", "47:24", "61:2-3", "4:135", "21:47")


class TestSoul(unittest.TestCase):
    def test_five_files_each_wearing_lineage(self):
        for name in FILES:
            p = os.path.join(SOUL, name)
            self.assertTrue(os.path.exists(p), name)
            head = open(p, encoding="utf-8").read(600)
            self.assertIn("lineage:", head, "%s carries no lineage line" % name)

    def test_every_organ_path_is_real(self):
        token = re.compile(r"`((?:engine|law|vessel|docs)/[^`\n]+)`")
        hits = []
        for name in FILES:
            text = open(os.path.join(SOUL, name), encoding="utf-8").read()
            for t in token.findall(text):
                if not os.path.exists(os.path.join(REPO, t.strip())):
                    hits.append("%s -> %s" % (name, t))
        self.assertEqual(hits, [], "dead organ paths: %s" % hits)

    def test_anchors_stay_home(self):
        home = os.path.join(SOUL, "ground-truth.md")
        home_text = open(home, encoding="utf-8").read()
        for a in ANCHORS:
            self.assertIn(a, home_text, "anchor %s missing from its one page" % a)
        for base in ("engine", "vessel", "law", "docs", "soul"):
            for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, base)):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for n in filenames:
                    p = os.path.join(dirpath, n)
                    if p == home or not n.endswith(".md"):
                        continue
                    text = open(p, encoding="utf-8").read()
                    for a in ANCHORS:
                        self.assertNotIn(a, text,
                                         "anchor %s escaped to %s"
                                         % (a, os.path.relpath(p, REPO)))

    def test_every_conviction_named_and_carried(self):
        text = open(os.path.join(SOUL, "values.md"), encoding="utf-8").read()
        convictions = re.findall(r"^\d+\. \*\*(.+?)\.\*\*", text, re.M)
        self.assertEqual(len(convictions), 7, convictions)
        for block in re.split(r"^\d+\. ", text, flags=re.M)[1:8]:
            self.assertIn("parents:", block)
            self.assertIn("organ:", block)
        # the projection map: every path exists, every conviction carried
        map_rows = re.findall(r"^\| `([^`]+)` .*\| (.+) \|$", text, re.M)
        self.assertTrue(map_rows, "the projection map parsed to nothing")
        for path, _ in map_rows:
            first = path.split("`")[0].strip()
            self.assertTrue(os.path.exists(os.path.join(REPO, first)),
                            "projection map names a ghost: %s" % first)
        carried = " ".join(c for _, c in map_rows)
        for i in ("1", "2", "3", "4", "5", "6", "7"):
            self.assertIn(i, carried, "conviction %s is carried by nothing" % i)

    def test_the_lint_fires(self):
        # a green result must mean something: a deliberately broken claim is caught
        token = re.compile(r"`((?:engine|law|vessel|docs)/[^`\n]+)`")
        fake = "the organ is `engine/does-not-exist.py` here"
        found = token.findall(fake)
        self.assertTrue(found and not os.path.exists(os.path.join(REPO, found[0])))
