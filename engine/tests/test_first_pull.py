# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the first pull, watched from the only end this machine can watch.

J20 asks whether a build ever really landed on someone else. There is no
network here and no reading a friend's record, so the watcher reads two
things the owner's own workshop holds: the `build-shared` events it minted,
and the note the owner stages when a friend tells them — a human
confirmation, named as one (cold-read F21).
"""
import os
import subprocess
import tempfile
import unittest

from engine import journal, notes, share, shelf

from . import REPO, pressing


def run_cli(*args, **kw):
    env = dict(os.environ)
    if kw.get("home"):
        env["SANDBOX_HOME"] = kw["home"]
    env.pop("SANDBOX_TEST_KEY", None)
    return subprocess.run([os.path.join(REPO, "sandbox"), *args], input="",
                          capture_output=True, text=True, timeout=60, env=env)


NAG = ('shared 1, no pull witnessed yet — stage one: '
       'sandbox note "pull-witnessed: WHO BUILD"')


class TestFirstPull(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9pull-")
        journal.ensure_genesis(self.ws)
        src = os.path.join(tempfile.mkdtemp(prefix="sbx9src-"), "kit.md")
        with open(src, "w") as f:
            f.write("a shared kit\n")
        shelf.save(self.ws, src)

    def witness(self, body):
        notes.note(self.ws, body)
        with pressing("k"):
            notes.approve(self.ws, out=lambda *_a: None)

    def test_a_shelf_that_never_shared_nags_about_nothing(self):
        got = shelf.first_pull(self.ws)
        self.assertEqual(got["shared"], [])
        self.assertEqual(got["witnessed"], [])

    def test_a_share_with_no_witness_is_the_unproven_state(self):
        share.share(self.ws, "kit.md", tempfile.mkdtemp(prefix="sbx9st-"))
        got = shelf.first_pull(self.ws)
        self.assertEqual(got["shared"], ["kit.md"])
        self.assertEqual(got["witnessed"], [])

    def test_the_owner_staged_note_is_what_closes_it(self):
        """the note lands like any other line: staged, shown, and landed on
        the owner's k. Nothing here reads the friend's machine."""
        share.share(self.ws, "kit.md", tempfile.mkdtemp(prefix="sbx9st-"))
        self.witness("pull-witnessed: dana kit.md")
        got = shelf.first_pull(self.ws)
        self.assertEqual(got["shared"], ["kit.md"])
        self.assertEqual(got["witnessed"], ["pull-witnessed: dana kit.md"])

    def test_a_note_that_only_mentions_a_pull_does_not_count(self):
        share.share(self.ws, "kit.md", tempfile.mkdtemp(prefix="sbx9st-"))
        self.witness("dana said she pull-witnessed: it, i think")
        self.assertEqual(shelf.first_pull(self.ws)["witnessed"], [])

    def test_a_draft_that_never_landed_does_not_count(self):
        """the record is what landed; a waiting draft has not happened yet."""
        share.share(self.ws, "kit.md", tempfile.mkdtemp(prefix="sbx9st-"))
        notes.note(self.ws, "pull-witnessed: dana kit.md")
        self.assertEqual(shelf.first_pull(self.ws)["witnessed"], [])

    def test_builds_prints_the_nag_until_a_witness_lands(self):
        share.share(self.ws, "kit.md", tempfile.mkdtemp(prefix="sbx9st-"))
        got = run_cli("builds", home=self.ws)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertIn(NAG, got.stdout)
        self.witness("pull-witnessed: dana kit.md")
        got = run_cli("builds", home=self.ws)
        self.assertNotIn("no pull witnessed yet", got.stdout)

    def test_builds_says_nothing_about_pulls_before_a_share(self):
        got = run_cli("builds", home=self.ws)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertNotIn("no pull witnessed yet", got.stdout)


if __name__ == "__main__":
    unittest.main()
