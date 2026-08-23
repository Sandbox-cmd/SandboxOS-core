# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""share/fetch: the way out strips, the way in checks.

The 8.2.3 shape refused a build whose card carried the owner's home path,
which is every build a stock `~/Sandbox` ever pressed — the suite could not
catch it because the suite ran under a temp dir. Here the workshop is built
with a floor needle IN ITS OWN PATH, so a card that carried an absolute path
would fail these tests the way the real workshop failed.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

from engine import clean, gate, journal, share, shelf

from . import key

FLOOR = clean.FLOOR[0]          # the needle, assembled — never typed here
HAS_MINISIGN = shutil.which("minisign") is not None


def homey_workshop():
    """a workshop sitting where a person's really does: under a home path."""
    ws = os.path.join(tempfile.mkdtemp(prefix="sbx9home-"),
                      FLOOR.strip("/"), "pat", "Sandbox")
    os.makedirs(ws)
    journal.ensure_genesis(ws)
    return ws


def throwaway_key():
    """a keypair that exists for one test and belongs to nobody.

    The core's own signing key is never touched here: the shelf signs with a
    second key (R15), and a test that borrowed the first would be proving the
    opposite of the ruling.
    """
    d = tempfile.mkdtemp(prefix="sbx9key-")
    sec = os.path.join(d, "shelf.key")
    pub = os.path.join(d, "shelf.pub")
    r = subprocess.run(["minisign", "-G", "-W", "-s", sec, "-" + "p", pub],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        return None, None, None
    with open(pub, encoding="utf-8") as f:
        text = [l.strip() for l in f if l.strip()
                and not l.startswith("untrusted comment")]
    return sec, pub, text[-1]


class TestShare(unittest.TestCase):
    def setUp(self):
        self.ws = homey_workshop()
        src = os.path.join(self.ws, "tokens.css")
        with open(src, "w") as f:
            f.write(":root {}\n")
        shelf.save(self.ws, src, note="the design tokens")
        self.staging = tempfile.mkdtemp(prefix="sbx9st-")

    def build_dir(self):
        return os.path.join(self.ws, "shelf", "tokens.css")

    def staged(self, rel="BUILD.md"):
        return os.path.join(self.staging, "builds", "tokens.css", rel)

    def test_a_card_from_a_stock_home_shares_and_exits_zero(self):
        """shelf.md check 3, run where it bites: the workshop's own path
        carries the floor needle, so the 8.2.3 blanket refusal fires here."""
        ok, msg = share.share(self.ws, "tokens.css", self.staging)
        self.assertTrue(ok, msg)
        self.assertIn("the push is your hand", msg)
        for dirpath, _, names in os.walk(os.path.join(self.staging, "builds")):
            for n in names:
                with open(os.path.join(dirpath, n), encoding="utf-8") as f:
                    self.assertNotIn(FLOOR, f.read(), n)

    def test_the_card_never_carried_an_absolute_path_to_begin_with(self):
        c = shelf.card(self.ws, "tokens.css")
        self.assertEqual(c["from"], "tokens.css")
        self.assertFalse(c["from"].startswith("/"))

    def test_a_source_outside_the_workshop_is_named_not_pathed(self):
        outside = os.path.join(tempfile.mkdtemp(prefix="sbx9out-"), "kit.md")
        with open(outside, "w") as f:
            f.write("a kit\n")
        shelf.save(self.ws, outside)
        c = shelf.card(self.ws, "kit.md")
        self.assertEqual(c["from"], "outside the workshop (kit.md)")

    def test_a_home_path_in_the_payload_is_stripped_and_counted(self):
        with open(os.path.join(self.build_dir(), "notes.md"), "w") as f:
            f.write("built at " + FLOOR + "someone/thing and " + FLOOR + "someone/else\n")
        ok, msg = share.share(self.ws, "tokens.css", self.staging)
        self.assertTrue(ok, msg)
        self.assertIn("stripped", msg)
        self.assertIn("notes.md", msg)
        with open(self.staged("notes.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn(FLOOR, text)
        self.assertIn("~/thing", text)

    def test_the_staged_card_says_which_workshop_not_whose(self):
        share.share(self.ws, "tokens.css", self.staging)
        with open(self.staged(), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("from-workshop: %s" % shelf.workshop_id(self.ws), text)
        self.assertNotIn(FLOOR, text)

    def test_a_private_term_still_refuses(self):
        """a home path is a shape and has a scrub-safe spelling; a private
        term is a secret and has none, so this half of the gate stays shut."""
        with open(os.path.join(self.build_dir(), "bio.md"), "w") as f:
            f.write("the owner's company files\n")
        terms = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        terms.write("company files\n")
        terms.close()
        os.environ[clean.TERMS_ENV] = terms.name
        try:
            ok, msg = share.share(self.ws, "tokens.css", self.staging)
        finally:
            del os.environ[clean.TERMS_ENV]
        self.assertFalse(ok)
        self.assertIn("scrub refused", msg)
        self.assertFalse(os.path.exists(self.staged()))

    def test_a_deny_listed_file_still_refuses(self):
        with open(os.path.join(self.build_dir(), "creds.env"), "w") as f:
            f.write("SECRET=1\n")
        ok, msg = share.share(self.ws, "tokens.css", self.staging)
        self.assertFalse(ok)
        self.assertIn("deny-listed", msg)
        self.assertFalse(os.path.exists(self.staged()))

    def test_a_refused_share_records_nothing(self):
        with open(os.path.join(self.build_dir(), "creds.env"), "w") as f:
            f.write("SECRET=1\n")
        share.share(self.ws, "tokens.css", self.staging)
        events, _ = journal.read(self.ws)
        self.assertEqual([e for e in events if e.get("cls") == "build-shared"], [])

    def test_a_share_lands_on_the_record_with_the_card_as_receipt(self):
        share.share(self.ws, "tokens.css", self.staging)
        events, _ = journal.read(self.ws)
        shared = [e for e in events if e.get("cls") == "build-shared"]
        self.assertEqual(len(shared), 1)
        self.assertEqual(shared[0]["build"], "tokens.css")
        self.assertEqual(shared[0]["body"], "shared: tokens.css")
        self.assertEqual(shared[0]["ink"], "receipted")
        self.assertTrue(os.path.exists(shared[0]["receipt"]))

    def test_no_git_rides_the_staging(self):
        subprocess.run(["git", "init", "--quiet", self.build_dir()], check=True)
        ok, msg = share.share(self.ws, "tokens.css", self.staging)
        self.assertTrue(ok, msg)
        self.assertFalse(os.path.exists(self.staged(".git")))


class TestSigning(unittest.TestCase):
    def setUp(self):
        self.ws = homey_workshop()
        src = os.path.join(self.ws, "kit.md")
        with open(src, "w") as f:
            f.write("a shared kit\n")
        shelf.save(self.ws, src)
        self.staging = tempfile.mkdtemp(prefix="sbx9st-")
        self._env = {k: os.environ.get(k)
                     for k in (share.SECKEY_ENV, share.PUBKEY_ENV)}

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_the_core_key_is_refused_by_name(self):
        """rule R15: the shelf signs with a second key. A leaked shelf key must
        never be able to speak for the core's own manifest."""
        os.environ[share.SECKEY_ENV] = share.CORE_KEY
        ok, msg = share.share(self.ws, "kit.md", self.staging, sign=True)
        self.assertFalse(ok)
        self.assertIn("second key", msg)
        self.assertFalse(os.path.exists(
            os.path.join(self.staging, "builds", "kit.md", "BUILD.md")))

    def test_no_key_set_refuses_and_says_which_one_it_wants(self):
        os.environ.pop(share.SECKEY_ENV, None)
        ok, msg = share.share(self.ws, "kit.md", self.staging, sign=True)
        self.assertFalse(ok)
        self.assertIn(share.SECKEY_ENV, msg)

    @unittest.skipUnless(HAS_MINISIGN, "minisign is not installed here")
    def test_a_signed_share_writes_the_signature_beside_the_card(self):
        sec, pub, keystr = throwaway_key()
        self.assertIsNotNone(sec, "minisign would not make a throwaway key")
        os.environ[share.SECKEY_ENV] = sec
        os.environ[share.PUBKEY_ENV] = pub
        ok, msg = share.share(self.ws, "kit.md", self.staging, sign=True)
        self.assertTrue(ok, msg)
        card = os.path.join(self.staging, "builds", "kit.md", "BUILD.md")
        self.assertTrue(os.path.exists(card + share.SIG_SUFFIX))
        self.assertIn("signed: minisign, key %s…" % keystr[:12], msg)
        with open(card, encoding="utf-8") as f:
            self.assertIn("signed-by: %s" % keystr, f.read())


class TestFetch(unittest.TestCase):
    def setUp(self):
        self.ws = homey_workshop()
        self.other = homey_workshop()
        src = os.path.join(self.other, "kit.md")
        with open(src, "w") as f:
            f.write("a shared kit\n")
        shelf.save(self.other, src)
        self.source = tempfile.mkdtemp(prefix="sbx9src-")
        self._env = {k: os.environ.get(k)
                     for k in (share.SECKEY_ENV, share.PUBKEY_ENV)}
        share.share(self.other, "kit.md", self.source)

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def resign(self):
        """re-stage the same build signed, with a key made for this test."""
        sec, pub, keystr = throwaway_key()
        os.environ[share.SECKEY_ENV] = sec
        os.environ[share.PUBKEY_ENV] = pub
        self.source = tempfile.mkdtemp(prefix="sbx9src-")
        ok, msg = share.share(self.other, "kit.md", self.source, sign=True)
        os.environ.pop(share.PUBKEY_ENV, None)
        return ok, msg, keystr

    def test_the_unsigned_line_is_written_exactly(self):
        ok, msg = share.fetch(self.ws, self.source, "kit.md", None)
        self.assertFalse(ok)
        self.assertIn("source: UNVERIFIED — no signature on this card. you are "
                      "trusting the shelf you fetched from, not a key. it still "
                      "lands on your k.", msg)
        self.assertIn("real terminal", msg)

    def test_fetch_lists_verifies_and_needs_the_key(self):
        self.assertEqual(share.list_source(self.source), ["kit.md"])
        ok, msg = share.fetch(self.ws, self.source, "kit.md", key())
        self.assertTrue(ok, msg)
        c = shelf.card(self.ws, "kit.md")
        self.assertEqual(c["origin"], "external")  # provenance never launders

    def test_a_fetched_card_remembers_which_door_it_came_by(self):
        share.fetch(self.ws, self.source, "kit.md", key())
        c = shelf.card(self.ws, "kit.md")
        self.assertTrue(shelf.door_of(c).startswith("fetched from"))
        self.assertNotIn(FLOOR, shelf.door_of(c))

    def test_the_fetched_line_gets_its_rung_from_the_one_function(self):
        share.fetch(self.ws, self.source, "kit.md", key())
        events, _ = journal.read(self.ws)
        landed = [e for e in events if e.get("cls") == "build-kept"
                  and e.get("origin") == "external"][0]
        self.assertEqual(landed["ink"], "receipted")
        self.assertEqual(landed["hand"], "synthetic")  # a rig's key, stamped
        from engine import desk
        self.assertEqual(desk.compute_ink({"receipt": landed["receipt"]}), "receipted")

    def test_tampered_bytes_never_fetch(self):
        payload = os.path.join(self.source, "builds", "kit.md", "kit.md")
        with open(payload, "a") as f:
            f.write("tampered\n")
        ok, msg = share.fetch(self.ws, self.source, "kit.md", key())
        self.assertFalse(ok)
        self.assertIn("disagree with its own pin", msg)
        self.assertIsNone(shelf.card(self.ws, "kit.md"))

    @unittest.skipUnless(HAS_MINISIGN, "minisign is not installed here")
    def test_the_signed_line_with_a_key_expected_is_written_exactly(self):
        ok, msg, keystr = self.resign()
        self.assertTrue(ok, msg)
        ok, msg = share.fetch(self.ws, self.source, "kit.md", key(),
                              expect_key=keystr)
        self.assertTrue(ok, msg)
        self.assertIn("source: signed by %s… — matches the key you expected"
                      % keystr[:12], msg)

    @unittest.skipUnless(HAS_MINISIGN, "minisign is not installed here")
    def test_the_signed_line_with_no_key_expected_is_written_exactly(self):
        ok, msg, keystr = self.resign()
        self.assertTrue(ok, msg)
        ok, msg = share.fetch(self.ws, self.source, "kit.md", key())
        self.assertTrue(ok, msg)
        self.assertIn("source: signed by %s… — no key expected, so i checked "
                      "only that the signature holds" % keystr[:12], msg)

    @unittest.skipUnless(HAS_MINISIGN, "minisign is not installed here")
    def test_a_key_that_is_not_the_one_you_expected_refuses(self):
        ok, msg, _keystr = self.resign()
        self.assertTrue(ok, msg)
        other = throwaway_key()[2]
        ok, msg = share.fetch(self.ws, self.source, "kit.md", key(),
                              expect_key=other)
        self.assertFalse(ok)
        self.assertEqual(msg, "the signature does not match the key you "
                              "expected — nothing fetched")
        self.assertIsNone(shelf.card(self.ws, "kit.md"))

    @unittest.skipUnless(HAS_MINISIGN, "minisign is not installed here")
    def test_a_signature_that_does_not_hold_refuses_before_the_key(self):
        ok, msg, _keystr = self.resign()
        self.assertTrue(ok, msg)
        card = os.path.join(self.source, "builds", "kit.md", "BUILD.md")
        with open(card, "a") as f:
            f.write("note: added after the signature\n")
        ok, msg = share.fetch(self.ws, self.source, "kit.md", None)
        self.assertFalse(ok)
        self.assertIn("the signature does not hold — nothing fetched", msg)
        self.assertNotIn("real terminal", msg)


if __name__ == "__main__":
    unittest.main()
