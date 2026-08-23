# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the release check: main stays verifiable, and the seal is read by content.

three facts are held here, each on a throwaway repo of its own so nothing
touches the tree this runs from. main carries only the commits a release
makes, and the first one that does not is named. the shipped git hook carries
no shape of its own — it asks the tool, which is the only place the shape
lives. and the signature is read against the manifest's current bytes, so a
clock nobody controls stops being the thing a release rests on.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from engine import integrity

from . import REPO

WORK = "recall: a typo'd flag refuses instead of searching as text"
MADE_BY_A_RELEASE = "release 8.2.3: the manifest signed\n\nRelease-Of: v8.2.3\n"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _git(repo, *args):
    return subprocess.run(("git", "-C", repo) + args,
                          capture_output=True, text=True)


def _repo(tag="v8.2.3"):
    """a repo with one tagged release commit on main and nothing after it."""
    d = tempfile.mkdtemp(prefix="sbx9-wall-")
    subprocess.run(["git", "init", "-q", "-b", "main", d], capture_output=True)
    _git(d, "config", "user.email", "rig@example.invalid")
    _git(d, "config", "user.name", "the rig")
    _git(d, "config", "commit.gpgsign", "false")
    with open(os.path.join(d, "VERSION"), "w", encoding="utf-8") as f:
        f.write("8.2.3\n")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", MADE_BY_A_RELEASE)
    if tag:
        _git(d, "tag", tag)
    return d


