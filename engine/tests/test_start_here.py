# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""walking START-HERE instead of reading it.

the page's DO blocks are parsed out of the markdown and run in a throwaway
workshop, in the order a reader meets them, twice: once at a `pty` with the
rig's key, once down a pipe where the gated verbs must refuse and exit 1. the
SEE strings the page promises are asserted against what the door actually
printed.

one step is skipped and the skip is named: step 5 opens a Claude Code session,
which is a person's host and not this suite's. the page's own IF-NOT for a
reader without `claude` is run in its place, and the test asserts that
fallback command is still on the page — so the skip stays honest rather than
becoming a hole.

the scar behind this file: 8.2.3's step 4 described a walk the engine never
performed, and nothing in the suite noticed, because nobody ever walked the
page.
"""
import os
import pty
import re
import shlex
import subprocess
import tempfile
import unittest

from . import REPO

DOOR = os.path.join(REPO, "sandbox")
PAGE = os.path.join(REPO, "docs", "START-HERE.md")
STEP = re.compile(r"^## (\d+) · (.+)$")
# the session step: a host this suite has no business opening.
SESSION_STEP = 5
FALLBACK = 'make --open "add a README to this project saying what it is for"'
# the verbs on this page that read a key from the terminal itself.
GATED = ("approve", "ship")


def _text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def steps(text=None):
    """{n: [command line, …]} — every DO block's lines, per numbered step."""
    text = text if text is not None else _text(PAGE)
    out, n, in_do, in_fence = {}, None, False, False
    for line in text.splitlines():
        m = STEP.match(line)
        if m:
            n, in_do, in_fence = int(m.group(1)), False, False
            out[n] = []
            continue
        if n is None:
            continue
        if line.strip() == "DO" or line.startswith("DO —"):
            in_do = True
            continue
        if line.startswith("```"):
            if in_do and not in_fence:
                in_fence = True
                continue
            if in_fence:
                in_fence, in_do = False, False
                continue
        if in_fence and line.strip():
            out[n].append(line.strip())
    return out


def run(argv, home, key=None, pipe=False):
    """one run of the real door — at a terminal, or down a pipe."""
    env = dict(os.environ)
    env["HOME"] = home
    env["SANDBOX_HOME"] = os.path.join(home, "Sandbox")
    env.pop("SANDBOX_TEST_KEY", None)
    if key is not None:
        env["SANDBOX_TEST_KEY"] = key
    if pipe:
        return subprocess.run([DOOR] + list(argv), input="k", env=env,
                              capture_output=True, text=True, timeout=120)
    master, slave = pty.openpty()
    try:
        return subprocess.run([DOOR] + list(argv), stdin=slave, env=env,
                              capture_output=True, text=True, timeout=120)
    finally:
        os.close(master)
        os.close(slave)


def argv_of(line, home):
    """a DO line as arguments to the door, with `~` resolved."""
    parts = shlex.split(line.replace("~", home))
    return parts[1:] if parts and parts[0].endswith("sandbox") else parts


class Walk(unittest.TestCase):
    """the shared harness: one workshop, walked once, output kept per step."""

    @classmethod
    def setUpClass(cls):
        cls.page = _text(PAGE)
        cls.steps = steps(cls.page)
        cls.home = tempfile.mkdtemp(prefix="sbx9-starthere-")
        cls.out = {}
        cls.skipped = []
        cls.walk(cls.home, key="k")

    @classmethod
    def project(cls, *parts):
        return os.path.join(cls.home, "Sandbox", "projects", "hello", *parts)

    @classmethod
    def walk(cls, home, key):
        """every DO line, in page order, with the reader's own edits between."""
        for n in sorted(cls.steps):
            cls.out[n] = []
            for line in cls.steps[n]:
                if n == SESSION_STEP and not line.startswith("sandbox"):
                    cls.skipped.append(line)
                    continue
                argv = argv_of(line, home)
                if not argv:
                    continue
                cls.out[n].append((line, run(argv, home, key=key)))
            cls.between(n, home)

    @classmethod
    def between(cls, n, home):
        """what the page tells the reader to do with their own hands."""
        if n == SESSION_STEP - 1:
            # the session this suite does not open; the page's IF-NOT instead.
            run(shlex.split(FALLBACK), home, key="k")
            with open(cls.project("README.md"), "w", encoding="utf-8") as fh:
                fh.write("# hello\n\nwhat this project is for.\n")
        if n == SESSION_STEP:
            # step 6 tells the reader to put one line under `## checks`.
            p = cls.project("PROJECT.md")
            text = _text(p).replace("## checks\n", "## checks\ntest -f README.md\n")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)

    def out_of(self, n):
        return "\n".join(r.stdout for _, r in self.out[n])

    def codes(self, n):
        return [r.returncode for _, r in self.out[n]]


