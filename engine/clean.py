# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""person-clean (law 13's mechanism): nothing of the owner ships by accident.

Two jobs. `scan` reads a tree and names every place person data could ride:
text hits against the floor needles and the owner's private terms (read from
OUTSIDE any shipped tree, so this module itself stays clean), files it
cannot read into text (binaries — named, never silently passed), and
deny-listed patterns that never ship at all. `fresh_export` copies a tree
for publishing WITHOUT its git history, by construction — the scrub that
once took a hand-done line-by-line pass, become mechanism.
"""
import os
import re
import shutil

TERMS_ENV = "SANDBOX_PRIVATE_TERMS"

# Floor needles are assembled, not written literally, so this file passes
# its own scan.
FLOOR = ("/" + "Users" + "/", "/" + "home" + "/")

# Where a needle's owner-name ends: the next separator, or any character that
# closes a path in prose. Assembled here so this file still passes its scan.
_ENDS = set(" \t\n\r\"'`,;:)]}>*")


def strip_home(text):
    """rewrite every home path to `~/…`. returns (text, count).

    the same needles `scan` reads, rewritten rather than refused. a home path
    is a shape, and the shape has a spelling that belongs to nobody: `~`. a
    private term has no such spelling, which is why share still refuses those
    and only these get fixed on the way out.
    """
    count = 0
    for needle in FLOOR:
        while needle in text:
            i = text.index(needle)
            j = i + len(needle)
            while j < len(text) and text[j] != "/" and text[j] not in _ENDS:
                j += 1
            text = text[:i] + "~" + text[j:]
            count += 1
    return text, count


# Never ships, full stop.
DENY_PATTERNS = (".env", ".sqlite", ".db", ".pem", ".key", "id_rsa")

SKIP_DIRS = {".git", "__pycache__", ".DS_Store", "node_modules"}


def private_terms():
    """the owner's terms, from outside the tree. Absent file → floor only,
    and the report says so rather than pretending the deeper scan ran."""
    p = os.environ.get(TERMS_ENV, "").strip()
    if not p or not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return [t.strip() for t in f if t.strip() and not t.startswith("#")]


def scan(root):
    """returns a report dict; report['clean'] is the one honest verdict.

    hits: text files carrying a needle/term. denied: deny-listed names.
    unscannable: files that would not read as text — person data could hide
    there, so publishing requires a per-file ack, never silence.
    """
    terms = private_terms()
    needles = list(FLOOR) + (terms or [])
    report = {"hits": [], "denied": [], "unscannable": [],
              "terms_loaded": terms is not None}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            if any(name.endswith(p) or name == p for p in DENY_PATTERNS):
                report["denied"].append(rel)
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                report["unscannable"].append(rel)
                continue
            for n in needles:
                if n in text:
                    report["hits"].append((rel, n if terms and n in terms else "home-path"))
                    break
    report["clean"] = not report["hits"] and not report["denied"]
    return report


def fresh_export(src, dest):
    """copy a tree for publishing. `.git` never comes, by construction.

    Returns the scan report of the EXPORTED tree — the thing that would
    actually ship is the thing that gets scanned.
    """
    if os.path.exists(dest) and os.listdir(dest):
        raise ValueError("fresh_export: destination must be empty — a stale "
                         "export scanned clean is a costume")
    os.makedirs(dest, exist_ok=True)
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel = os.path.relpath(dirpath, src)
        for name in filenames:
            out_dir = os.path.join(dest, rel) if rel != "." else dest
            os.makedirs(out_dir, exist_ok=True)
            shutil.copy2(os.path.join(dirpath, name), os.path.join(out_dir, name))
    return scan(dest)


MARK = "[redacted]"

# one home path, as a span: the floor needle plus everything that reads as
# part of the same path. built from FLOOR so there is one list of needles.
_HOME_SPAN = re.compile(
    "(?:%s)[A-Za-z0-9._+@%%~-]*(?:/[A-Za-z0-9._+@%%~-]*)*"
    % "|".join(re.escape(n) for n in FLOOR))


def redact(text, terms=None):
    """swap every home path and every owner term out of one text.

    returns `(text, report)`. the report counts home paths under `home_path`
    and each term under `t<N>`, where N is the term's place in the list handed
    in — the count travels onto the record, the words stay with the owner.
    the path pass is `strip_home`, so the two readers of the floor cannot
    drift apart; the fallback below is what runs if it ever goes away.
    """
    report = {"home_path": 0, "terms": {}}
    strip = globals().get("strip_home")
    if callable(strip):
        text, report["home_path"] = strip(text)
    else:
        text, report["home_path"] = _HOME_SPAN.subn(MARK, text)
    return _terms_pass(text, terms, report)


def _terms_pass(text, terms, report):
    """the owner's own words, counted by their place in the file, never named."""
    for i, term in enumerate(terms or (), 1):
        if not term:
            continue
        n = text.count(term)
        if n:
            text = text.replace(term, MARK)
            report["terms"]["t%d" % i] = n
    return text, report
