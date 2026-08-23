# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the hygiene pins: every file the engine opens, it closes.

a bare `open(...)` leaves the handle to the collector, which is why the suite
runs under `-W error::ResourceWarning` — but that only catches a path a test
walks. this file reads the source instead, so a site nothing exercises is
still held.

two readings of the same rule, on purpose. the ast reading is the pin: it
knows a call from a comment and from a string, and it knows which calls are a
`with` statement's own. the line reading mirrors the shell grep the build spec
quotes, so the command in the spec keeps meaning what it says.
"""
import ast
import os
import unittest

from . import REPO

ENGINE = os.path.join(REPO, "engine")


def engine_sources():
    """engine/*.py — the modules, and not the suite that drives them."""
    return [os.path.join(ENGINE, n) for n in sorted(os.listdir(ENGINE))
            if n.endswith(".py")]


def _text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _held_by_a_with(tree):
    """every call node that is a `with` statement's own context expression."""
    held = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                held.add(id(item.context_expr))
    return held


def bare_open_sites(path):
    """`path:lineno` for every builtin `open(...)` no `with` is holding.

    `os.open` is out of it: it hands back a file descriptor, not a handle, and
    the two sites that use it close theirs by hand.
    """
    tree = ast.parse(_text(path), os.path.basename(path))
    held = _held_by_a_with(tree)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "open"):
            continue
        if id(node) in held:
            continue
        out.append("%s:%d" % (os.path.relpath(path, REPO), node.lineno))
    return out


def grep_sites(path):
    """the shell grep the build spec quotes, run in python.

    `grep -rn 'open(' engine/*.py | grep -v 'with ' | grep -v 'os.open\\|def \\|#'`
    """
    out = []
    for n, line in enumerate(_text(path).splitlines(), 1):
        if "open(" not in line:
            continue
        if "with " in line:
            continue
        if "os.open" in line or "def " in line or "#" in line:
            continue
        out.append("%s:%d" % (os.path.relpath(path, REPO), n))
    return out


class TestEveryOpenIsHeld(unittest.TestCase):
    def test_no_bare_open_in_the_engine(self):
        loose = []
        for path in engine_sources():
            loose += bare_open_sites(path)
        self.assertEqual(loose, [], "these open a file and let go of it: %s"
                         % loose)

    def test_the_shell_grep_agrees(self):
        """the spec's own command prints nothing — the pin above is what the
        grep would have caught, read the way a person would run it."""
        loose = []
        for path in engine_sources():
            loose += grep_sites(path)
        self.assertEqual(loose, [], loose)

    def test_the_reading_finds_a_planted_one(self):
        """a pin that cannot fail is a costume: the ast reading is shown a
        bare open, a held one, a comment, a string and `os.open`."""
        import tempfile
        src = ('import os\n'
               'def a(p):\n'
               '    return open(p).read()\n'
               'def b(p):\n'
               '    with open(p) as f:\n'
               '        return f.read()\n'
               'def c(p):\n'
               '    # open(p) in a comment\n'
               '    note = "open(p) in a string"\n'
               '    fd = os.open(p, os.O_RDONLY)\n'
               '    os.close(fd)\n'
               '    return note\n')
        d = tempfile.mkdtemp(prefix="sbx9hyg-")
        p = os.path.join(d, "planted.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(src)
        self.assertEqual([s.rsplit(":", 1)[1] for s in bare_open_sites(p)], ["3"])
        # the grep is the blunter of the two: it reads lines, so the sentence
        # in a string counts as a site. that is why the ast reading is the pin
        # and the grep is the command a person can type.
        self.assertEqual([s.rsplit(":", 1)[1] for s in grep_sites(p)], ["3", "9"])

    def test_the_two_os_open_sites_close_their_own_descriptor(self):
        """gate.py takes a descriptor on the terminal itself; it is closed on
        every path out, which is what keeps it out of the pin above."""
        text = _text(os.path.join(ENGINE, "gate.py"))
        self.assertEqual(text.count("os.open("), 2)
        self.assertEqual(text.count("os.close("), 2)


if __name__ == "__main__":
    unittest.main()
