# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""make: the diff is code's word; the summary waits behind the key."""
import os
import tempfile
import unittest

from engine import desk, journal, make, project


class TestMake(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self.root = project.root_of(self.ws, "geardoor")

    def test_open_build_close_computes_the_diff(self):
        ok, _ = make.open_session(self.ws, "geardoor", "add the tax table")
        self.assertTrue(ok)
        with open(os.path.join(self.root, "tax.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(self.root, "PROJECT.md"), "a") as f:
            f.write("\n")
        ok, msg = make.close_session(self.ws, "geardoor", "tax table added")
        self.assertTrue(ok)
        events, _ = journal.read(self.ws)
        close = [e for e in events if e.get("op") == "make" and e.get("phase") == "close"][0]
        self.assertIn("tax.json", close["diff"]["added"])
        self.assertIn("PROJECT.md", close["diff"]["changed"])
        pile, _ = desk.drafts(self.ws)
        self.assertTrue(any(d.get("cls") == "make-summary" and
                            d.get("receipt", "").startswith("journal:") for d in pile))

    def test_double_open_refused(self):
        make.open_session(self.ws, "geardoor", "one")
        ok, msg = make.open_session(self.ws, "geardoor", "two")
        self.assertFalse(ok)
        self.assertIn("already open", msg)

    def test_close_without_open_refused(self):
        ok, msg = make.close_session(self.ws, "geardoor")
        self.assertFalse(ok)

    def test_build_without_a_builder_hands_you_the_prompt(self):
        os.environ[make.CLAUDE_ENV] = "none"
        try:
            ok, msg = make.build(self.ws, "geardoor", "add the tax table")
        finally:
            del os.environ[make.CLAUDE_ENV]
        self.assertTrue(ok, msg)
        self.assertIn("PROMPT.md", msg)
        prompt = open(os.path.join(self.root, "PROMPT.md")).read()
        self.assertIn("add the tax table", prompt)

    def test_build_with_a_fake_builder_runs_and_closes(self):
        fake = os.path.join(tempfile.mkdtemp(prefix="sbx8f-"), "fakeclaude")
        with open(fake, "w") as f:
            f.write("#!/bin/sh\necho built the thing\nprintf 'x' > done.txt\n")
        os.chmod(fake, 0o755)
        os.environ[make.CLAUDE_ENV] = fake
        try:
            ok, msg = make.build(self.ws, "geardoor", "do the thing")
        finally:
            del os.environ[make.CLAUDE_ENV]
        self.assertTrue(ok, msg)
        self.assertIn("built the thing", msg)
        events, _ = journal.read(self.ws)
        close = [e for e in events if e.get("op") == "make" and e.get("phase") == "close"][-1]
        self.assertIn("done.txt", close["diff"]["added"])

    def test_no_summary_stages_nothing(self):
        make.open_session(self.ws, "geardoor", "quiet pass")
        make.close_session(self.ws, "geardoor")
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(pile, [])


if __name__ == "__main__":
    unittest.main()
