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
        for name in os.listdir(os.path.join(REPO, "docs")):
            text = open(os.path.join(REPO, "docs", name), encoding="utf-8").read().lower()
            for w in CUT:
                self.assertNotIn(w, text, "%s says %r" % (name, w))

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

    def test_the_lint_fires(self):
        self.assertNotEqual("stale block", selfmap.render_verbs().strip())


if __name__ == "__main__":
    unittest.main()
