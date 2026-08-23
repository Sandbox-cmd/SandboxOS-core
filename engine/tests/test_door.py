# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the door answers, and answers honestly."""
import os
import subprocess
import tempfile
import unittest

from engine import selfmap, verbs

from . import REPO


def run_cli(*args, **kw):
    """one run of the real door. stdin is a pipe by default — the suite has
    no terminal to lend, and a verb that needs one must say so."""
    env = dict(os.environ)
    home = kw.get("home")
    if home:
        env["SANDBOX_HOME"] = home
    env.pop("SANDBOX_TEST_KEY", None)
    return subprocess.run(
        [os.path.join(REPO, "sandbox"), *args], input=kw.get("input", ""),
        capture_output=True, text=True, timeout=60, env=env,
        cwd=kw.get("cwd"),
    )


class TestDoor(unittest.TestCase):
    def test_version_reads_the_file(self):
        with open(os.path.join(REPO, "VERSION"), encoding="utf-8") as f:
            want = "Sandbox OS " + f.read().strip()
        got = run_cli("version")
        self.assertEqual(got.returncode, 0)
        lines = got.stdout.strip().splitlines()
        self.assertEqual(lines[0], want)
        # the second line says which tree runs — one home is a ruling
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[1].startswith("from "), lines[1])

    def test_unknown_verb_refuses_plainly(self):
        got = run_cli("frobnicate")
        self.assertEqual(got.returncode, 2)
        self.assertIn("no verb named", got.stdout)
        self.assertIn("sandbox help", got.stdout)

    def test_help_promises_nothing_unbuilt(self):
        with open(os.path.join(REPO, "VERSION"), encoding="utf-8") as f:
            version = f.read().strip()
        got = run_cli("help")
        self.assertEqual(got.returncode, 0)
        self.assertIn("Sandbox OS " + version, got.stdout)

    def test_help_gives_every_verb_two_lines(self):
        """the index says what a verb does before it says what it costs —
        two lines, because one row could hold both only by cutting the half
        a person came for."""
        got = run_cli("help")
        self.assertEqual(got.returncode, 0)
        lines = got.stdout.splitlines()
        for name in sorted(verbs.TABLE):
            d = verbs.DECLARATIONS[name]
            first = "  %-10s %s" % (name, d["blurb"])
            second = "             %s · %s" % (selfmap.GATE_WORDS[d["gate"]],
                                               selfmap.scope_words(d["writes"]))
            self.assertIn(first, lines, name)
            self.assertEqual(lines[lines.index(first) + 1], second, name)

    def test_no_help_line_runs_past_a_terminal_row(self):
        got = run_cli("help")
        long = [l for l in got.stdout.splitlines() if len(l) > 80]
        self.assertEqual(long, [], "help runs past 80 columns: %s" % long)


class TestPluginDir(unittest.TestCase):
    """the marketplace's `command` source (R14), as a verb a person can run.

    It prints where the plugin lives and does nothing else — no key, no write,
    no workshop needed — because the host runs it at every session start and a
    source line that could change the record would be a hook by another name.
    """

    def test_it_prints_the_plugin_directory_and_exits_zero(self):
        from engine import vessel
        got = run_cli("plugin-dir")
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(got.stdout.strip(), vessel.PLUGIN)
        self.assertTrue(os.path.isdir(got.stdout.strip()))

    def test_it_writes_nothing_and_needs_no_key(self):
        d = verbs.DECLARATIONS["plugin-dir"]
        self.assertEqual(d["writes"], ())
        self.assertEqual(d["gate"], "none")
        self.assertIsNone(d["emits"])

    def test_it_answers_without_a_workshop(self):
        home = tempfile.mkdtemp(prefix="sbx9nows-")
        got = run_cli("plugin-dir", home=os.path.join(home, "nothing-here"))
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertFalse(os.path.exists(os.path.join(home, "nothing-here")))


class TestVerbHelp(unittest.TestCase):
    """`sandbox VERB --help` is the one flag every verb knows. It is answered
    at the door, above the unknown-flag refusal, so no verb body ever reads
    it as content — the scar that staged a draft whose whole body was the
    flag cannot come back through this door."""

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="sbx-help-")

    def test_every_verb_answers_help_with_exit_zero(self):
        for name in sorted(verbs.TABLE):
            got = run_cli(name, "--help", home=self.home)
            self.assertEqual(got.returncode, 0,
                             "%s --help exited %d: %s" % (name, got.returncode, got.stdout))
            self.assertEqual(got.stdout.strip(), selfmap.render_verb_help(name), name)

    def test_the_four_lines_and_the_page(self):
        got = run_cli("note", "--help", home=self.home)
        lines = got.stdout.strip().splitlines()
        self.assertEqual(len(lines), 5, lines)
        self.assertEqual(lines[0], verbs.DECLARATIONS["note"]["blurb"])
        self.assertTrue(lines[1].startswith("gate: "), lines[1])
        self.assertTrue(lines[2].startswith("writes: "), lines[2])
        self.assertTrue(lines[3].startswith("flags: "), lines[3])
        self.assertEqual(lines[4], "the page: docs/MANUAL.md")

    def test_a_verb_with_no_flags_still_answers(self):
        got = run_cli("doctor", "--help", home=self.home)
        self.assertEqual(got.returncode, 0)
        self.assertIn("flags: none", got.stdout)

    def test_help_is_not_a_content_flag(self):
        """--help is answered, never absorbed: it is not in FLAGS, and the
        verb body never sees it."""
        for spec in verbs.FLAGS.values():
            self.assertNotIn("--help", spec)
        got = run_cli("note", "--help", "what you found", home=self.home)
        self.assertEqual(got.returncode, 0)
        self.assertNotIn("waiting", got.stdout)


