# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the README's pasted sitting, re-run instead of remembered.

the scar this closes is `f0a17fb` — "the README's loud line replaced for being
false". a transcript on the first screen is the strongest claim the page
makes, and a transcript nobody re-runs is the easiest one to let rot. so the
block between the sitting markers is parsed here, every `$` line is run
against the real door in a throwaway workshop, and the first line that differs
fails.

three things move between machines and are normalized on both sides: the home
directory (`~`), the version the plugin line prints, and the eight-character
digest the gate shows. the digest's identity is checked separately — the line
the key landed carries the same one the screen showed, which is the whole
point of printing it twice.
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
BEGIN = "<!-- sitting:begin"
END = "<!-- sitting:end -->"
HASH = re.compile(r"\b[0-9a-f]{8}\b")


def _text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def sitting_block(text=None):
    """the fenced lines between the two markers, fences dropped."""
    text = text if text is not None else _text(os.path.join(REPO, "README.md"))
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(BEGIN))
    stop = next(i for i, l in enumerate(lines) if l.startswith(END))
    return [l for l in lines[start + 1:stop] if not l.startswith("```")]


def steps(block):
    """[(argv, [line, …])] — one command and the output pasted under it."""
    out = []
    for line in block:
        if line.startswith("$ "):
            argv = shlex.split(line[2:])
            # the page shows the door by path once, then the shim's name.
            out.append((argv[1:] if argv[0].endswith("sandbox") else argv, []))
        elif out:
            out[-1][1].append(line)
    return out


def at_a_pty(argv, home):
    """one run of the real door, with a terminal and the rig's key."""
    env = dict(os.environ)
    env["HOME"] = home
    env["SANDBOX_HOME"] = os.path.join(home, "Sandbox")
    env["SANDBOX_TEST_KEY"] = "k"
    env.pop("NO_COLOR", None)
    master, slave = pty.openpty()
    try:
        return subprocess.run([DOOR] + list(argv), stdin=slave, env=env,
                              capture_output=True, text=True, timeout=120)
    finally:
        os.close(master)
        os.close(slave)


def normalized(lines, home, version):
    """the lines a reader could compare on any machine."""
    out = []
    for line in lines:
        line = line.replace(os.path.join(home, "Sandbox"), "~/Sandbox")
        line = line.replace(home, "~")
        line = line.replace(version, "<version>")
        line = HASH.sub("<hash>", line)
        out.append(line.rstrip())
    return out


class TestTheSittingIsReal(unittest.TestCase):
    """every line under a `$` in the README was printed by this build."""

    def setUp(self):
        self.block = sitting_block()
        self.steps = steps(self.block)
        self.version = _text(os.path.join(REPO, "VERSION")).strip()
        self.home = tempfile.mkdtemp(prefix="sbx9-sitting-")

    def test_the_block_is_a_walk_and_not_a_screenshot(self):
        self.assertGreaterEqual(len(self.steps), 5,
                                "the first screen stopped being a whole sitting")
        for argv, said in self.steps:
            self.assertTrue(argv, "a `$` line with no command")
            self.assertTrue(said, "%s is pasted with no output" % " ".join(argv))

    def test_every_pasted_line_is_printed_again_by_this_build(self):
        for argv, said in self.steps:
            run = at_a_pty(argv, self.home)
            got = normalized(run.stdout.splitlines(), self.home, self.version)
            want = normalized(said, self.home, self.version)
            self.assertEqual(
                want, got,
                "the README's sitting drifted at `sandbox %s` — re-run it in a "
                "probe workshop and paste what it says now" % " ".join(argv))

    def test_the_landed_line_carries_the_digest_the_screen_showed(self):
        """rule R12 as arithmetic: what was shown and what landed share one hash."""
        shown = [l for l in self.block if l.startswith("shown: ")]
        landed = [l for l in self.block if l.startswith("landed ")]
        self.assertTrue(shown and landed, "the sitting stopped showing the pile")
        pair = HASH.findall(shown[0]) + HASH.findall(landed[0])
        self.assertEqual(2, len(pair), "a digest went missing from the block")
        self.assertEqual(pair[0], pair[1],
                         "the block shows one digest and lands another")

    def test_the_sitting_was_captured_against_this_version(self):
        """the one place a version literal is allowed in the docs: a
        transcript. it is allowed because this line makes it a fact."""
        joined = "\n".join(self.block)
        self.assertIn(self.version, joined,
                      "the sitting was captured on another build — re-run it")


if __name__ == "__main__":
    unittest.main()