class TestTheNineSteps(Walk):
    def test_the_page_still_has_nine_numbered_steps(self):
        self.assertEqual(list(range(1, 10)), sorted(self.steps),
                         "the walk and the page disagree about the steps")
        for n in sorted(self.steps):
            self.assertTrue(self.steps[n], "step %d has no DO block" % n)

    def test_step_1_opens_a_workshop_and_writes_the_shim(self):
        out = self.out_of(1)
        self.assertIn("opened your workshop at", out)
        self.assertIn("day 0. nothing on the record yet.", out)
        self.assertIn("ready. nobody's tool.", out)
        self.assertIn("one shim written:", out)
        self.assertEqual([0, 0], self.codes(1))

    def test_step_2_prints_its_rows_and_its_legend(self):
        out = self.out_of(2)
        for row in ("python 3.9 or newer", "git on the path", "the record reads",
                    "no torn lines", "project contracts parse"):
            self.assertIn(row, out, row)
        self.assertIn("ok = proved · LOOK = needs you · ? = could not read", out)
        for row in ("ok = proved", "? = could not read"):
            self.assertIn(row, self.page, "step 2's SEE dropped the legend")

    def test_step_3_names_the_project_and_says_nothing_needs_you(self):
        out = self.out_of(3)
        self.assertIn("project hello is born", out)
        self.assertIn("hello is on — bare verbs land there", out)
        self.assertIn("nothing needs you.", out)

    def test_step_4_stages_first_and_lands_on_the_key(self):
        """the whole point of the page, and the thing 8.2.3 got wrong."""
        out = self.out_of(4)
        self.assertIn("waiting for your approval — approve it: sandbox approve", out)
        self.assertIn("waiting: [note] the first thing worth remembering", out)
        self.assertIn("press k to land this one · any other key cancels", out)
        self.assertIn("landed 1 (shown ", out)

    def test_step_4s_fingerprint_is_the_same_on_both_lines(self):
        out = self.out_of(4)
        shown = re.search(r"^shown: ([0-9a-f]{8})$", out, re.M)
        landed = re.search(r"^landed 1 \(shown ([0-9a-f]{8})\)$", out, re.M)
        self.assertTrue(shown and landed, "the approve screen changed shape")
        self.assertEqual(shown.group(1), landed.group(1))
        self.assertIn("fingerprints exactly the lines above it", self.page,
                      "step 4 stopped explaining the fingerprint")

    def test_step_5_skips_the_session_and_says_which_line_it_skipped(self):
        self.assertIn("cd ~/Sandbox", self.skipped)
        self.assertIn("claude", self.skipped)
        self.assertIn(FALLBACK.split('"')[0].strip(), self.page,
                      "step 5's IF-NOT stopped naming the terminal fallback")
        self.assertIn(FALLBACK, self.page.replace("\n", " "),
                      "the command this walk runs in the session's place left the page")

    def test_step_5_closes_on_a_computed_diff_and_lands_the_summary(self):
        out = self.out_of(5)
        self.assertIn("confirmed — 1 file(s) changed on hello", out)
        self.assertIn("README.md", out)
        self.assertIn("1 summary staged, waiting on your keypress", out)
        self.assertIn("[make-summary] make: hello: wrote the README", out)
        self.assertIn("landed 1 (shown ", out)

    def test_step_6_ratifies_the_checks_and_ships(self):
        out = self.out_of(6)
        self.assertIn("ratified — your k is on these exact checks", out)
        self.assertIn("shipped — 1 check(s) green, on the record", out)
        self.assertEqual([0], self.codes(6))

    def test_step_6_quotes_the_heading_trap_the_engine_really_prints(self):
        """a check appended at the end of PROJECT.md lands under `## notes`."""
        p = self.project("PROJECT.md")
        keep = _text(p)
        try:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("# hello\ngoal: g\nstate: active\n\n## checks\n\n"
                         "## notes\ntest -f README.md\n")
            r = run(["ship", "hello"], self.home, key="k")
            self.assertEqual(1, r.returncode)
            self.assertIn("looks like a check — move it", r.stdout)
            self.assertIn("under ## checks", r.stdout)
            self.assertIn("a line under ## notes looks like a check", self.page,
                          "step 6's IF-NOT stopped quoting the trap")
        finally:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(keep)

    def test_step_7_reads_the_note_back_out_of_the_journal(self):
        out = self.out_of(7)
        self.assertIn("[claimed] [human] the first thing worth remembering", out)
        self.assertTrue(os.path.exists(
            os.path.join(self.home, "Sandbox", ".sandbox", "journal.jsonl")),
            "step 7 points at a file the walk never produced")

    def test_step_8_writes_one_file_that_says_what_it_is(self):
        out = self.out_of(8)
        self.assertIn("not redacted — 0 span(s) would go under --redact", out)
        # the verb prints the path with `~` for a home (A#11); the walk runs
        # in a scratch home, so expanduser is the one that reads either.
        path = os.path.expanduser(out.strip().splitlines()[-1])
        self.assertTrue(os.path.exists(path), path)
        self.assertIn("this is a file — opening it leaves nothing on the record",
                      _text(path))
        self.assertIn("this is a file — opening it leaves nothing on the record",
                      " ".join(self.page.split()),
                      "step 8 stopped quoting the footer")

    def test_step_9_leaves_the_reader_holding_a_build(self):
        out = self.out_of(9)
        self.assertIn("kept: hello (session-kept) — reuse it with: sandbox use hello",
                      out)
        self.assertIn("the shape i want to start from next time", out)


