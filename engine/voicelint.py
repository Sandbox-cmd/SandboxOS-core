# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the voice lint: one cut-list, read from the soul, over every text a person meets.

stdlib only. importable, and runnable as `python3 -m engine.voicelint PATH…`.

the list of forbidden phrases lives in `soul/voice.md` with a reason per
phrase; this module parses it and nothing here re-types it. the rule every
check obeys: a check that measures shape gates; a proxy for meaning reports.
density counts negators, which is a proxy, so it prints a smell line; stacked
and naked prohibitions are exact, so they gate.

the checks:

  A  forbidden phrases, over engine/, vessel/, soul/, docs/, CHANGELOG.md,
     README.md and both plugin json files
  B  negation — density (smell), stacked (gate), naked (gate)
  C  lint-string — every printed literal in engine/*.py and guard.py held to
     a row of `soul/surfaces.md`
  D  docstrings open lowercase
  E  a short list of words the specs use and no printed string may carry

every exemption is a row in EXEMPTIONS with its reason, and `report()` carries
them out so a reader can see what the green run skipped.
"""
import argparse
import ast
import os
import random
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUL = os.path.join(REPO, "soul")
TABLE_HEADING = "## forbidden phrases, with reasons"

# the four ruled signal words: FAIL, doctor's LOOK, the statusline pill whose
# caps are its die-cut shape, and UNVERIFIED (gate 3, 2026-08-22; R23).
CAPS_ALLOWED = ("FAIL", "LOOK", "DRAFTS", "UNVERIFIED")  # R23

# argument placeholders in a usage line. the caps are the placeholder's shape:
# `sandbox save PATH` says "your own path goes here" rather than shouting.
# docs/MANUAL.md, README.md and docs/START-HERE.md spell the same placeholders
# the same way, so lowering them in the engine would make the tool and its own
# pages disagree about what to type. `PATH` doubles as the shell variable the
# setup line names, and the case there is the variable's. WHO and BUILD joined
# the list with R26's sweep: the shelf's pull-witnessed line asks for a person
# and a build by name, and it asked in the superseded `<who>` shape.
CAPS_PLACEHOLDERS = ("NAME", "PATH", "DIR", "ID", "K", "N", "VALUE",
                     "WHO", "BUILD")

# words the specs use for parts of the machine; a printed line uses the thing
# instead (experience.md principle 7). soul/ and docs/ prose and law/ keep them.
SPEC_ONLY_WORDS = ("desk", "wall", "seam", "ink", "body", "amana")

CEILING = 2.5  # negators per 100 words — ruled at gate 2; a smell until 8.4.0

NEGATOR = re.compile(
    r"\b(never|no|not|don't|dont|nothing|nobody|none|nor|without|neither"
    r"|nowhere|cannot|can't|won't|isn't|aren't|doesn't|didn't|mustn't|must not)\b",
    re.I)
PROHIBIT = re.compile(r"\b(never|don't|dont|do not|must not|mustn't)\b", re.I)
REASON = re.compile(
    r"\b(because|since|so that|so the|so a|so it|so you|so i|which is why)\b"
    r"|—\s*\S+(\s+\S+){3,}", re.I)


# ---------------------------------------------------------------- exemptions

class Exemption(object):
    """one skipped region, its checks, and the reason it is skipped.

    `start` opens the region and `until` closes it; when `until` is None the
    region is the one matching line. `checks` names which checks the region
    is out of; every other check still reads it.
    """

    def __init__(self, path, start, until, checks, why, clears=None):
        self.path = path
        self.start = re.compile(start)
        self.until = re.compile(until) if until else None
        self.checks = checks
        self.why = why
        self.clears = clears  # the pull that ends the exemption, when there is one

    def __repr__(self):
        return "<exempt %s %s (%s)>" % (self.path, "/".join(self.checks), self.why)


# surface: 17
# every `why` below is a doc sentence: it prints in the exemption report a
# reader opens to see what the green run skipped.
EXEMPTIONS = (
    Exemption("soul/voice.md", r"^" + re.escape(TABLE_HEADING), None,
              ("forbidden",), "the table is the list's home: it names the "
              "words in order to name the reason"),
    Exemption("soul/voice.md", r"^\s*\|", None,
              ("forbidden",), "the table's rows are the list itself"),
    Exemption("soul/*.md", r"^\s*(pair — )?before:", r"^\s*after:",
              ("forbidden", "negation", "caps"),
              "a pair's before-line wears the voice the page is replacing; it "
              "is the exhibit, not the page's own words"),
    Exemption("vessel/plugin/output-styles/across-the-desk.md",
              r"are marketing, and marketing is off", None,
              ("forbidden",),
              "the style names two of the cut words as its examples; the list "
              "itself lives in soul/voice.md, with a reason per phrase"),
    Exemption("vessel/plugin/agents/voicer.md",
              r"\*\*the word list\.\*\*", r"^\s*$",
              ("forbidden",),
              "the voicer is the one seat that needs the list in hand; the "
              "brief names soul/voice.md as where the reasons live"),
    Exemption("vessel/plugin/crew.json",
              r"\*\*the word list\.\*\*", r"plurals, stacked flourishes",
              ("forbidden",),
              "the voicer's word list, as the data the brief is rendered "
              "from; the same two lines, and the same reason"),
    Exemption("docs/START-HERE.md", r"^\s*(DO|SEE|IF-NOT)\b", None,
              ("negation", "caps"),
              "the three step words of the tutorial in docs/START-HERE.md are "
              "ruled in (gate 2): they are a form the reader follows rather "
              "than a sentence they read"),
)

# whole directories skipped, with the reason.
SKIP_DIRS = {
    "__pycache__": "compiled bytes, not text",
    ".git": "not shipped text",
    "voice_fixtures": "the fixtures wear the words they test, on purpose",
}
# whole trees never walked.
SKIP_TREES = {
    "law": "hash-pinned; amending a law is its own ceremony",
}
SKIP_FILES = {
    "manifest.json": "hashes, not sentences",
    "manifest.json.minisig": "a signature",
}

# the walk derives its directories rather than listing them, so a new tree of
# text joins it the day it lands instead of being quietly unread.
WALK_FILES = ("README.md", "CHANGELOG.md",
              os.path.join(".claude-plugin", "marketplace.json"),
              os.path.join("vessel", "plugin", ".claude-plugin", "plugin.json"))
TEXT_SUFFIXES = (".md", ".py", ".json", ".txt", ".sh")

# the instruction texts the negation checks read: what a person is told to be.
INSTRUCTION_FILES = (
    "vessel/claude-code/CLAUDE.md",
    "vessel/plugin/output-styles/across-the-desk.md",
)

# a table whose rows are the page's prose, and the columns whose shape (rather
# than whose sentences) carries the negation. row 21's `avoid — and why` cell
# is a forbidden move stated as one; counting it measures the table, not the page.
COLUMN_SKIP = {
    "soul/surfaces.md": ("first person", "avoid — and why"),
}


def _text(path):
    """read one file whole and close it — every reader here goes through this."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _rel(path):
    return os.path.relpath(os.path.abspath(path), REPO).replace(os.sep, "/")


def exemptions_for(rel, check):
    out = []
    for ex in EXEMPTIONS:
        if check not in ex.checks:
            continue
        if ex.path == rel:
            out.append(ex)
        elif ex.path.endswith("/*.md") and rel.startswith(ex.path[:-5] + "/") \
                and rel.endswith(".md"):
            out.append(ex)
    return out


def exempt_lines(rel, text, check):
    """the 1-based line numbers of `rel` that `check` does not read."""
    rules = exemptions_for(rel, check)
    if not rules:
        return set()
    out, lines = set(), text.splitlines()
    for ex in rules:
        i = 0
        while i < len(lines):
            if ex.start.search(lines[i]):
                if ex.until is None:
                    out.add(i + 1)
                    i += 1
                    continue
                j = i
                while j < len(lines):
                    out.add(j + 1)
                    j += 1
                    if j < len(lines) and ex.until.search(lines[j]):
                        break
                i = j
            else:
                i += 1
    return out


def blanked(text, rel, check):
    """`text` with every exempt line blanked — line numbers stay honest."""
    skip = exempt_lines(rel, text, check)
    if not skip:
        return text
    return "\n".join("" if n + 1 in skip else l
                     for n, l in enumerate(text.splitlines()))


# ------------------------------------------------- check A: forbidden phrases

class Phrase(object):
    __slots__ = ("phrase", "cls", "scope", "why", "regex")

    def __init__(self, phrase, cls, scope, why):
        self.phrase, self.cls, self.scope, self.why = phrase, cls, scope, why
        if phrase.startswith("/") and phrase.endswith("/"):
            self.regex = re.compile(phrase[1:-1])
        else:
            self.regex = re.compile(r"\b" + re.escape(phrase) + r"\b", re.I)

    def __repr__(self):
        return "<phrase %r %s/%s>" % (self.phrase, self.cls, self.scope)


def _table(text, heading):
    """the rows under `heading`, as dicts keyed by the header's column names."""
    body, seen = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            if seen:
                break
            seen = line.strip() == heading
            continue
        if seen:
            body.append(line)
    rows, header = [], None
    for line in body:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if len(cells) != len(header):
            raise ValueError("row has %d cells, the header has %d: %s"
                             % (len(cells), len(header), line))
        rows.append(dict(zip(header, cells)))
    if header is None:
        raise ValueError("no table under %r" % heading)
    return header, rows


def forbidden_phrases(path=None):
    """the one list, parsed from soul/voice.md's table. columns by name.

    a row with an empty reason raises with the row quoted, so a phrase cannot
    reach the list without the reason that puts it there.
    """
    path = path or os.path.join(SOUL, "voice.md")
    text = _text(path)
    header, rows = _table(text, TABLE_HEADING)
    for col in ("phrase", "class", "scope", "why"):
        if col not in header:
            raise ValueError("the forbidden table has no %r column: %s"
                             % (col, header))
    out = []
    for row in rows:
        if not row["why"]:
            raise ValueError("a phrase with no reason: %r" % row["phrase"])
        found = re.findall(r"`([^`]+)`", row["phrase"])
        if not found:
            raise ValueError("a phrase cell with no backticked phrase: %r"
                             % row["phrase"])
        for p in found:
            out.append(Phrase(p, row["class"], row["scope"], row["why"]))
    return tuple(out)


def phrase_hits(text, phrases=None, scopes=("all",)):
    """[(lineno, phrase, Phrase)] — word boundary, case-folded, whole file."""
    phrases = phrases if phrases is not None else forbidden_phrases()
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for p in phrases:
            if p.scope not in scopes:
                continue
            if p.regex.search(line):
                out.append((n, p.phrase, p))
    return out


# ----------------------------------------------------- check B: the negation

_UNSET = object()


def _strip_columns(text, rel, cols=_UNSET):
    """for a page whose table is its prose, keep the rows minus the shape columns.

    `cols` overrides the page's own entry: `()` keeps every column, which is
    what makes the before-and-after in the test an honest pair.
    """
    if cols is _UNSET:
        cols = COLUMN_SKIP.get(rel)
    if cols is None:
        return text
    out, header = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            out.append(line)
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            out.append("")
            continue
        if header is None:
            header = cells
            out.append("")
            continue
        if len(cells) == len(header):
            keep = [c for c, h in zip(cells, header) if h not in cols]
        else:
            keep = cells
        out.append(" ".join(keep))
    return "\n".join(out)


def body(text, rel="", columns=_UNSET):
    """the prose a person reads: no frontmatter, code spans, headings, or data rows."""
    table_is_prose = (COLUMN_SKIP.get(rel) if columns is _UNSET else columns) is not None
    text = blanked(text, rel, "negation") if rel else text
    text = _strip_columns(text, rel, columns)
    text = re.sub(r"^---.*?---\s*", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    text = re.sub(r"^#+ .*$", "", text, flags=re.M)
    if not table_is_prose:
        text = re.sub(r"^\|.*$", "", text, flags=re.M)   # table rows: data
    text = re.sub(r"^\s*<.*>\s*$", "", text, flags=re.M)  # format placeholders
    return text


def sentences(text, rel=""):
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n|\n(?=\s*(?:[-*]|\d+\.)\s)",
                     body(text, rel))
    return [re.sub(r"\s+", " ", s).strip() for s in parts if len(s.strip()) > 3]


def density(text, rel="", columns=_UNSET):
    """negators per 100 words, and the word count it rides on."""
    b = body(text, rel, columns)
    words = re.findall(r"[a-zA-Z'’-]+", b)
    return 100.0 * len(NEGATOR.findall(b)) / max(1, len(words)), len(words)


def stacked(text, rel=""):
    """sentences carrying three or more negators — a reader cannot hold them."""
    return [s for s in sentences(text, rel) if len(NEGATOR.findall(s)) >= 3]


def naked(text, rel=""):
    """prohibitions with no reason riding the sentence and no positive sibling."""
    sents, out = sentences(text, rel), []
    for i, s in enumerate(sents):
        m = PROHIBIT.search(s)
        if not m or REASON.search(s[m.start():]):
            continue
        if any(not NEGATOR.search(w) for w in sents[i + 1:i + 3]):
            continue
        out.append(s)
    return out


# --------------------------------------------------- check C/D: the ast walk

class Literal(object):
    __slots__ = ("path", "lineno", "func", "text")

    def __init__(self, path, lineno, func, text):
        self.path, self.lineno, self.func, self.text = path, lineno, func, text

    @property
    def where(self):
        return "%s:%d" % (self.path, self.lineno)

    def __repr__(self):
        return "<literal %s %r>" % (self.where, self.text[:40])


class _Walk(ast.NodeVisitor):
    """a scope stack, so the innermost function owns the literal (repair B5)."""

    def __init__(self):
        self.stack, self.docs, self.found = ["<module>"], set(), []

    def _mark_doc(self, node):
        first = node.body[0] if getattr(node, "body", None) else None
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            self.docs.add(id(first.value))

    def visit_Module(self, node):
        self._mark_doc(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._mark_doc(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._mark_doc(node)
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Constant(self, node):
        if isinstance(node.value, str) and id(node) not in self.docs:
            self.found.append((node.lineno, self.stack[-1], node.value))
        self.generic_visit(node)


# a regex's own source is a pattern, never a sentence: `\b`, `\s`, `\d`, a
# group flag or a negated class says so. `\n` stays out of the list — real
# printed lines carry it.
_PATTERN = re.compile(r"\\[bswdSWDA]|\(\?|\[\^")


def _printable(s):
    """a string a person could read as a sentence — not html, a path, or a flag."""
    return (len(s) >= 25 and " " in s.strip()
            and not s.lstrip().startswith(("<", "#", "/", "--"))
            and not _PATTERN.search(s))


def literals(path):
    """every printed literal in one python file, innermost function named."""
    rel = _rel(path)
    src = _text(path)
    walk = _Walk()
    walk.visit(ast.parse(src, path))
    return [Literal(rel, ln, fn, s) for ln, fn, s in sorted(walk.found)
            if _printable(s)]


def docstrings(path):
    """[(kind, lineno, name, text)] for module, class and function docstrings."""
    rel = _rel(path)
    tree = ast.parse(_text(path), path)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            text = ast.get_docstring(node, clean=False)
            if not text:
                continue
            kind = "module" if isinstance(node, ast.Module) else "inner"
            out.append((kind, getattr(node, "lineno", 1),
                        getattr(node, "name", rel), text))
    return sorted(out, key=lambda t: t[1])


def opens_lowercase(text):
    """the case rule: a line opens lowercase, a backtick, a digit, or punctuation.

    a leading filename, the product's own name, a `%s` and the ruled signal
    words carry a case that is not the sentence's, so they are stripped first.
    """
    s = text.lstrip()
    s = re.sub(r"^(FAIL|LOOK|DRAFTS|UNVERIFIED|ok)\b\s*", "", s)
    s = re.sub(r"^Sandbox OS\b\s*", "", s)
    s = re.sub(r"^[A-Za-z0-9_.-]+\.(md|py|json|txt|sh)\b\s*", "", s)
    s = re.sub(r"^%[sdr]\s*", "", s)
    s = s.lstrip()
    return not s[:1].isupper()


def case_exempt(row, lit):
    """true when the surfaces row itself names this literal as its one capital.

    row 11's case cell reads `lowercase (the one capitalized block today,
    make.py:67)` — the soul carries the exemption, so the lint reads it there
    rather than keeping a second list.
    """
    if not row:
        return False
    return "%s:%d" % (os.path.basename(lit.path), lit.lineno) in row.get("case", "")


# a filename wears the file's case, not the sentence's: CLAUDE.md is a name.
_FILENAME_CAPS = re.compile(r"\b([A-Z][A-Z0-9_-]{1,})\.(md|py|json|txt|sh)\b")
# the product's own name, spelled the way the product is spelled.
_PRODUCT_CAPS = re.compile(r"\bSandbox (OS)\b")


def caps_tokens(text):
    """the ALL-CAPS tokens a line shouts: not the ruled words, a filename, the
    product's own name, or a placeholder standing where an argument goes."""
    named = set(m.group(1) for m in _FILENAME_CAPS.finditer(text))
    named |= set(m.group(1) for m in _PRODUCT_CAPS.finditer(text))
    out = []
    for t in re.findall(r"\b[A-Z][A-Z0-9_-]{1,}\b", text):
        if t in CAPS_ALLOWED or t in named:
            continue
        if t.strip("-_") in CAPS_PLACEHOLDERS:
            continue
        out.append(t)
    return out


def spec_word_hits(text):
    return [w for w in SPEC_ONLY_WORDS
            if re.search(r"\b" + w + r"\b", text, re.I)]


# ------------------------------------------------- check C: the surfaces rows

def surface_rows(path=None):
    """soul/surfaces.md's table, by row id, columns read by name."""
    path = path or os.path.join(SOUL, "surfaces.md")
    text = _text(path)
    header, rows = None, {}
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        if header is None:
            header = cells
            continue
        if len(cells) != len(header):
            raise ValueError("surfaces row has %d cells, header %d: %s"
                             % (len(cells), len(header), line[:60]))
        row = dict(zip(header, cells))
        rows[row["#"]] = row
    if not rows:
        raise ValueError("soul/surfaces.md parsed to no rows")
    return rows


def word_budget(row):
    """the row's `max words` as a number, or None when the row counts lines."""
    cell = row.get("max words", "")
    nums = re.findall(r"\d+", cell)
    if not nums or "line" in cell:
        return None
    return sum(int(n) for n in nums)


# `(file, function)` or `(file, lineno)` → surfaces row. a lineno key wins over
# a function key, which is how a function that emits several kinds is split
# without putting lint vocabulary in the engine (repair B5). a `# surface: N`
# comment in the source overrides both.
SURFACE = {
    ("engine/apps.py", "install"): "7",
    ("engine/apps.py", "remove"): "7",
    ("engine/apps.py", "placement_allowed"): "3c",
    ("engine/apps.py", "_expand"): "3a",
    ("engine/apps.py", 116): "3a",
    ("engine/apps.py", 119): "3a",
    ("engine/apps.py", 123): "3a",
    ("engine/apps.py", 126): "3a",
    ("engine/apps.py", 130): "3c",
    ("engine/apps.py", 135): "3a",
    ("engine/apps.py", 140): "26",
    ("engine/apps.py", 138): "26",
    ("engine/apps.py", 145): "3b",
    ("engine/apps.py", 178): "3a",
    ("engine/clean.py", "fresh_export"): "3a",
    ("engine/desk.py", "submit"): "6a",
    ("engine/desk.py", 75): "3a",
    ("engine/desk.py", 77): "3a",
    ("engine/desk.py", 80): "3c",
    ("engine/desk.py", "mint"): "3a",
    ("engine/desk.py", "drafts"): "7",
    ("engine/desk.py", "drop"): "2",
    ("engine/desk.py", 139): "3a",
    ("engine/desk.py", "land_all"): "2",
    ("engine/desk.py", 160): "3b",
    ("engine/gate.py", "decide"): "3b",
    ("engine/gate.py", "show"): "27",
    ("engine/gate.py", "ask"): "27",
    ("engine/integrity.py", "seal"): "3b",
    ("engine/integrity.py", "verify"): "2",
    ("engine/integrity.py", "release_notes"): "14",
    ("engine/integrity.py", 216): "3a",
    ("engine/integrity.py", "release_check"): "13",
    ("engine/journal.py", "ensure_genesis"): "7",
    ("engine/journal.py", "append"): "3a",
    ("engine/journal.py", "read"): "7",
    ("engine/make.py", "open_session"): "3a",
    ("engine/make.py", "close_session"): "2",
    ("engine/check.py", "run"): "2",
    ("engine/notes.py", "refresh_canon"): "8",
    ("engine/notes.py", "approve"): "27",
    ("engine/notes.py", "strike"): "3a",
    ("engine/notes.py", "why"): "2",
    ("engine/onboard.py", "emit_settings"): "7",
    ("engine/onboard.py", 82): "3a",
    ("engine/onboard.py", "run"): "7",
    ("engine/export.py", "lines"): "7",
    ("engine/export.py", "render_line"): "7",
    ("engine/export.py", "write"): "7",
    ("engine/page.py", "render"): "12",
    ("engine/placement.py", "sync"): "7",
    ("engine/project.py", "_git_birth"): "7",
    ("engine/project.py", "new"): "3a",
    ("engine/project.py", "switch"): "2",
    ("engine/project.py", "done"): "2",
    ("engine/provisional.py", "confirm"): "2",
    ("engine/provisional.py", 123): "3b",
    ("engine/provisional.py", 132): "3a",
    ("engine/provisional.py", "revert"): "2",
    ("engine/provisional.py", 153): "3a",
    ("engine/provisional.py", 155): "3b",
    ("engine/registry.py", "fact"): "3a",
    ("engine/selfmap.py", "render_verbs"): "5",
    ("engine/selfmap.py", "write"): "3a",
    ("engine/selfmap.py", 20): "5",
    ("engine/selfmap.py", 22): "5",
    ("engine/share.py", "share"): "7",
    ("engine/share.py", "sign_card"): "3a",
    ("engine/share.py", "trust_line"): "26",
    ("engine/share.py", "fetch"): "26",
    ("engine/shelf.py", "from_line"): "9",
    ("engine/shelf.py", "save"): "2",
    ("engine/shelf.py", "door_of"): "1",
    ("engine/shelf.py", "entry_for"): "16",
    ("engine/shelf.py", "_write_readme"): "17",
    ("engine/shelf.py", "verify_entry"): "3a",
    ("engine/shelf.py", "_pinned"): "26",
    ("engine/apps.py", "verify_entry"): "3a",
    ("engine/shelf.py", "use"): "3a",
    ("engine/ship.py", "ratify"): "28",
    ("engine/ship.py", "ship"): "2",
    ("engine/status.py", "status"): "1",
    ("engine/status.py", "resume"): "22",
    ("engine/status.py", "play"): "10",
    ("engine/status.py", "doctor"): "4",
    ("engine/status.py", 109): "3a",
    ("engine/succession.py", "run"): "7",
    ("engine/succession.py", 115): "3a",
    ("engine/succession.py", 120): "3a",
    ("engine/update.py", "skew"): "7",
    ("engine/update.py", "run"): "7",
    ("engine/update.py", "void_ratifications"): "7",
    ("engine/update.py", "_migration_one_home"): "7",
    ("engine/update.py", "_migration_two_plugin"): "7",
    ("engine/verbs.py", "<module>"): "5",
    ("engine/verbs.py", "declaration"): "3a",
    ("engine/verbs.py", "_flags_refusal"): "3a",
    ("engine/verbs.py", "_help"): "5",
    ("engine/verbs.py", "dispatch"): "3a",
    ("engine/verbs.py", "_project"): "3a",
    ("engine/verbs.py", "_note"): "3a",
    ("engine/verbs.py", "_drafts"): "7",
    ("engine/verbs.py", 215): "3a",
    ("engine/verbs.py", "_recall"): "2",
    ("engine/verbs.py", "_target"): "3a",
    ("engine/verbs.py", "_make"): "3a",
    ("engine/verbs.py", "_ship"): "3a",
    ("engine/verbs.py", "_check"): "3a",
    ("engine/verbs.py", "_invalidate"): "3a",
    ("engine/verbs.py", "_session"): "3a",
    ("engine/verbs.py", "_save"): "3a",
    ("engine/verbs.py", "_builds"): "1",
    ("engine/verbs.py", "_shelf_dir"): "1",
    ("engine/verbs.py", "_use"): "3a",
    ("engine/verbs.py", "_share"): "3a",
    ("engine/verbs.py", "_fetch"): "3a",
    ("engine/verbs.py", "_import"): "3a",
    ("engine/verbs.py", "_app"): "3a",
    ("engine/verbs.py", "_setup"): "7",
    ("engine/verbs.py", "_reset"): "3a",
    ("engine/verbs.py", "_page"): "25",
    ("engine/verbs.py", "_export"): "7",
    ("engine/verbs.py", "_export_report"): "7",
    ("engine/verbs.py", "_release"): "13",
    ("engine/voicelint.py", "report"): "4",
    ("engine/voicelint.py", "main"): "4",
    ("engine/voicelint.py", "line"): "4",
    ("engine/voicelint.py", "_table"): "3a",
    ("engine/voicelint.py", "forbidden_phrases"): "3a",
    ("engine/voicelint.py", "surface_rows"): "3a",
    ("vessel/plugin/hooks/guard.py", "decide"): "3c",
}

# a literal nothing renders: schema text a builder and a test read, and no
# person ever meets. `# surface: none` says so out loud, so it is counted as
# answered-for rather than sitting in the unmapped list forever.
NOT_PRINTED = "none"

SURFACE_MARKER = re.compile(r"^\s*#\s*surface:\s*(\S+)")
_DEF = re.compile(r"^\s*(def|class|async def)\b")


def surface_markers(path):
    """`# surface: N` comments, as {lineno: row}. the marker rules from the line
    after it until the next marker or the next def/class — B5's mechanism for a
    function that emits several kinds and for module-level literals."""
    out, current = {}, None
    for n, line in enumerate(_text(path).splitlines(), 1):
        m = SURFACE_MARKER.match(line)
        if m:
            current = m.group(1)
            continue
        if _DEF.match(line):
            current = None
        if current:
            out[n] = current
    return out


def row_for(lit, markers=None):
    """the surfaces row this literal answers to, or None when nothing claims it."""
    markers = markers if markers is not None else {}
    if lit.lineno in markers:
        return markers[lit.lineno]
    key = (lit.path, lit.lineno)
    if key in SURFACE:
        return SURFACE[key]
    return SURFACE.get((lit.path, lit.func))


# ----------------------------------------------------------------- the walks

def walk_text_files():
    """every text a person meets, with law/ and the named skips left out."""
    out = []
    for base in sorted(os.listdir(REPO)):
        top = os.path.join(REPO, base)
        if not os.path.isdir(top) or base in SKIP_TREES or base in SKIP_DIRS:
            continue
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in sorted(filenames):
                if name in SKIP_FILES or not name.endswith(TEXT_SUFFIXES):
                    continue
                out.append(os.path.join(dirpath, name))
    for name in WALK_FILES:
        p = os.path.join(REPO, name)
        if os.path.exists(p):
            out.append(p)
    return sorted(set(out))


def source_files():
    """the files lint-string reads: engine/*.py and the guard the plugin ships."""
    out = [os.path.join(REPO, "engine", n)
           for n in sorted(os.listdir(os.path.join(REPO, "engine")))
           if n.endswith(".py")]
    out.append(os.path.join(REPO, "vessel", "plugin", "hooks", "guard.py"))
    return [p for p in out if os.path.exists(p)]


def docstring_files():
    """check D reads the tests too: a docstring is read at the moment a check
    fails, which is exactly when a person is looking."""
    tests = os.path.join(REPO, "engine", "tests")
    return source_files() + [os.path.join(tests, n) for n in sorted(os.listdir(tests))
                             if n.endswith(".py")]


def negation_files():
    """the texts that tell a person how to be: the layer, plus the soul."""
    out = [os.path.join(REPO, p) for p in INSTRUCTION_FILES]
    adir = os.path.join(REPO, "vessel", "plugin", "agents")
    if os.path.isdir(adir):
        out += [os.path.join(adir, n) for n in sorted(os.listdir(adir))
                if n.endswith(".md")]
    sdir = os.path.join(REPO, "vessel", "plugin", "skills")
    if os.path.isdir(sdir):
        for dirpath, _, filenames in os.walk(sdir):
            out += [os.path.join(dirpath, n) for n in sorted(filenames)
                    if n == "SKILL.md"]
    out += [os.path.join(SOUL, n) for n in sorted(os.listdir(SOUL))
            if n.endswith(".md")]
    for n in sorted(os.listdir(os.path.join(REPO, "docs"))):
        if n.endswith(".md"):
            out.append(os.path.join(REPO, "docs", n))
    out += [os.path.join(REPO, "README.md"), os.path.join(REPO, "CHANGELOG.md")]
    return [p for p in out if os.path.exists(p)]


# ------------------------------------------------------------------ the report

class Report(object):
    """what one run found. gates fail; smells print."""

    def __init__(self):
        self.files = 0
        self.forbidden = []      # (where, phrase, why)         gate
        self.stacked = []        # (rel, sentence)              gate
        self.naked = []          # (rel, sentence)              gate
        self.density = []        # (rel, number, words)         smell
        self.literals = []       # Literal                      counted
        self.unmapped = []       # Literal                      counted
        self.not_printed = []    # Literal                      counted
        self.case = []           # (where, text)                gate
        self.spec_words = []     # (where, word, text)          gate
        self.caps = []           # (where, token)               smell
        self.budget = []         # (where, row, count, ceiling) smell
        self.moves = []          # (where, move, text)          gate
        self.docstrings = 0
        self.doc_case = []       # (kind, where, first line)    gate on modules

    @property
    def gates(self):
        return (self.forbidden + self.stacked + self.naked + self.case
                + self.spec_words + self.moves)

    def line(self):
        return ("coverage: %d file(s), %d printed literal(s), %d mapped to a "
                "surfaces row, %d never printed, %d still unmapped"
                % (self.files, len(self.literals),
                   len(self.literals) - len(self.unmapped) - len(self.not_printed),
                   len(self.not_printed), len(self.unmapped)))


REFUSAL_ROWS = ("3a", "3b", "3c", "30")
FORBIDDEN_MOVES = (
    ("please", re.compile(r"\bplease\b", re.I)),
    ("sorry", re.compile(r"\bsorry\b", re.I)),
    ("invalid", re.compile(r"\binvalid\b", re.I)),
)


def check_text(path, rep, phrases):
    rel = _rel(path)
    try:
        text = _text(path)
    except (UnicodeDecodeError, OSError):
        return
    rep.files += 1
    clean = blanked(text, rel, "forbidden")
    for n, phrase, p in phrase_hits(clean, phrases, scopes=("all",)):
        rep.forbidden.append(("%s:%d" % (rel, n), phrase, p.why))


def check_negation(path, rep):
    rel = _rel(path)
    text = _text(path)
    d, words = density(text, rel)
    rep.density.append((rel, d, words))
    for s in stacked(text, rel):
        rep.stacked.append((rel, s))
    for s in naked(text, rel):
        rep.naked.append((rel, s))


def check_source(path, rep, phrases, rows):
    rel = _rel(path)
    markers = surface_markers(path)
    for lit in literals(path):
        rep.literals.append(lit)
        row_id = row_for(lit, markers)
        if row_id == NOT_PRINTED:
            rep.not_printed.append(lit)
        elif row_id is None:
            rep.unmapped.append(lit)
        for n, phrase, p in phrase_hits(lit.text, phrases, scopes=("all", "error")
                                        if row_id in REFUSAL_ROWS else ("all",)):
            rep.forbidden.append((lit.where, phrase, p.why))
        row = rows.get(row_id) if row_id else None
        if not opens_lowercase(lit.text) and not case_exempt(row, lit):
            rep.case.append((lit.where, lit.text))
        for w in spec_word_hits(lit.text):
            rep.spec_words.append((lit.where, w, lit.text))
        for t in caps_tokens(lit.text):
            rep.caps.append((lit.where, t))
        if row_id in REFUSAL_ROWS:
            for name, rx in FORBIDDEN_MOVES:
                if rx.search(lit.text):
                    rep.moves.append((lit.where, name, lit.text))
        if row:
            ceiling = word_budget(row)
            n_words = len(lit.text.split())
            if ceiling and n_words > ceiling:
                rep.budget.append((lit.where, row_id, n_words, ceiling))



def check_docstrings(path, rep):
    rel = _rel(path)
    for kind, lineno, name, text in docstrings(path):
        rep.docstrings += 1
        if not opens_lowercase(text):
            rep.doc_case.append((kind, "%s:%d" % (rel, lineno),
                                 text.strip().splitlines()[0][:60]))


def run(paths=None):
    """one whole pass. `paths` narrows it; absent, it walks the tree."""
    rep = Report()
    phrases = forbidden_phrases()
    rows = surface_rows()
    if paths:
        texts = [p for p in paths if not p.endswith(".py")]
        sources = [p for p in paths if p.endswith(".py")]
        negations = [p for p in paths if p.endswith(".md")]
    else:
        texts = walk_text_files()
        sources = source_files()
        negations = negation_files()
    for p in texts + [s for s in sources if paths]:
        check_text(p, rep, phrases)
    if not paths:
        for p in sources:
            check_text(p, rep, phrases)
    for p in negations:
        check_negation(p, rep)
    for p in sources:
        check_source(p, rep, phrases, rows)
    for p in (sources if paths else docstring_files()):
        check_docstrings(p, rep)
    return rep


def report(rep, sample=0, out=None):
    """print what the run found: smells first, then the gates, then coverage."""
    out = out or sys.stdout
    for rel, d, words in sorted(rep.density):
        mark = "smell" if d > CEILING else "ok   "
        out.write("%s density %-42s %5.2f per 100 words over %d (ceiling %.1f)\n"
                  % (mark, rel, d, words, CEILING))
    if rep.density:
        out.write("ok    negation over %d file(s): stacked %d, naked %d\n"
                  % (len(rep.density), len(rep.stacked), len(rep.naked)))
    out.write("%s caps: %d token(s) outside %s%s\n"
              % ("smell" if rep.caps else "ok   ", len(rep.caps),
                 ", ".join(CAPS_ALLOWED),
                 (", first: " + ", ".join("%s %s" % (w, t) for w, t in rep.caps[:3]))
                 if rep.caps else ""))
    out.write("%s budget: %d literal(s) over their row's word count\n"
              % ("smell" if rep.budget else "ok   ", len(rep.budget)))
    mods = [d for d in rep.doc_case if d[0] == "module"]
    out.write("%s docstrings: %d of %d open uppercase (%d of them module "
              "docstrings)\n"
              % ("smell" if rep.doc_case else "ok   ", len(rep.doc_case),
                 rep.docstrings, len(mods)))
    for where, phrase, why in rep.forbidden:
        out.write("FAIL %s says %r — %s\n" % (where, phrase, why))
    for rel, s in rep.stacked:
        out.write("FAIL %s stacks three prohibitions: %s\n" % (rel, s[:90]))
    for rel, s in rep.naked:
        out.write("FAIL %s prohibits with no reason: %s\n" % (rel, s[:90]))
    for where, text in rep.case:
        out.write("FAIL %s opens uppercase: %r\n" % (where, text[:60]))
    for where, word, _ in rep.spec_words:
        out.write("FAIL %s says %r, a word for a part of the machine\n"
                  % (where, word))
    for where, move, text in rep.moves:
        out.write("FAIL %s says %r in a refusal: %r\n" % (where, move, text[:50]))
    if sample:
        pool = list(rep.literals)
        random.shuffle(pool)
        out.write("a sample, for your eye:\n")
        for lit in pool[:sample]:
            out.write("  %-28s %s\n" % (lit.where, lit.text[:70]))
    for lit in rep.unmapped:
        out.write("unmapped %-26s %s in %s\n"
                  % (lit.where, repr(lit.text[:44]), lit.func))
    out.write(rep.line() + "\n")
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m engine.voicelint",
                                 description="the voice lint, over any path")
    ap.add_argument("paths", nargs="*", help="files to read; absent, the tree")
    ap.add_argument("--sample", type=int, default=0,
                    help="print N literals for a cold read")
    args = ap.parse_args(argv)
    rep = run([os.path.abspath(p) for p in args.paths] or None)
    report(rep, sample=args.sample)
    return 1 if rep.gates else 0


if __name__ == "__main__":
    sys.exit(main())
