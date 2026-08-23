# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the shelf: cards keep their promises; drifted payloads never spread."""
import os
import tempfile
import unittest
from unittest import mock

from engine import journal, project, shelf


class TestBuilds(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self.src = os.path.join(tempfile.mkdtemp(prefix="sbx8b-"), "tokens.css")
        open(self.src, "w").write(":root { --ink: black; }\n")

    def events(self, cls):
        events, _ = journal.read(self.ws)
        return [e for e in events if e.get("cls") == cls]

    def test_a_card_never_carries_an_absolute_path(self):
        """the S1 case, at its root: `from:` is workshop-relative, so nothing has to
        strip it on the way out (inventory finding 4)."""
        inside = os.path.join(project.root_of(self.ws, "geardoor"), "tax.json")
        with open(inside, "w") as f:
            f.write("{}\n")
        shelf.save(self.ws, inside)
        self.assertEqual(shelf.card(self.ws, "tax.json")["from"],
                         "projects/geardoor/tax.json")

    def test_a_source_outside_the_workshop_is_named_not_pathed(self):
        shelf.save(self.ws, self.src)
        self.assertEqual(shelf.card(self.ws, "tokens.css")["from"],
                         "outside the workshop (tokens.css)")

    def test_the_workshop_is_named_by_an_id_never_by_a_home_path(self):
        """law 13: the scrub-safe answer to "whose workshop". Minted on first
        need — a save — because init is not the only door a workshop opens by."""
        idfile = os.path.join(self.ws, journal.STATE_DIR, shelf.ID_FILE)
        self.assertFalse(os.path.exists(idfile))
        shelf.save(self.ws, self.src)
        self.assertTrue(os.path.exists(idfile))
        first = shelf.workshop_id(self.ws)
        self.assertEqual(len(first), 12)
        int(first, 16)                       # hex, and nothing else
        self.assertEqual(shelf.workshop_id(self.ws), first)   # kept, not re-minted

    def test_a_kept_build_says_which_door_it_came_by(self):
        shelf.save(self.ws, self.src)
        self.assertEqual(shelf.door_of(shelf.card(self.ws, "tokens.css")),
                         "kept here")

    def test_save_writes_card_with_hash_and_origin(self):
        ok, msg = shelf.save(self.ws, self.src, note="the design tokens")
        self.assertTrue(ok)
        c = shelf.card(self.ws, "tokens.css")
        self.assertEqual(len(c["sha256"]), 64)
        self.assertEqual(c["origin"], "session-kept")
        self.assertEqual(c["note"], "the design tokens")

    def test_origin_never_reads_the_terminal(self):
        """a file descriptor is not a hand. Under a rig's pty `isatty()` said
        owner-kept for a build no owner touched, and this test went red at a
        real terminal for the same reason. owner-kept waits for S1: a key on
        the build itself."""
        import sys
        with mock.patch.object(sys.stdin, "isatty", return_value=True):
            shelf.save(self.ws, self.src)
        self.assertEqual(shelf.card(self.ws, "tokens.css")["origin"], "session-kept")

    def test_a_press_and_a_use_both_land_on_the_record(self):
        """the J19 case: the card remembered where a build went and the record learned
        nothing. Both moves are events now, each with its card as receipt."""
        shelf.save(self.ws, self.src)
        kept = self.events("build-kept")
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["ink"], "receipted")
        self.assertTrue(kept[0]["receipt"].endswith("BUILD.md"))
        self.assertEqual(kept[0]["build"], "tokens.css")
        shelf.use(self.ws, "tokens.css", "geardoor", project.root_of(self.ws, "geardoor"))
        used = self.events("build-used")
        self.assertEqual(len(used), 1)
        self.assertEqual(used[0]["project"], "geardoor")
        self.assertEqual(used[0]["body"], "used: tokens.css on geardoor")
        self.assertEqual(used[0]["ink"], "receipted")
        self.assertTrue(os.path.exists(used[0]["receipt"]))

    def test_a_refused_use_leaves_the_record_alone(self):
        shelf.save(self.ws, self.src)
        root = project.root_of(self.ws, "geardoor")
        with open(os.path.join(root, "tokens.css"), "w") as f:
            f.write("mine\n")
        ok, _ = shelf.use(self.ws, "tokens.css", "geardoor", root)
        self.assertFalse(ok)
        self.assertEqual(self.events("build-used"), [])

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
    """seal writes the REAL manifest — snapshot and restore it, or every
    suite run dirties the tree (the release verb's first catch)."""

    def setUp(self):
        from engine import integrity
        self._mp = integrity.manifest_path()
        self._saved = open(self._mp, "rb").read() if os.path.exists(self._mp) else None
        self._stat = os.stat(self._mp) if self._saved is not None else None

    def tearDown(self):
        if self._saved is not None:
            with open(self._mp, "wb") as f:
                f.write(self._saved)
            # bytes AND clock — a restored file that looks newer than the
            # signature would make every release check refuse forever
            os.utime(self._mp, (self._stat.st_atime, self._stat.st_mtime))

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


class TestTheCardsEmptyLedger(unittest.TestCase):
    """item X10 — an empty `## used` section explains itself, and parses."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self.src = os.path.join(tempfile.mkdtemp(prefix="sbx8b-"), "tokens.css")
        with open(self.src, "w") as f:
            f.write(":root { --ink: black; }\n")

    def _card_text(self, name):
        with open(os.path.join(self.ws, "shelf", name, "BUILD.md"),
                  encoding="utf-8") as f:
            return f.read()

    def test_a_fresh_card_says_what_the_section_is_for(self):
        shelf.save(self.ws, self.src, name="tokens")
        text = self._card_text("tokens")
        self.assertIn("## used\n%s\n" % shelf.USED_HINT, text)
        self.assertIn("each sandbox use appends a line here", shelf.USED_HINT)

    def test_the_card_still_parses_field_for_field(self):
        shelf.save(self.ws, self.src, name="tokens", note="the ink scale")
        c = shelf.card(self.ws, "tokens")
        for field in ("kept", "from", "sha256", "origin", "note"):
            self.assertIn(field, c, c)
        self.assertEqual(c["origin"], "session-kept")

    def test_a_use_writes_its_line_under_the_hint(self):
        shelf.save(self.ws, self.src, name="tokens")
        ok, msg = shelf.use(self.ws, "tokens", "geardoor",
                            project.root_of(self.ws, "geardoor"))
        self.assertTrue(ok, msg)
        text = self._card_text("tokens")
        self.assertIn(shelf.USED_HINT, text)
        self.assertIn("used on ", text)
        self.assertLess(text.index(shelf.USED_HINT), text.index("used on "))

    def test_a_rebuild_of_an_empty_ledger_leaves_the_card_alone(self):
        """the hint is the empty state, so rebuilding an unused card writes
        the same bytes and reports no move."""
        shelf.save(self.ws, self.src, name="tokens")
        before = self._card_text("tokens")
        self.assertFalse(shelf.write_used(self.ws, "tokens", []))
        self.assertEqual(self._card_text("tokens"), before)


if __name__ == "__main__":
    unittest.main()