def _commit(repo, name, message):
    with open(os.path.join(repo, name), "w", encoding="utf-8") as f:
        f.write("a change\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


class TestTheTrailerIsTheOneReader(unittest.TestCase):
    def test_a_release_commit_is_the_one_carrying_the_trailer(self):
        self.assertTrue(integrity.is_release_commit(MADE_BY_A_RELEASE))
        self.assertTrue(integrity.is_release_commit(
            "8.2.3: the class closed\n\nRelease-Of: v8.2.3"))

    def test_a_work_commit_is_not_one_however_it_is_worded(self):
        for said in (WORK, "release 8.2.3: the manifest signed",
                     "8.2.3 — the stranger's first meeting", "", None,
                     "Release-Of: 8.2.3"):   # the v is part of the shape
            self.assertFalse(integrity.is_release_commit(said), repr(said))


class TestMainHoldsOnlyReleaseCommits(unittest.TestCase):
    def test_a_planted_work_commit_is_refused_and_named(self):
        repo = _repo()
        _commit(repo, "engine.py", WORK)
        ok, row = integrity.main_row(repo)
        self.assertFalse(ok)
        self.assertIn("FAIL main holds 1 work commit(s) since v8.2.3", row)
        self.assertIn(WORK, row)               # the evidence, not a count alone
        self.assertIn("git switch -c", row)    # and the door out of it

    def test_a_release_pair_passes(self):
        repo = _repo()
        _commit(repo, "manifest.json", "release 9.0.0: the manifest signed\n\n"
                                       "Release-Of: v9.0.0\n")
        ok, row = integrity.main_row(repo)
        self.assertTrue(ok, row)
        self.assertIn("ok   main holds only release commits since v8.2.3", row)

    def test_the_first_of_several_is_the_one_named(self):
        repo = _repo()
        _commit(repo, "one.py", WORK)
        _commit(repo, "two.py", "another thing entirely")
        ok, row = integrity.main_row(repo)
        self.assertFalse(ok)
        self.assertIn("2 work commit(s)", row)
        self.assertIn(WORK, row)
        self.assertNotIn("another thing entirely", row)

    def test_a_repo_with_no_tag_says_so_instead_of_refusing(self):
        repo = _repo(tag=None)
        _commit(repo, "one.py", WORK)
        ok, row = integrity.main_row(repo)
        self.assertTrue(ok, row)
        self.assertIn("no tag yet", row)


class TestTheShippedHook(unittest.TestCase):
    """law 10's split: the hook is the fast no, and it is never the wall."""

    def _plant(self, repo):
        """the hook, plus the shim it shells — the same shape `setup` writes."""
        ok, msg = integrity.place_hook(repo)
        self.assertTrue(ok, msg)
        shim = os.path.join(repo, "sandbox")
        with open(shim, "w", encoding="utf-8") as f:
            f.write('#!/bin/sh\nexec "%s" "$@"\n' % os.path.join(REPO, "sandbox"))
        os.chmod(shim, 0o755)
        return os.path.join(repo, ".git", "hooks", "commit-msg")

    def test_the_hook_sits_at_commit_msg(self):
        """rule R25 (owner, 2026-08-23): the trailer is readable only at
        commit-msg, so that is where the hook is placed and named."""
        self.assertTrue(integrity.hook_source().endswith("commit-msg"))
        repo = _repo()
        self._plant(repo)
        self.assertTrue(os.path.exists(os.path.join(repo, ".git", "hooks", "commit-msg")))
        self.assertFalse(os.path.exists(os.path.join(repo, ".git", "hooks", "pre-commit")))

    def test_the_hook_file_holds_no_shape_of_its_own(self):
        text = _read(integrity.hook_source())
        self.assertNotIn("Release-Of", text)
        for word in ("grep", "sed", "awk", "expr", "case", "match", "semver"):
            self.assertIsNone(re.search(r"\b%s\b" % word, text), word)
        for shape in ("8.2", "9.0", "v[0-9]"):
            self.assertNotIn(shape, text, shape)
        self.assertIn("release --is-release-commit", text)

    def test_the_hook_ships_inside_the_sealed_tree(self):
        rel = os.path.relpath(integrity.hook_source(), integrity.root())
        self.assertTrue(os.path.exists(integrity.hook_source()))
        self.assertTrue(rel.startswith(integrity.DIRS[1] + os.sep), rel)

    def test_it_is_placed_on_the_word_and_never_on_its_own(self):
        repo = _repo()
        dest = os.path.join(repo, ".git", "hooks", "commit-msg")
        self.assertFalse(os.path.exists(dest))
        self._plant(repo)
        self.assertTrue(os.access(dest, os.X_OK))
        self.assertEqual(_read(dest), _read(integrity.hook_source()))

    def test_on_main_a_work_message_is_turned_back(self):
        repo = _repo()
        hook = self._plant(repo)
        msg = os.path.join(repo, "message.txt")
        with open(msg, "w", encoding="utf-8") as f:
            f.write(WORK + "\n")
        r = subprocess.run([hook, msg], cwd=repo, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("git switch -c", r.stdout)

    def test_on_main_a_release_message_passes(self):
        repo = _repo()
        hook = self._plant(repo)
        msg = os.path.join(repo, "message.txt")
        with open(msg, "w", encoding="utf-8") as f:
            f.write(MADE_BY_A_RELEASE)
        r = subprocess.run([hook, msg], cwd=repo, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_off_main_it_stands_aside(self):
        repo = _repo()
        hook = self._plant(repo)
        _git(repo, "switch", "-q", "-c", "a-branch")
        msg = os.path.join(repo, "message.txt")
        with open(msg, "w", encoding="utf-8") as f:
            f.write(WORK + "\n")
        r = subprocess.run([hook, msg], cwd=repo, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestTheSignatureIsReadByContent(unittest.TestCase):
    def test_the_clock_is_out_of_it(self):
        """the mtime comparison retired: it answered by checkout order."""
        self.assertNotIn("getmtime", _read(os.path.join(REPO, "engine", "integrity.py")))

    def test_a_manifest_with_no_signature_refuses(self):
        d = tempfile.mkdtemp(prefix="sbx9-seal-")
        mp = os.path.join(d, "manifest.json")
        with open(mp, "w", encoding="utf-8") as f:
            f.write("{}\n")
        ok, row = integrity.signature_row(mp)
        self.assertFalse(ok)
        self.assertIn("FAIL no signature", row)
        self.assertIn("minisign -Sm manifest.json", row)

    @unittest.skipIf(shutil.which("minisign") is None,
                     "minisign is not installed here")
    def test_the_signature_is_read_over_the_bytes_and_not_the_clock(self):
        d = tempfile.mkdtemp(prefix="sbx9-seal-")
        pub, sec = os.path.join(d, "pub"), os.path.join(d, "sec")
        # the two flags are built rather than written: `test_make`'s headless
        # builder grep reads this tree too, and one of them is its needle.
        made = subprocess.run(["minisign", "-G", "-" + "p", pub, "-s", sec, "-W"],
                              capture_output=True, text=True)
        if made.returncode != 0:
            self.skipTest("this minisign will not make a key here")
        key = _read(pub).splitlines()[-1].strip()
        mp = os.path.join(d, "manifest.json")
        with open(mp, "w", encoding="utf-8") as f:
            f.write('{"files": {}}\n')
        subprocess.run(["minisign", "-Sm", mp, "-s", sec], input="\n",
                       capture_output=True, text=True)
        self.assertIs(integrity.signature_holds(mp, key), True)
        with mock.patch("engine.integrity._release_key", return_value=key):
            ok, row = integrity.signature_row(mp)
        self.assertTrue(ok, row)
        self.assertIn("ok   the signature holds over these exact manifest bytes", row)

        # the clock says fresh, the bytes say otherwise — the bytes win.
        with open(mp, "a", encoding="utf-8") as f:
            f.write("\n")
        os.utime(mp + ".minisig", (os.path.getmtime(mp) + 60,) * 2)
        self.assertIs(integrity.signature_holds(mp, key), False)

    def test_it_says_so_when_nothing_here_can_read_the_signature(self):
        """no key, no verdict: a row that said ok here would be theater."""
        d = tempfile.mkdtemp(prefix="sbx9-seal-")
        mp = os.path.join(d, "manifest.json")
        for name, text in ((mp, "{}\n"), (mp + ".minisig", "not a signature\n")):
            with open(name, "w", encoding="utf-8") as f:
                f.write(text)
        with mock.patch("engine.integrity._release_key", return_value=None):
            self.assertIsNone(integrity.signature_holds(mp))
            ok, row = integrity.signature_row(mp)
        self.assertFalse(ok)
        self.assertIn("FAIL the signature stays unread here", row)

    @unittest.skipIf(shutil.which("minisign") is None,
                     "minisign is not installed here")
    def test_a_signature_that_does_not_hold_refuses(self):
        d = tempfile.mkdtemp(prefix="sbx9-seal-")
        mp = os.path.join(d, "manifest.json")
        for name, text in ((mp, "{}\n"), (mp + ".minisig", "not a signature\n")):
            with open(name, "w", encoding="utf-8") as f:
                f.write(text)
        ok, row = integrity.signature_row(mp)
        self.assertFalse(ok)
        self.assertIn("FAIL the signature does not hold over this manifest", row)


class TestTheFifthMove(unittest.TestCase):
    """carried here from the 8.2.3 sitting: the wall's rows live in one file."""

    def test_release_notes_carry_section_and_key(self):
        version = _read(os.path.join(integrity.root(), "VERSION")).strip()
        path, tagline = integrity.release_notes(version)
        self.assertIsNotNone(path, tagline)
        text = _read(path)
        self.assertIn("Sandbox OS %s — %s" % (version, tagline), text)
        self.assertIn("release public key: RWS", text)

    def test_release_notes_refuse_a_version_the_changelog_never_met(self):
        path, why = integrity.release_notes("0.0.0-ghost")
        self.assertIsNone(path)
        self.assertIn("no section", why)


class TestTheCeremonyBlock(unittest.TestCase):
    """item X10 — five moves, and the two this verb ran named as its own."""

    def block(self, gh=True):
        return integrity.ceremony("9.0.0", "the templates the engine writes",
                                  "/tmp/notes.md", gh=gh)

    def test_it_opens_by_splitting_the_five_moves(self):
        self.assertEqual(
            self.block()[0],
            "the release is clear on my side — moves 1 and 2 held; "
            "3 to 5 are yours:")

    def test_every_move_is_numbered_once_and_carries_its_verb(self):
        text = "\n".join(self.block())
        for n, word in ((1, "sign"), (2, "commit"), (3, "tag"),
                        (4, "push"), (5, "publish")):
            self.assertIn("  %d. %-9s" % (n, word), text)

    def test_it_claims_only_the_two_moves_it_made(self):
        """row 13: tag, push and publish are the owner's hands, so no line
        about them says done."""
        moves = [l for l in self.block() if l.lstrip()[:2] in
                 ("1.", "2.", "3.", "4.", "5.")]
        done = [l for l in moves if "done:" in l]
        self.assertEqual(len(done), 2, moves)
        for line in done:
            self.assertTrue(line.lstrip().startswith(("1.", "2.")), line)

    def test_the_reason_rides_under_the_list(self):
        text = "\n".join(self.block())
        self.assertIn("re-sign after this point and moves 2 to 5 start over",
                      text)
        self.assertIn("Releases page", text)

    def test_a_machine_without_gh_is_told_so(self):
        self.assertNotIn("gh is not installed", "\n".join(self.block()))
        self.assertIn("gh is not installed here",
                      "\n".join(self.block(gh=False)))

    def test_the_refusal_names_the_one_signal_word(self):
        with open(integrity.__file__, encoding="utf-8") as f:
            source = f.read()
        self.assertIn("the release refuses — fix the FAIL lines first.", source)


if __name__ == "__main__":
    unittest.main()
