# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""share/fetch: the scrub gates the way out; the hash gates the way in."""
import os
import tempfile
import unittest

from engine import gate, journal, share, shelf


def key():
    return gate.mint_consent(is_real_tty=True, keychar="k")


class TestShare(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        src = os.path.join(tempfile.mkdtemp(prefix="sbx8s-"), "tokens.css")
        open(src, "w").write(":root {}\n")
        shelf.save(self.ws, src)
        self.staging = tempfile.mkdtemp(prefix="sbx8st-")

    def test_clean_build_stages_with_honest_notes(self):
        ok, msg = share.share(self.ws, "tokens.css", self.staging)
        self.assertTrue(ok, msg)
        self.assertIn("the push is your hand", msg)
        self.assertIn("only the floor scrub ran", msg)
        self.assertTrue(os.path.exists(
            os.path.join(self.staging, "builds", "tokens.css", "BUILD.md")))

    def test_person_data_refuses_the_share(self):
        leak = os.path.join(self.ws, "shelf", "tokens.css", "notes.md")
        open(leak, "w").write("built at /" + "Users" + "/someone\n")
        ok, msg = share.share(self.ws, "tokens.css", self.staging)
        self.assertFalse(ok)
        self.assertIn("scrub refused", msg)

    def test_no_git_rides_the_staging(self):
        import subprocess
        bdir = os.path.join(self.ws, "shelf", "tokens.css")
        subprocess.run(["git", "init", "--quiet", bdir], check=True)
        ok, msg = share.share(self.ws, "tokens.css", self.staging)
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(
            os.path.join(self.staging, "builds", "tokens.css", ".git")))


class TestFetch(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        # A second workshop shares a build; ours fetches it.
        self.other = tempfile.mkdtemp(prefix="sbx8o-")
        journal.ensure_genesis(self.other)
        src = os.path.join(tempfile.mkdtemp(prefix="sbx8s-"), "kit.md")
        open(src, "w").write("a shared kit\n")
        shelf.save(self.other, src)
        self.source = tempfile.mkdtemp(prefix="sbx8src-")
        share.share(self.other, "kit.md", self.source)

    def test_fetch_lists_verifies_and_needs_the_key(self):
        self.assertEqual(share.list_source(self.source), ["kit.md"])
        ok, msg = share.fetch(self.ws, self.source, "kit.md", None)
        self.assertFalse(ok)
        self.assertIn("UNVERIFIED", msg)
        self.assertIn("real terminal", msg)
        ok, msg = share.fetch(self.ws, self.source, "kit.md", key())
        self.assertTrue(ok)
        c = shelf.card(self.ws, "kit.md")
        self.assertEqual(c["origin"], "external")  # provenance never launders

    def test_tampered_bytes_never_fetch(self):
        payload = os.path.join(self.source, "builds", "kit.md", "kit.md")
        open(payload, "a").write("tampered\n")
        ok, msg = share.fetch(self.ws, self.source, "kit.md", key())
        self.assertFalse(ok)
        self.assertIn("do not match the card", msg)
        self.assertIsNone(shelf.card(self.ws, "kit.md"))


if __name__ == "__main__":
    unittest.main()
