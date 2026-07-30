# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The shelf: cards keep their promises; drifted payloads never spread."""
import os
import tempfile
import unittest

from engine import journal, project, shelf


class TestBuilds(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self.src = os.path.join(tempfile.mkdtemp(prefix="sbx8b-"), "tokens.css")
        open(self.src, "w").write(":root { --ink: black; }\n")

    def test_save_writes_card_with_hash_and_origin(self):
        ok, msg = shelf.save(self.ws, self.src, note="the design tokens")
        self.assertTrue(ok)
        c = shelf.card(self.ws, "tokens.css")
        self.assertEqual(len(c["sha256"]), 64)
        self.assertEqual(c["origin"], "session-kept")  # no tty in the suite
        self.assertEqual(c["note"], "the design tokens")

    def test_double_save_refused(self):
        shelf.save(self.ws, self.src)
        ok, msg = shelf.save(self.ws, self.src)
        self.assertFalse(ok)

    def test_use_copies_and_ledgers(self):
        shelf.save(self.ws, self.src)
        root = project.root_of(self.ws, "geardoor")
        ok, msg = shelf.use(self.ws, "tokens.css", "geardoor", root)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(os.path.join(root, "tokens.css")))
        card_text = open(os.path.join(self.ws, "shelf", "tokens.css", "BUILD.md")).read()
        self.assertIn("used on geardoor", card_text)

    def test_drifted_payload_never_spreads(self):
        shelf.save(self.ws, self.src)
        payload = os.path.join(self.ws, "shelf", "tokens.css", "tokens.css")
        open(payload, "a").write("/* drift */\n")
        root = project.root_of(self.ws, "geardoor")
        ok, msg = shelf.use(self.ws, "tokens.css", "geardoor", root)
        self.assertFalse(ok)
        self.assertIn("drifted", msg)

    def test_use_never_overwrites(self):
        shelf.save(self.ws, self.src)
        root = project.root_of(self.ws, "geardoor")
        open(os.path.join(root, "tokens.css"), "w").write("mine\n")
        ok, msg = shelf.use(self.ws, "tokens.css", "geardoor", root)
        self.assertFalse(ok)
        self.assertEqual(open(os.path.join(root, "tokens.css")).read(), "mine\n")

    def test_directory_build_round_trips(self):
        d = tempfile.mkdtemp(prefix="sbx8d-")
        open(os.path.join(d, "a.md"), "w").write("a\n")
        os.makedirs(os.path.join(d, "sub"))
        open(os.path.join(d, "sub", "b.md"), "w").write("b\n")
        ok, _ = shelf.save(self.ws, d, name="kit")
        self.assertTrue(ok)
        root = project.root_of(self.ws, "geardoor")
        ok, _ = shelf.use(self.ws, "kit", "geardoor", root)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(os.path.join(root, os.path.basename(d), "sub", "b.md")))


class TestIntegrity(unittest.TestCase):
    """Seal writes the REAL manifest — snapshot and restore it, or every
    suite run dirties the tree (the release verb's first catch)."""

    def setUp(self):
        from engine import integrity
        self._mp = integrity.manifest_path()
        self._saved = open(self._mp, "rb").read() if os.path.exists(self._mp) else None

    def tearDown(self):
        if self._saved is not None:
            with open(self._mp, "wb") as f:
                f.write(self._saved)

    def test_seal_verify_cycle_and_drift_naming(self):
        from engine import integrity
        ok, msg = integrity.seal()
        self.assertTrue(ok)
        ok, msg = integrity.verify()
        self.assertTrue(ok, msg)
        # No strict theater without a key:
        self.assertIn("tamper-evident", msg)

    def test_strict_mode_refuses_without_the_machinery(self):
        from engine import integrity
        os.environ[integrity.PUBKEY_ENV] = "RWTtestkey"
        try:
            ok, msg = integrity.verify()
            self.assertFalse(ok)
            self.assertIn("refusing", msg)
        finally:
            del os.environ[integrity.PUBKEY_ENV]


if __name__ == "__main__":
    unittest.main()
