# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The 8.2.3 sitting's pins: the unknown-flag class closed at the one door,
the drop exit for accidental drafts, honest exit codes and verdicts, the
kept-file drift a green doctor used to hide, and the release wall's fifth
move. Each of these was found live on 8.2.2 before it was fixed here."""
import contextlib
import io
import json
import os
import tempfile
import unittest

from engine import desk, journal, make, notes, placement, project, verbs


def _run(ws, verb, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = verbs.dispatch(ws, verb, argv)
    return rc, buf.getvalue()


class Workshop(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")


class TestUnknownFlagClass(Workshop):
    """A verb that treats an unknown --flag as content is the bug — the
    class, not the instance. note --help once staged a junk draft; drafts
    --drop 10 was silently ignored."""

    def test_every_verb_refuses_an_unknown_flag(self):
        for verb in verbs.TABLE:
            rc, out = _run(self.ws, verb, ["--no-such-flag"])
            self.assertEqual(rc, 2, "%s swallowed an unknown flag" % verb)
            self.assertIn("doesn't know --no-such-flag", out, verb)

    def test_note_dash_dash_help_stages_nothing(self):
        rc, out = _run(self.ws, "note", ["--help"])
        self.assertEqual(rc, 2)
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(pile, [])

    def test_known_flags_still_pass_the_door(self):
        rc, out = _run(self.ws, "recall", ["--project", "geardoor", "ghost"])
        self.assertEqual(rc, 0)

    def test_a_flag_valued_value_is_not_refused(self):
        # save --note takes a value; a value starting with -- is content.
        rc, out = _run(self.ws, "save", ["--note", "--weird-but-content"])
        self.assertIn("save needs a path", out)  # the PATH refusal, never the flag's
        self.assertNotIn("doesn't know", out)


class TestDraftsDrop(Workshop):
    def test_drop_retracts_one_and_says_it_in_full(self):
        notes.note(self.ws, "keep me", target_project="geardoor")
        notes.note(self.ws, "drop me", target_project="geardoor")
        rc, out = _run(self.ws, "drafts", ["--drop", "2"])
        self.assertEqual(rc, 0)
        self.assertIn("drop me", out)  # the retraction happens in the open
        pile, _ = desk.drafts(self.ws)
        self.assertEqual([d["body"] for d in pile], ["keep me"])

    def test_drop_out_of_range_refuses(self):
        notes.note(self.ws, "only one", target_project="geardoor")
        rc, out = _run(self.ws, "drafts", ["--drop", "5"])
        self.assertEqual(rc, 1)
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(len(pile), 1)

    def test_drop_keeps_torn_lines_on_disk(self):
        notes.note(self.ws, "first", target_project="geardoor")
        with open(desk.staging_path(self.ws), "ab") as f:
            f.write(b"{torn json\n")
        notes.note(self.ws, "second", target_project="geardoor")
        rc, _ = _run(self.ws, "drafts", ["--drop", "1"])
        self.assertEqual(rc, 0)
        raw = open(desk.staging_path(self.ws), "rb").read()
        self.assertIn(b"{torn json", raw)
        pile, scars = desk.drafts(self.ws)
        self.assertEqual([d["body"] for d in pile], ["second"])
        self.assertEqual(len(scars), 1)

    def test_drop_last_draft_removes_the_file(self):
        notes.note(self.ws, "solo", target_project="geardoor")
        rc, _ = _run(self.ws, "drafts", ["--drop", "1"])
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(desk.staging_path(self.ws)))


class TestHonestExits(Workshop):
    def test_headless_approve_exits_nonzero(self):
        notes.note(self.ws, "waiting", target_project="geardoor")
        rc, out = _run(self.ws, "approve", [])
        self.assertEqual(rc, 1)  # the words refuse; the exit must agree
        self.assertIn("real terminal", out)

    def test_make_close_over_empty_diff_says_attempted(self):
        make.open_session(self.ws, "geardoor", "change nothing")
        ok, msg = make.close_session(self.ws, "geardoor")
        self.assertTrue(ok)
        self.assertIn("attempted", msg)
        self.assertNotIn("confirmed", msg)

    def test_make_close_over_real_diff_still_confirms(self):
        make.open_session(self.ws, "geardoor", "change one file")
        root = project.root_of(self.ws, "geardoor")
        with open(os.path.join(root, "new.txt"), "w", encoding="utf-8") as f:
            f.write("born\n")
        ok, msg = make.close_session(self.ws, "geardoor")
        self.assertTrue(ok)
        self.assertIn("confirmed — 1 file(s) changed", msg)


class TestKeptFileDrift(Workshop):
    """Two surfaces told the truth about their own scope and the wall stayed
    old: update said 'kept (yours)', doctor said 'placed files current'."""

    def _payload(self):
        src_dir = tempfile.mkdtemp(prefix="sbx8-payload-")
        src = os.path.join(src_dir, "guard.py")
        with open(src, "w", encoding="utf-8") as f:
            f.write("the shipped fence\n")
        dest = os.path.join(self.ws, ".claude", "guard.py")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        return {dest: src}, dest, src

    def test_unrecorded_old_copy_is_named_as_drift(self):
        payload, dest, _ = self._payload()
        with open(dest, "w", encoding="utf-8") as f:
            f.write("the three-releases-old fence\n")
        self.assertEqual(placement.unrecorded_drift(self.ws, payload), [dest])

    def test_matching_unrecorded_copy_is_adopted_on_sync(self):
        payload, dest, src = self._payload()
        with open(dest, "w", encoding="utf-8") as f:
            f.write("the shipped fence\n")
        report = placement.sync(self.ws, payload)
        self.assertTrue(any("adopted" in line for line in report))
        self.assertIn(dest, placement.book(self.ws))
        self.assertEqual(placement.unrecorded_drift(self.ws, payload), [])

    def test_recorded_and_current_files_are_not_drift(self):
        payload, dest, src = self._payload()
        placement.sync(self.ws, payload)  # places it and records it
        self.assertEqual(placement.unrecorded_drift(self.ws, payload), [])


class TestResetByName(Workshop):
    def test_reset_reaches_a_payload_dest_the_book_never_recorded(self):
        from unittest import mock
        src_dir = tempfile.mkdtemp(prefix="sbx8-payload-")
        src = os.path.join(src_dir, "guard.py")
        with open(src, "w", encoding="utf-8") as f:
            f.write("the shipped fence\n")
        dest = os.path.join(self.ws, ".claude", "guard.py")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write("the old fence\n")
        with mock.patch("engine.onboard.shipped_payload", return_value={dest: src}):
            rc, out = _run(self.ws, "reset", ["guard.py"])
        self.assertEqual(rc, 0)
        self.assertIn("reset to pristine", out)
        self.assertEqual(open(dest, encoding="utf-8").read(), "the shipped fence\n")
        self.assertIn(dest, placement.book(self.ws))  # the book heals

    def test_reset_still_refuses_what_was_never_placed(self):
        rc, out = _run(self.ws, "reset", ["/no/such/file"])
        self.assertEqual(rc, 1)
        self.assertIn("never placed", out)


class TestReleaseWallFifthMove(unittest.TestCase):
    def test_release_notes_carry_section_and_key(self):
        from engine import integrity
        version = open(os.path.join(integrity.root(), "VERSION"), encoding="utf-8").read().strip()
        path, tagline = integrity.release_notes(version)
        self.assertIsNotNone(path, tagline)
        text = open(path, encoding="utf-8").read()
        self.assertIn("Sandbox OS %s — %s" % (version, tagline), text)
        self.assertIn("release public key: RWS", text)

    def test_release_notes_refuse_a_version_the_changelog_never_met(self):
        from engine import integrity
        path, why = integrity.release_notes("0.0.0-ghost")
        self.assertIsNone(path)
        self.assertIn("no section", why)


if __name__ == "__main__":
    unittest.main()
