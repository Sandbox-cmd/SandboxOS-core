# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the key at a terminal, through a pty: what is shown is what lands.

The rig gives the door a terminal (`pty.openpty`) and the character (
`SANDBOX_TEST_KEY`), and every consent it mints wears `hand: synthetic` — so
none of this can ever read back as a person. The pipe cases use no rig at
all: they are the refusal a script meets.
"""
import hashlib
import os
import pty
import select
import subprocess
import tempfile
import time
import unittest

from engine import journal

from . import REPO

DOOR = os.path.join(REPO, "sandbox")


def run(args, home, key=None, pipe=False):
    """one CLI run, either at a pty or down a pipe."""
    env = dict(os.environ)
    env["SANDBOX_HOME"] = home
    env.pop("SANDBOX_TEST_KEY", None)
    if key is not None:
        env["SANDBOX_TEST_KEY"] = key
    if pipe:
        return subprocess.run([DOOR] + args, input="k", capture_output=True,
                              text=True, env=env, timeout=60)
    master, slave = pty.openpty()
    try:
        return subprocess.run([DOOR] + args, stdin=slave, capture_output=True,
                              text=True, env=env, timeout=60)
    finally:
        os.close(master)
        os.close(slave)


def staged(home):
    p = os.path.join(home, journal.STATE_DIR, "staging.jsonl")
    if not os.path.exists(p):
        return b""
    with open(p, "rb") as f:
        return f.read()


def landed(home):
    events, _ = journal.read(home)
    return [e for e in events if e.get("cls") == "note"]


class Screen(unittest.TestCase):
    """the approve screen, read the way a person reads it."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="sbx9pty-")
        run(["init"], self.home)
        run(["project", "new", "geardoor", "the store's data"], self.home)
        run(["project", "on", "geardoor"], self.home)

    def note(self, body, project=None):
        args = ["note"] + (["--project", project] if project else []) + [body]
        got = run(args, self.home)
        self.assertEqual(got.returncode, 0, got.stdout)
        self.assertIn("waiting for your approval", got.stdout)

    def block(self, out):
        """the lines the digest is taken over: the numbered rows and the
        page line, everything printed before `shown:`."""
        lines = out.splitlines()
        return lines[:[n for n, l in enumerate(lines) if l.startswith("shown: ")][0]]

    def test_any_other_key_lands_nothing(self):
        self.note("a finding the machine made")
        before = staged(self.home)
        got = run(["approve"], self.home, key="x")
        self.assertEqual(got.returncode, 0)
        self.assertEqual(got.stdout.splitlines()[-1], "cancelled — nothing landed")
        self.assertEqual(staged(self.home), before)
        self.assertEqual(landed(self.home), [])

    def test_the_key_lands_one_and_the_landed_line_carries_the_hash(self):
        self.note("a finding the machine made")
        got = run(["approve"], self.home, key="k")
        self.assertEqual(got.returncode, 0, got.stdout)
        lines = got.stdout.splitlines()
        self.assertEqual(lines[0], " 1. [note] a finding the machine made")
        digest = hashlib.sha256("\n".join(self.block(got.stdout)).encode()).hexdigest()
        self.assertEqual(lines[1], "shown: %s" % digest[:8])
        self.assertEqual(lines[2], "press k to land this one · any other key cancels")
        self.assertEqual(lines[3], "landed 1 (shown %s)" % digest[:8])
        rows = landed(self.home)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["shown"], digest)
        self.assertEqual(rows[0]["hand"], "synthetic")
        self.assertEqual(staged(self.home), b"")

    def test_three_land_on_one_key_under_one_hash(self):
        for i in range(3):
            self.note("finding %d" % i)
        got = run(["approve"], self.home, key="k")
        self.assertEqual(got.returncode, 0, got.stdout)
        lines = got.stdout.splitlines()
        digest = hashlib.sha256("\n".join(self.block(got.stdout)).encode()).hexdigest()
        self.assertEqual(lines[4], "press k to land these 3 · any other key cancels")
        self.assertEqual(lines[5], "landed 3 (shown %s)" % digest[:8])
        self.assertEqual({r["shown"] for r in landed(self.home)}, {digest})

    def test_a_long_pile_pages_at_twenty(self):
        for i in range(25):
            self.note("finding %02d" % i)
        got = run(["approve"], self.home, key="k")
        self.assertEqual(got.returncode, 0, got.stdout)
        lines = got.stdout.splitlines()
        self.assertEqual(lines[20], "20 of 25 shown — land these, or narrow "
                                    "with: sandbox approve --project NAME")
        digest = hashlib.sha256("\n".join(self.block(got.stdout)).encode()).hexdigest()
        self.assertEqual(lines[22], "press k to land these 20 · any other key cancels")
        self.assertEqual(lines[23], "landed 20 (shown %s)" % digest[:8])
        self.assertEqual(len(landed(self.home)), 20)
        self.assertEqual(len(staged(self.home).splitlines()), 5)

    def test_approve_narrows_to_one_project(self):
        run(["project", "new", "other"], self.home)
        self.note("for geardoor", "geardoor")
        self.note("for other", "other")
        got = run(["approve", "--project", "other"], self.home, key="k")
        self.assertEqual(got.returncode, 0, got.stdout)
        self.assertEqual(got.stdout.splitlines()[0], " 1. [note] for other")
        self.assertEqual([r["body"] for r in landed(self.home)], ["for other"])
        self.assertEqual(len(staged(self.home).splitlines()), 1)
        self.assertNotIn("arrived while you read", got.stdout)

    def test_nothing_waiting_says_so(self):
        got = run(["approve"], self.home, key="k")
        self.assertEqual(got.returncode, 0)
        self.assertEqual(got.stdout.strip(),
                         "i found nothing waiting — no notes need your approval.")