class TestThePipeRefusal(unittest.TestCase):
    """`echo k | sandbox VERB` — the refusal names the verb you typed and the
    exit code agrees with the words. resume returned 0 on it until 9.0; this
    is the pin that keeps that scar closed."""

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="sbx-pipe-")
        run_cli("init", home=cls.home)
        run_cli("note", "one thing waiting", home=cls.home)

    def test_the_landing_verbs_refuse_a_pipe_and_exit_one(self):
        for verb in ("approve", "resume"):
            got = run_cli(verb, home=self.home, input="k")
            self.assertEqual(got.returncode, 1, "%s: %s" % (verb, got.stdout))
            self.assertIn("real terminal", got.stdout, verb)
            self.assertIn("sandbox %s" % verb, got.stdout, verb)

    def test_the_pile_is_still_there_afterwards(self):
        got = run_cli("drafts", home=self.home)
        self.assertIn("one thing waiting", got.stdout)


class TestTheTargetRule(unittest.TestCase):
    """which project a bare verb binds to: --project, else where you stand,
    else the one that is on, else a refusal that names the candidates (the
    sh door's comment made true — scar 07-19)."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="sbx-target-")
        run_cli("init", home=self.home)
        for name in ("a", "b"):
            run_cli("project", "new", name, "the %s work" % name, home=self.home)
            run_cli("project", "on", name, home=self.home)

    def staged(self):
        from engine import desk
        pile, _ = desk.drafts(self.home)
        return [(d.get("project"), d.get("body")) for d in pile]

    def test_a_note_typed_inside_a_project_lands_on_that_project(self):
        got = run_cli("note", "found while standing in a", home=self.home,
                      cwd=os.path.join(self.home, "projects", "a"))
        self.assertEqual(got.returncode, 0, got.stdout)
        self.assertEqual(self.staged(), [("a", "found while standing in a")])

    def test_two_on_and_nowhere_to_stand_refuses_and_names_both(self):
        got = run_cli("note", "from nowhere", home=self.home, cwd=self.home)
        self.assertEqual(got.returncode, 2, got.stdout)
        self.assertEqual(got.stdout.strip(), "which project? you are standing "
                         "in none, and 2 are on: a, b — say: --project NAME")
        self.assertEqual(self.staged(), [])

    def test_the_flag_wins_over_where_you_stand(self):
        run_cli("note", "--project", "b", "said out loud", home=self.home,
                cwd=os.path.join(self.home, "projects", "a"))
        self.assertEqual(self.staged(), [("b", "said out loud")])

    def test_the_workshop_flag_still_reaches_the_workshop(self):
        got = run_cli("note", "--workshop", "about the whole place",
                      home=self.home, cwd=self.home)
        self.assertEqual(got.returncode, 0, got.stdout)
        self.assertEqual(self.staged(), [(None, "about the whole place")])

    def test_one_on_and_nowhere_to_stand_still_binds(self):
        run_cli("project", "off", "b", home=self.home)
        run_cli("note", "the only one on", home=self.home, cwd=self.home)
        self.assertEqual(self.staged(), [("a", "the only one on")])

    def test_the_door_promises_this(self):
        """the sh door says the working directory binds a verb to a project.
        that sentence is only true because of the rule above."""
        with open(os.path.join(REPO, "sandbox"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("the caller's working directory is load-bearing", text)
        self.assertIn("to the project you are standing in", text)


class TestPersonClean(unittest.TestCase):
    """no committed file carries a personal absolute path. The full lint
    (external private-terms list) arrives with row A6; this floor holds now."""

    # Needles are assembled, not written literally, so this file passes its
    # own lint.
    NEEDLES = ("/" + "Users" + "/", "/" + "home" + "/")

    def test_no_home_paths_in_tree(self):
        hits = []
        for dirpath, dirnames, filenames in os.walk(REPO):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for name in filenames:
                path = os.path.join(dirpath, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        text = f.read()
                except (UnicodeDecodeError, OSError):
                    continue
                if any(n in text for n in self.NEEDLES):
                    hits.append(os.path.relpath(path, REPO))
        self.assertEqual(hits, [], "personal paths in: %s" % hits)


if __name__ == "__main__":
    unittest.main()
