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
FILES = ("ground-truth.md", "values.md", "voice.md", "partner.md",
         "lineage.md", "surfaces.md")
ANCHORS = ("54:17", "96:6-7", "33:72", "21:22", "55:7-9",
           "2:222", "47:24", "61:2-3", "4:135", "21:47")


def projection_map():
    """values.md's map, columns read by name (repair B4).

    every row opens with one backticked path; a row that does not is a parse
    error, said out loud rather than skipped in silence.
    """
    with open(os.path.join(SOUL, "values.md"), encoding="utf-8") as fh:
        text = fh.read()
    header, rows = None, []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        if header is None:
            if "projection" not in cells:
                continue          # an earlier table on the page
            header = cells
            continue
        row = dict(zip(header, cells))
        m = re.match(r"`([^`]+)`", row.get("projection", ""))
        if not m:
            raise ValueError("a projection row opens with no backticked path: %s"
                             % line[:60])
        row["path"] = m.group(1).strip()
        row["carries"] = row.get("carries", "")
        row["held by"] = row.get("held by", "")
        rows.append(row)
    return rows


# the check kinds the map is allowed to cite, and the test that holds each.
# a kind with None is cited and not yet built; the coverage line says so and
# the number is allowed to be low, because it is honest.
KIND_TESTS = {
    "budget": "engine.tests.test_layer.TestLayerBudget."
              "test_charter_and_style_within_budget",
    "dead-path": "engine.tests.test_layer.TestLayerDeadPath."
                 "test_no_dead_path_in_shipped_text",
    "forbidden phrases": "engine.tests.test_voice.TestForbiddenPhrases."
                         "test_no_forbidden_phrase_in_any_text",
    "negation ceiling": "engine.tests.test_voice.TestNegation."
                        "test_negation_density_reported",
    "lint-string": "engine.tests.test_voice.TestLintString."
                   "test_every_mapped_row_is_a_row_of_the_page",
    "the two descriptions pinned equal":
        "engine.tests.test_layer.TestPluginDescription."
        "test_marketplace_matches_the_plugin",
    "lowercase-first": None,      # docs-stranger check 6 builds it
    "pins": None,                 # per-seat pins land with C7
    '"i" present': None,          # lands with C4's first-person lines
    "`## output` held to its surfaces row": None,   # lands with C4
}


class TestSoul(unittest.TestCase):
    def test_six_files_each_wearing_lineage(self):
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
        with open(os.path.join(SOUL, "values.md"), encoding="utf-8") as fh:
            text = fh.read()
        convictions = re.findall(r"^\d+\. \*\*(.+?)\.\*\*", text, re.M)
        self.assertEqual(len(convictions), 7, convictions)
        for block in re.split(r"^\d+\. ", text, flags=re.M)[1:8]:
            self.assertIn("parents:", block)
            self.assertIn("organ:", block)
        # the projection map: every path exists, every conviction carried.
        # repair B4: the columns are read by name. the first draft read them by
        # position and captured `held by` as `carries`, which went red the day
        # the third column landed.
        rows = projection_map()
        self.assertTrue(rows, "the projection map parsed to nothing")
        for row in rows:
            self.assertTrue(os.path.exists(os.path.join(REPO, row["path"])),
                            "projection map names a ghost: %s" % row["path"])
        carried = " ".join(row["carries"] for row in rows)
        for i in ("1", "2", "3", "4", "5", "6", "7"):
            self.assertIn(i, carried, "conviction %s is carried by nothing" % i)

    def test_the_lint_fires(self):
        # a green result must mean something: a claim broken on purpose is caught
        token = re.compile(r"`((?:engine|law|vessel|docs)/[^`\n]+)`")
        fake = "the organ is `engine/does-not-exist.py` here"
        found = token.findall(fake)
        self.assertTrue(found and not os.path.exists(os.path.join(REPO, found[0])))


class TestCoverageManifest(unittest.TestCase):
    """the map says who holds each row, and the number it prints is honest."""

    def test_coverage_manifest_prints(self):
        rows = projection_map()
        by_check, prose, cited = [], [], set()
        for row in rows:
            held = row["held by"]
            if held.startswith("check:"):
                by_check.append(row["path"])
                kinds = [k for k in KIND_TESTS if k in held]
                self.assertTrue(kinds, "%s cites no check kind this suite knows: %s"
                                % (row["path"], held))
                cited.update(kinds)
            else:
                prose.append(row["path"])
        built = [k for k in cited if KIND_TESTS[k]]
        print("coverage: %d of %d projections held by a check, %d prose-only; "
              "%d of %d cited check kinds are built"
              % (len(by_check), len(rows), len(prose), len(built), len(cited)))
        self.assertEqual(len(by_check) + len(prose), len(rows))

    def test_no_row_cites_a_test_that_was_renamed_away(self):
        """the vale-ms rule: a citation the loader cannot resolve is a ghost."""
        loader = unittest.TestLoader()
        for kind, dotted in sorted(KIND_TESTS.items()):
            if not dotted:
                continue
            suite = loader.loadTestsFromName(dotted)
            found = list(suite)
            self.assertEqual(len(found), 1, "%s: %s resolves to %d test(s)"
                             % (kind, dotted, len(found)))
            self.assertNotIn("_FailedTest", type(found[0]).__name__,
                             "%s cites a ghost: %s" % (kind, dotted))


class TestSoulCommits(unittest.TestCase):
    """a soul change names what it re-read, or says `none` out loud."""

    def _git(self, *args):
        import subprocess
        return subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                              text=True, timeout=20)

    def test_soul_commits_name_their_projections(self):
        import shutil
        if not shutil.which("git") or not os.path.isdir(os.path.join(REPO, ".git")):
            print("soul commits: skipped — no git here (a shipped copy has none)")
            return
        tag = self._git("describe", "--tags", "--abbrev=0")
        span = "%s..HEAD" % tag.stdout.strip() if tag.returncode == 0 else "HEAD"
        log = self._git("log", "--format=%H%n%B%n--8<--", span, "--", "soul/")
        if log.returncode != 0:
            print("soul commits: skipped — git could not read the log")
            return
        paths = {row["path"] for row in projection_map()}
        commits = [c for c in log.stdout.split("--8<--") if c.strip()]
        for c in commits:
            body = c.strip()
            head = body.splitlines()[0][:8]
            named = [l for l in body.splitlines() if l.strip().startswith("soul:")]
            self.assertTrue(named, "%s touched soul/ and named no projection; "
                            "a `soul:` line says what was re-read, or `none`" % head)
            said = " ".join(named)
            self.assertTrue("none" in said or any(p in said for p in paths),
                            "%s says %r, which names no projection on the map"
                            % (head, said.strip()))
        print("soul commits: %d since %s, each naming its projections"
              % (len(commits), span.split("..")[0]))
