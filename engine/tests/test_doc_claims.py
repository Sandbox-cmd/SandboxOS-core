# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The doc lint: generated blocks match the source; no hand-carried facts."""
import os
import re
import unittest

from engine import selfmap, verbs
from engine.tests import REPO


class TestDocClaims(unittest.TestCase):
    def test_manual_verb_block_matches_the_source(self):
        self.assertEqual(selfmap.current_block(), selfmap.render_verbs().strip(),
                         "MANUAL.md's verb table drifted — run: python3 -m engine.selfmap --write")

    def test_every_verb_appears_in_the_manual(self):
        text = open(selfmap.manual_path(), encoding="utf-8").read()
        for name in verbs.TABLE:
            self.assertIn("`%s`" % name, text, name)

    def test_docs_speak_no_cut_words(self):
        from engine.tests.test_voice import CUT
        pages = [os.path.join(REPO, "docs", n)
                 for n in os.listdir(os.path.join(REPO, "docs"))]
        pages.append(os.path.join(REPO, "README.md"))  # root-level, same voice
        for path in pages:
            text = open(path, encoding="utf-8").read().lower()
            for w in CUT:
                self.assertNotIn(w, text,
                                 "%s says %r" % (os.path.relpath(path, REPO), w))

    def test_version_is_read_not_written(self):
        """The version appears in VERSION and CHANGELOG (its birthplace) and
        OPEN.md's header — nowhere else in prose."""
        version = open(os.path.join(REPO, "VERSION")).read().strip()
        allowed = {"CHANGELOG.md", "VERSION", "manifest.json"}
        for name in ("README.md",) + tuple(
                os.path.join("docs", n) for n in os.listdir(os.path.join(REPO, "docs"))):
            if os.path.basename(name) in allowed or os.path.basename(name) == "OPEN.md":
                continue
            text = open(os.path.join(REPO, name), encoding="utf-8").read()
            self.assertNotIn(version, text,
                             "%s hand-carries the version — name the command instead" % name)

    def test_readme_points_at_the_real_repo(self):
        text = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
        self.assertIn("Sandbox-cmd/SandboxOS-core", text)

    def test_readme_line_citations_resolve(self):
        """The page cites source by file and line; the cited line must say it.

        A README that points at `engine/ship.py`, line 45 is making a claim a
        stranger will check. When the source moves, this fails here instead of
        lying there.
        """
        text = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
        cites = re.findall(r"`(engine/[a-z_]+\.py)`, line (\d+)", text)
        self.assertTrue(cites, "no line citations found — did the page stop citing source?")
        for rel, lineno in cites:
            lines = open(os.path.join(REPO, rel), encoding="utf-8").read().splitlines()
            n = int(lineno)
            self.assertLessEqual(n, len(lines), "%s has no line %d" % (rel, n))
            self.assertTrue(lines[n - 1].lstrip().startswith("return"),
                            "%s:%d is not the refusal the README says it is" % (rel, n))

    def test_readme_loud_line_is_true(self):
        """The page's one loud line says a pipe cannot approve. Prove it.

        Cited behaviour, not a cited line number — this is the claim a stranger
        is most likely to actually try.
        """
        from engine import desk
        text = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
        self.assertIn("A PIPE CANNOT APPROVE ANYTHING", text,
                      "the loud line changed — re-point this pin at whatever replaced it")
        for consent in (None, {}, {"source": "pipe", "key": "k"}, {"source": "tty", "key": "x"}):
            n, msg = desk.land_all(REPO, consent)
            self.assertEqual(0, n, "land_all landed %d without a real key" % n)
            self.assertIn("real terminal", msg)

    def test_readme_install_block_obeys_its_three_laws(self):
        """The install gate: the bill is named before the clone, and the block
        ends in the health check. The website byte-locks this block, so drift
        here breaks two surfaces."""
        lines = open(os.path.join(REPO, "README.md"), encoding="utf-8").read().splitlines()
        clone = next(i for i, l in enumerate(lines) if l.startswith("git clone"))
        caveat = next((i for i, l in enumerate(lines) if "claude" in l.lower()), None)
        self.assertIsNotNone(caveat, "the README never names the one paid command")
        self.assertLess(caveat, clone,
                        "the paid-command caveat sits below the clone line — "
                        "a stranger types before they learn the bill")
        end = next(i for i, l in enumerate(lines[clone:], clone) if l.startswith("```"))
        self.assertIn("./sandbox doctor", lines[end - 1],
                      "the install block must end in the health check, with the ./")

    def test_the_lint_fires(self):
        self.assertNotEqual("stale block", selfmap.render_verbs().strip())


if __name__ == "__main__":
    unittest.main()