class RealKey(unittest.TestCase):
    """no rig at all: the door gets a terminal of its own and one key is
    typed into it. This is the only path that runs the raw read on /dev/tty.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="sbx9key-")
        run(["init"], self.home)
        run(["note", "typed at a terminal"], self.home)

    def typed(self, args, char, wait_for="press k"):
        """spawn the door on a terminal of its own, then press one key.

        The key is pressed again every quarter second until the door answers.
        The raw read flushes whatever was typed before it started listening,
        which is the gate's own rule and worth keeping: a key pressed before
        the pile reached the screen is a key pressed over nothing.
        """
        import termios
        pid, fd = pty.fork()
        if pid == 0:                                  # the child is the door
            os.environ["SANDBOX_HOME"] = self.home
            os.environ.pop("SANDBOX_TEST_KEY", None)
            os.execve(DOOR, [DOOR] + args, os.environ)
        before = termios.tcgetattr(fd)
        out, presses, last = "", 0, 0.0
        deadline = time.time() + 60
        while time.time() < deadline:
            if select.select([fd], [], [], 0.1)[0]:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                out += chunk.decode("utf-8", "replace")
            if wait_for in out and time.time() - last > 0.25:
                os.write(fd, char.encode())
                presses += 1
                last = time.time()
        after = termios.tcgetattr(fd)
        os.close(fd)
        _pid, status = os.waitpid(pid, 0)
        self.assertTrue(presses, "the prompt never arrived: %r" % out)
        return os.waitstatus_to_exitcode(status), out, before, after

    def test_a_real_key_read_from_the_terminal_lands_the_pile(self):
        rc, out, _b, _a = self.typed(["approve"], "k")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.replace("\r\n", "\n").count("landed 1 (shown "), 1, out)
        rows = landed(self.home)
        self.assertEqual(len(rows), 1)
        self.assertNotIn("hand", rows[0])     # a real hand carries no stamp
        self.assertEqual(staged(self.home), b"")

    def test_a_real_other_key_cancels(self):
        rc, out, _b, _a = self.typed(["approve"], "x")
        self.assertEqual(rc, 0, out)
        self.assertIn("cancelled — nothing landed", out)
        self.assertEqual(landed(self.home), [])

    def test_the_terminal_is_handed_back_as_it_was(self):
        """the settings are restored on the way out: the shell that spawned
        it still echoes, which is what a person notices when it is missed."""
        rc, out, before, after = self.typed(["approve"], "k")
        self.assertEqual(rc, 0, out)
        self.assertEqual(before[3], after[3])   # the local flags, echo among them


class Pipe(unittest.TestCase):
    """a pipe refuses, and the exit code agrees with the words (the scar:
    resume printed the refusal and returned 0)."""

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="sbx9pipe-")
        run(["init"], cls.home)
        run(["note", "something waiting"], cls.home)

    def test_approve_down_a_pipe_refuses_and_exits_one(self):
        got = run(["approve"], self.home, pipe=True)
        self.assertEqual(got.returncode, 1)
        self.assertEqual(got.stdout.strip(),
                         "landing needs your 'k' at a real terminal — run: sandbox approve")
        self.assertEqual(landed(self.home), [])

    def test_resume_down_a_pipe_refuses_and_exits_one(self):
        got = run(["resume"], self.home, pipe=True)
        self.assertEqual(got.returncode, 1)
        self.assertEqual(got.stdout.strip(),
                         "landing needs your 'k' at a real terminal — run: sandbox resume")
        self.assertEqual(landed(self.home), [])

    def test_the_refusal_names_the_verb_you_typed(self):
        for verb in ("approve", "resume"):
            got = run([verb], self.home, pipe=True)
            self.assertIn("real terminal", got.stdout)
            self.assertIn(verb, got.stdout)


if __name__ == "__main__":
    unittest.main()