class TestThePipeRefuses(unittest.TestCase):
    """the second walk: no terminal, and the gated steps say so with exit 1."""

    def setUp(self):
        self.page = _text(PAGE)
        self.steps = steps(self.page)
        self.home = tempfile.mkdtemp(prefix="sbx9-starthere-pipe-")
        run(["init"], self.home, key="k")
        run(["project", "new", "hello", "see how this feels"], self.home, key="k")
        run(["project", "on", "hello"], self.home, key="k")
        # ship's own refusal comes first when `## checks` is empty; the page's
        # walk arrives here with a check under the heading, so the pipe meets
        # the gate rather than the costume line.
        p = os.path.join(self.home, "Sandbox", "projects", "hello", "PROJECT.md")
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text.replace("## checks\n", "## checks\ntest -d .\n"))

    def test_every_gated_do_line_refuses_down_a_pipe_and_exits_one(self):
        seen = 0
        for n in sorted(self.steps):
            for line in self.steps[n]:
                argv = argv_of(line, self.home)
                if not argv or argv[0] not in GATED:
                    continue
                seen += 1
                r = run(argv, self.home, pipe=True)
                self.assertEqual(1, r.returncode,
                                 "%s exited %d down a pipe" % (line, r.returncode))
                self.assertIn("a real terminal", r.stdout, line)
        self.assertGreaterEqual(seen, 2, "the page stopped walking a gated verb")

    def test_the_page_shows_the_pipe_refusal_it_will_meet(self):
        self.assertIn("landing needs your 'k' at a real terminal — run: "
                      "sandbox approve", self.page)
        self.assertIn("echo k | sandbox approve", self.page)

    def test_a_note_down_a_pipe_still_stages(self):
        """the split the page calls the whole design: staging needs no key."""
        r = run(["note", "the first thing worth remembering"], self.home, pipe=True)
        self.assertEqual(0, r.returncode)
        self.assertIn("waiting for your approval", r.stdout)
        d = run(["drafts"], self.home, pipe=True)
        self.assertIn("waiting: [note] the first thing worth remembering", d.stdout)


if __name__ == "__main__":
    unittest.main()
