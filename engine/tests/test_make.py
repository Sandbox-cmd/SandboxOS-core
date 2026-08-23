# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""make: the diff is code's word, the checks gate the close, and the summary
waits behind the key.

9.0 takes the builder out of this verb: the building happens in the session
the owner already sits in, so there is no subprocess here, no prompt file
written into anyone's project, and two forms in total — `--open` and
`--close`.
"""
import contextlib
import io
import os
import subprocess
import tempfile
import unittest

from engine import desk, journal, make, project, verbs

from . import REPO


def _run(ws, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = verbs.dispatch(ws, "make", argv)
    return rc, buf.getvalue()


class TestMake(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        self.root = project.root_of(self.ws, "geardoor")

    def _set_checks(self, checks):
        cpath = project.contract_path(self.ws, "geardoor")
        with open(cpath, encoding="utf-8") as f:
            base = f.read().split("## checks")[0]
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(base + "## checks\n" + "\n".join(checks) + "\n\n## notes\n")

    def closes(self):
        events, _ = journal.read(self.ws)
        return [e for e in events
                if e.get("op") == "make" and e.get("phase") == "close"]


class TestTheDiff(TestMake):
    def test_open_edit_close_computes_the_diff(self):
        ok, msg = make.open_session(self.ws, "geardoor", "add the tax table")
        self.assertTrue(ok)
        self.assertEqual(msg, "session open on geardoor — add the tax table")
        with open(os.path.join(self.root, "tax.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(self.root, "PROJECT.md"), "a") as f:
            f.write("\n")
        ok, msg = make.close_session(self.ws, "geardoor", "tax table added")
        self.assertTrue(ok, msg)
        close = self.closes()[0]
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
        self.assertEqual(msg, "no make session open on geardoor")

    def test_no_summary_stages_nothing(self):
        make.open_session(self.ws, "geardoor", "quiet pass")
        make.close_session(self.ws, "geardoor")
        pile, _ = desk.drafts(self.ws)
        self.assertEqual(pile, [])

    def test_prompt_file_is_not_a_change(self):
        """the scar of the no-builder branch, as a check: a make that builds
        nothing writes nothing into the project, so the diff is empty."""
        before = sorted(os.listdir(self.root))
        make.open_session(self.ws, "geardoor", "build nothing at all")
        ok, msg = make.close_session(self.ws, "geardoor")
        self.assertTrue(ok, msg)
        self.assertEqual(sorted(os.listdir(self.root)), before)
        self.assertNotIn("PROMPT.md", os.listdir(self.root))
        close = self.closes()[0]
        self.assertEqual(close["diff"], {"added": [], "removed": [], "changed": []})
        self.assertIn("attempted", msg)


class TestTheCloseRunsTheChecks(TestMake):
    def test_a_green_close_names_the_ship(self):
        self._set_checks(["true"])
        make.open_session(self.ws, "geardoor", "the tax table")
        ok, msg = make.close_session(self.ws, "geardoor", "tax table + 3 tests")
        self.assertTrue(ok, msg)
        self.assertEqual(msg.splitlines()[-1],
                         "checks green — ship it: sandbox ship geardoor")
        self.assertEqual(self.closes()[0]["checks"], "green")

    def test_a_red_close_refuses_and_the_make_stays_open(self):
        self._set_checks(["true", "false"])
        make.open_session(self.ws, "geardoor", "the tax table")
        ok, msg = make.close_session(self.ws, "geardoor", "tax table + 3 tests")
        self.assertFalse(ok)
        self.assertEqual(
            msg,
            "1 red — no close: FAIL false. fix them, then: "
            "sandbox make --close geardoor")
        self.assertEqual(self.closes(), [])          # nothing landed
        self.assertEqual(desk.drafts(self.ws)[0], [])  # nothing staged
        self.assertTrue(os.path.exists(make._open_path(self.ws, "geardoor")))
        # and the same close lands once the check is green again
        self._set_checks(["true"])
        ok, msg = make.close_session(self.ws, "geardoor", "tax table + 3 tests")
        self.assertTrue(ok, msg)

    def test_there_is_no_anyway_door(self):
        """rule R11: the refusal carries one door, and it is the check itself."""
        self._set_checks(["false"])
        make.open_session(self.ws, "geardoor", "the tax table")
        ok, msg = make.close_session(self.ws, "geardoor")
        self.assertFalse(ok)
        self.assertEqual([l for l in msg.splitlines() if "anyway" in l], [])
        self.assertNotIn("--anyway", open(
            os.path.join(REPO, "engine", "make.py"), encoding="utf-8").read())

    def test_a_close_with_no_checks_lands_and_says_the_costume_line(self):
        make.open_session(self.ws, "geardoor", "the tax table")
        ok, msg = make.close_session(self.ws, "geardoor", "tax table")
        self.assertTrue(ok, msg)
        self.assertEqual(msg.splitlines()[-1],
                         "nothing under ## checks — a ship with nothing "
                         "under it is a costume; add one line there")
        self.assertEqual(self.closes()[0]["checks"], "none")

    def test_an_empty_diff_still_says_attempted_after_a_green_run(self):
        self._set_checks(["true"])
        make.open_session(self.ws, "geardoor", "change nothing")
        ok, msg = make.close_session(self.ws, "geardoor")
        self.assertTrue(ok, msg)
        self.assertIn("attempted", msg)
        self.assertNotIn("confirmed", msg)


class TestTheTwoForms(TestMake):
    def test_open_never_takes_a_flag_as_its_intent(self):
        """--open --project NAME "intent": the intent is the words, never --project."""
        from engine import verbs
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = verbs.dispatch(self.ws, "make", ["--open", "--project", "geardoor", "band v — the vessel"])
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertIn("band v — the vessel", buf.getvalue())
        self.assertNotIn("— --project", buf.getvalue())

    def test_the_open_form_is_the_canonical_one(self):
        rc, out = _run(self.ws, ["--open", "add the tax table", "geardoor"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "session open on geardoor — add the tax table")

    def test_the_close_form_takes_the_name_beside_the_summary(self):
        make.open_session(self.ws, "geardoor", "the tax table")
        rc, out = _run(self.ws, ["--close", "geardoor", "--summary", "tax table"])
        self.assertEqual(rc, 0, out)
        self.assertIn("1 summary staged", out)

    def test_a_bare_intent_names_the_two_forms_and_exits_two(self):
        rc, out = _run(self.ws, ["add the tax table"])
        self.assertEqual(rc, 2)
        self.assertEqual(out.strip(), "a make opens with --open and closes "
                                      "with --close: sandbox make --open \"…\"")
        self.assertEqual([e for e in journal.read(self.ws)[0]
                          if e.get("op") == "make"], [])

    def test_make_with_nothing_at_all_says_the_same(self):
        rc, out = _run(self.ws, [])
        self.assertEqual(rc, 2)
        self.assertIn("a make opens with --open", out)

    def test_a_refusal_exits_one(self):
        """truth M5: a close with no make open is a refusal, not a usage
        mistake — the words refuse and the exit agrees."""
        rc, out = _run(self.ws, ["--close", "geardoor"])
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip(), "no make session open on geardoor")

    def test_a_name_the_workshop_never_met_refuses_with_one(self):
        rc, out = _run(self.ws, ["--open", "something", "ghostproject"])
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip(), "no project named ghostproject")


def _needle(*parts):
    """the four patterns, assembled at run time.

    Written whole they would be four more hits for the very grep below —
    this check has to be able to pass in the tree that carries it.
    """
    return "".join(parts)


class TestNoHeadlessBuilder(unittest.TestCase):
    def test_no_headless_builder(self):
        """slice 5's own check: the `-p` subprocess and the env var it read
        are gone from the engine and the vessel both."""
        needles = (_needle('"-', "p", '"'), _needle("--", "print"),
                   _needle("SANDBOX_", "CLAUDE_CMD"),
                   _needle("SANDBOX_", "MAKE_TIMEOUT"))
        argv = ["grep", "-rn"]
        for n in needles:
            argv += ["-e", n]
        r = subprocess.run(argv + ["engine/", "vessel/"],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "")
        self.assertEqual(r.returncode, 1)  # grep found nothing

    def test_the_verb_carries_no_builder_at_all(self):
        for gone in ("build", "_prompt", "CLAUDE_ENV", "TIMEOUT_ENV"):
            self.assertFalse(hasattr(make, gone), "make still carries %s" % gone)
        self.assertNotIn("subprocess", dir(make))


if __name__ == "__main__":
    unittest.main()
