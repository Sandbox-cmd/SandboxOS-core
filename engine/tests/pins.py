# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the pin map, read in both forms the suite actually writes (repair S4).

a pin is a string a test holds a source line to. the first draft of this map
was a grep for `assertIn`, and it missed a whole form: the pins written as
`assertTrue(any("…" in l for l in lines))`, fifteen of them today, were
invisible to it. so the map is read with the parser instead of a pattern, and
both forms are named here rather than in a spec that goes stale.

run it: `python3 -m engine.tests.pins`. it prints one line per pin — the test
that holds it and the source line it lands on — and a tail that counts the
ones no source carries.
"""
import ast
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS = os.path.join(REPO, "engine", "tests")

# a string a test supplies and then reads back: it pins nothing, because the
# test wrote it. named here so the count of unresolved pins stays honest.
TEST_DATA = (
    "built the thing", "precious", "drop me", "textual now",
    "the tax rule is 5%", "a landed fact", "migration %d", "the store",
    "see how this feels", "the first thing worth remembering",
    "one thing waiting",
    # 9.0: bodies these tests wrote, read back through a projection — the
    # shape around them is pinned elsewhere; the words are the test's own.
    "the count is 12", "the count is 11", "smuggled",
    "band v — the vessel", "— --project",
    "[checked] [machine] the prefix is per brand",
    "- [checked] [machine] the prefix is per brand",
    "the fact: [struck] [machine] [synthetic] the count is 12",
    "during session: sess-9 (opened",
    "supersedes: the count is 11",
    # 9.0, the plugin: the transcript bodies the sweep test writes and then
    # reads back out of the staging pile.
    "finding: the scrub refuses its own card",
    "ruling: the close always refuses on red",
    "the scrub refuses its own card",
    "close refuses on red",
)


def _text(path):
    """read one file whole and close it — every reader here goes through this."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _strings_under(node):
    """every `"x" in y` and `assertIn("x", …)` string inside one call."""
    out = []
    for sub in ast.walk(node):
        if (isinstance(sub, ast.Compare) and len(sub.ops) == 1
                and isinstance(sub.ops[0], ast.In)
                and isinstance(sub.left, ast.Constant)
                and isinstance(sub.left.value, str)):
            out.append(sub.left.value)
    return out


def pins_in(path):
    """[(lineno, phrase, form)] for one test file, both forms."""
    tree = ast.parse(_text(path), path)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        name = node.func.attr
        if name in ("assertIn", "assertNotIn"):
            arg = node.args[0] if node.args else None
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                out.append((node.lineno, arg.value, name))
        elif name == "assertTrue":
            for s in _strings_under(node):
                out.append((node.lineno, s, "assertTrue-any"))
    return sorted(out)


def pins():
    """the whole map: [(test_rel, lineno, phrase, form)]."""
    out = []
    for name in sorted(os.listdir(TESTS)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        rel = os.path.join("engine", "tests", name).replace(os.sep, "/")
        for lineno, phrase, form in pins_in(os.path.join(TESTS, name)):
            out.append((rel, lineno, phrase, form))
    return out


def _sources():
    out = []
    for base in ("engine", "vessel", "docs"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, base)):
            dirnames[:] = [d for d in dirnames
                           if d not in ("__pycache__", "tests", "voice_fixtures")]
            for n in sorted(filenames):
                if n.endswith((".py", ".md", ".json")):
                    out.append(os.path.join(dirpath, n))
    out += [os.path.join(REPO, "README.md"), os.path.join(REPO, "CHANGELOG.md"),
            os.path.join(REPO, "sandbox")]   # the sh door is source a test pins
    return [p for p in out if os.path.exists(p)]


def resolve(phrase, sources=None):
    """the source lines this phrase pins, as `path:lineno` — empty when none."""
    out = []
    for path in sources if sources is not None else _sources():
        try:
            text = _text(path)
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if phrase in line:
                out.append("%s:%d" % (os.path.relpath(path, REPO).replace(os.sep, "/"), n))
    return out


def unresolved(rows=None):
    """the pins no source carries and that nothing names as test data."""
    sources = _sources()
    out = []
    for rel, lineno, phrase, form in rows if rows is not None else pins():
        if phrase in TEST_DATA or len(phrase) < 4:
            continue
        if not resolve(phrase, sources):
            out.append((rel, lineno, phrase, form))
    return out


def main():
    rows = pins()
    sources = _sources()
    forms, loose = {}, 0
    for rel, lineno, phrase, form in rows:
        forms[form] = forms.get(form, 0) + 1
        where = resolve(phrase, sources)
        if not where and phrase not in TEST_DATA:
            loose += 1
        print("%-34s %-14s %-46r %s"
              % ("%s:%d" % (rel, lineno), form, phrase[:44],
                 where[0] if where else "(no source line)"))
    print("pins: %d, by form %s; %d carried by no source line"
          % (len(rows), sorted(forms.items()), loose))
    return 0


if __name__ == "__main__":
    sys.exit(main())
