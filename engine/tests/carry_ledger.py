# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the carry ledger: every 8.2.3 test either still runs, or is retired by name.

the scar this closes recurred twice — a body crossed into the next one without
a test that had been holding something, and the thing it held came back. so
the baseline is not a list anyone typed: it is read out of the tag itself,
`git show v8.2.3:engine/tests/<file>`, every file, parsed for its test method
names. today's suite is parsed the same way, and the two sets are diffed.

a name that is gone must appear in CHANGELOG.md — that is the whole rule. a
rename is a retirement plus a birth, and saying so out loud is the point: the
CHANGELOG is where a reader finds out what stopped being checked.

run it: `python3 engine/tests/carry_ledger.py`. it prints one line and exits 1
when a retired name is nowhere in the CHANGELOG.
"""
import ast
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAG = "v8.2.3"
TESTS = "engine/tests"


def _text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _git(*args):
    return subprocess.run(("git", "-C", REPO) + args, capture_output=True, text=True)


def tag_is_reachable(tag=TAG):
    """true when the tag this ledger reads from is in this clone."""
    return _git("rev-parse", "--verify", "--quiet", tag + "^{commit}").returncode == 0


def _names(src, where):
    """every `def test…` in one file, however deep it sits."""
    out = set()
    for node in ast.walk(ast.parse(src, where)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name.startswith("test"):
            out.add(node.name)
    return out


def baseline(tag=TAG):
    """8.2.3's test names, read out of the tag rather than out of a list."""
    listed = _git("ls-tree", "-r", tag, "--name-only", TESTS)
    out = set()
    for rel in listed.stdout.split():
        if not rel.endswith(".py"):
            continue
        shown = _git("show", "%s:%s" % (tag, rel))
        if shown.returncode == 0:
            out |= _names(shown.stdout, rel)
    return out


def today():
    d = os.path.join(REPO, TESTS)
    out = set()
    for name in sorted(os.listdir(d)):
        if name.endswith(".py"):
            out |= _names(_text(os.path.join(d, name)), name)
    return out


def ledger(tag=TAG):
    """`{carried, retired, new, unnamed}` — unnamed is the failure set."""
    old, new = baseline(tag), today()
    changelog = _text(os.path.join(REPO, "CHANGELOG.md"))
    retired = sorted(old - new)
    return {"carried": sorted(old & new), "retired": retired,
            "new": sorted(new - old),
            "unnamed": [n for n in retired if n not in changelog]}


def line(rows):
    return "carried %d, retired %d (named in CHANGELOG), new %d" % (
        len(rows["carried"]), len(rows["retired"]), len(rows["new"]))


def main():
    if not tag_is_reachable():
        print("%s is not in this clone — the ledger has nothing to read from" % TAG)
        return 0
    rows = ledger()
    print(line(rows))
    if rows["unnamed"]:
        print("retired and nowhere in CHANGELOG.md:")
        for n in rows["unnamed"]:
            print("  " + n)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
