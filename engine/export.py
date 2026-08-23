# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""export — the record leaves the workshop as one file a person can read.

law 2's outward half: `import` carries a past workshop in, and this carries
one out, in one honest verb, with what cannot come said plainly in the file's
own foot. one line per landed event, in time order, each wearing its rung,
whose hand it came from, and the receipt that opens it.

three forms, one rendering: `md` is the readable file, `html` is the same
lines as one self-contained page (what `sandbox page` writes now), and
`portable` is the leaving directory `import` reads back.

running it appends one `export` event carrying the written file's sha256 —
that is what left the machine. opening the written file appends nothing,
because a file has no way to reach back, and both facts are on the page.
"""
import hashlib
import json
import os
import re
import shutil

from . import clean, desk, journal, registry

# surface: 25
FOOTER = "this is a file — opening it leaves nothing on the record"
STEM = "record-"
SCAR_LINE = re.compile(r"line (\d+)")


def _ws_name(ws):
    """the workshop's own name for itself, or the plain words for it."""
    p = os.path.join(ws, journal.STATE_DIR, "workshop-id")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            said = f.read().strip()
        if said:
            return said
    # surface: 25
    return "this workshop"


def _marks(ws):
    """id → (rung, supersedes) from the typed read, so export re-derives none
    of it: a struck line reads struck here exactly as it reads in canon."""
    world = registry.project(ws)
    out = {}
    for x in world["note"]:
        out[x["id"]] = ("struck" if x.get("invalidated_by")
                        else x.get("ink", "claimed"), None)
    for r in world["ruling"]:
        out[r["id"]] = ("struck" if r.get("invalidated_by")
                        else r.get("stratum", "taste"), r.get("supersedes"))
    return out


def _diff_summary(e):
    """a make close's file counts, as one field."""
    d = e.get("diff") or {}
    if not isinstance(d, dict):
        return ""
    return "(+%d −%d ~%d)" % (len(d.get("added") or ()),
                              len(d.get("removed") or ()),
                              len(d.get("changed") or ()))


def _kind(e):
    """`op` when the op is the whole answer, `op/cls` when it carries one."""
    op = e.get("op") or "?"
    tail = e.get("cls") or e.get("phase") or e.get("action")
    return "%s/%s" % (op, tail) if tail else op


def _row(e, marks):
    rung, supersedes = marks.get(e.get("id"), (None, None))
    if rung is None:
        rung = e.get("ink") or "claimed"
    text = e.get("body") or e.get("note") or ""
    if e.get("op") == "make" and e.get("phase") == "close":
        text = (text + " " + _diff_summary(e)).strip()
    if supersedes:
        text = (text + " supersedes: journal:%s" % supersedes).strip()
    return {"ts": e.get("ts") or "", "ink": rung,
            "origin": e.get("origin") or "machine", "hand": e.get("hand"),
            "kind": _kind(e), "body": text,
            "receipt": e.get("receipt") or "journal:%s" % (e.get("id") or e.get("op")),
            "project": e.get("project"), "scar": False}


def _scar_row(text):
    return {"ts": "", "ink": "torn", "origin": "record", "hand": None,
            "kind": "scar", "body": text, "receipt": "", "project": None,
            "scar": True}


def lines(ws, since=None, project=None):
    """every event in time order, as the rows a line is rendered from.

    scars ride at the file position they were found at, never dropped: a torn
    line is part of the record, and an export that swallowed one would be a
    cleaner copy than the truth.
    """
    events, scars = journal.read(ws)
    at = {}
    for s in scars:
        m = SCAR_LINE.search(s)
        if m:
            at.setdefault(int(m.group(1)), []).append(s)
    marks = _marks(ws)
    rows, i, n = [], 0, 1
    while i < len(events) or at:
        for s in at.pop(n, ()):
            rows.append(_scar_row(s))
        if i < len(events):
            rows.append(_row(events[i], marks))
            i += 1
        elif not at:
            break
        n += 1
        if n > len(events) + len(scars) + 1:
            for rest in sorted(at):
                for s in at.pop(rest):
                    rows.append(_scar_row(s))
            break
    keep = []
    for r in rows:
        if r["scar"]:
            keep.append(r)
            continue
        if since and r["ts"][:10] < since:
            continue
        if project and r["project"] != project:
            continue
        keep.append(r)
    return keep


def render_line(r):
    """the one rendering of an event as a human line — recall and canon read
    the same fields and print their own short forms from them."""
    hand = " [%s]" % r["hand"] if r.get("hand") else ""
    out = "%s  [%s] [%s]%s %s" % (r["ts"], r["ink"], r["origin"], hand, r["kind"])
    if r["body"]:
        out += "  " + r["body"].replace("\n", " ")
    if r["receipt"]:
        out += "  " + r["receipt"]
    return out.rstrip()


def _span(rows):
    stamps = [r["ts"] for r in rows if r["ts"]]
    return (stamps[0], stamps[-1]) if stamps else ("", "")


def header(ws, rows, redacted=0, since=None, project=None, form="md"):
    """the file's own self-report: whose record, how much of it, and whether a
    span was taken out before it was handed over."""
    # surface: 12
    first, last = _span(rows)
    torn = len([r for r in rows if r["scar"]])
    slice_of = [x for x in (project, "since " + since if since else None) if x]
    title = "# record — %s, %s" % (_ws_name(ws), journal.now()[:10])
    if slice_of:
        title += " · %s (a slice, not the record)" % ", ".join(slice_of)
    count = "%d line(s) · %s → %s" % (len(rows), first or "—", last or "—")
    if torn:
        count += (" · %d torn line(s) on the record — a line it could not read; "
                  "doctor has details" % torn)
    if redacted:
        count += " — redacted, %d span(s) removed" % redacted
    return [title, "", count, ""]


# surface: 7
ROUND_TRIP = (
    "what comes back through import: every line above, verbatim — its id, its "
    "time, its origin, its rung, its receipt, and the scars as scars.",
    "what stays behind: the shelf's cards, the project trees and their git "
    "histories, staged drafts, and every ratification (checks await a fresh "
    "keystroke in the new workshop).",
)


def render_md(ws, rows, redacted=0, since=None, project=None):
    out = header(ws, rows, redacted, since, project)
    out += [render_line(r) for r in rows]
    out += ["", "## what travels", ""]
    out += ["- " + s for s in ROUND_TRIP]
    # surface: 25
    out += ["", FOOTER, ""]
    return "\n".join(out)


def _next_path(base, name, suffix):
    """`record-<date>.md`, then `-2`, then `-3`: an export is a receipt, and a
    receipt never silently replaces the one before it."""
    p = os.path.join(base, name + suffix)
    n = 1
    while os.path.exists(p):
        n += 1
        p = os.path.join(base, "%s-%d%s" % (name, n, suffix))
    return p


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def would_scrub(text, terms):
    """the count a run without --redact still prints, so nothing is handed
    over blind."""
    _, report = clean.redact(text, terms)
    return report["home_path"] + sum(report["terms"].values())


def write(ws, form="md", redact=False, since=None, project=None, to=None):
    """write the record out. returns `(path, report)`.

    the report carries what the terminal prints and what the event stores —
    the counts by needle index, never the owner's words.
    """
    # surface: 3a
    if form == "portable" and redact:
        return None, {"refused": (
            "a redacted export is a reading copy; import needs every line. "
            "run export --portable by itself.")}
    rows = lines(ws, since=since, project=project)
    terms = clean.private_terms()
    text = render_md(ws, rows, 0, since, project)
    counts = {"home_path": 0, "terms": {}}
    if redact:
        text, counts = clean.redact(text, terms)
        removed = counts["home_path"] + sum(counts["terms"].values())
        text = render_md(ws, rows, removed, since, project)
        text, counts = clean.redact(text, terms)
    base = os.path.abspath(os.path.expanduser(to)) if to else ws
    os.makedirs(base, exist_ok=True)
    name = STEM + journal.now()[:10]
    if form == "portable":
        path = _leaving_dir(ws, base, name, text, rows)
        sha = _sha(os.path.join(path, name + ".md"))
    elif form == "html":
        from . import page
        path = _next_path(base, name, ".html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(page.render(rows, header(ws, rows, 0, since, project),
                                ROUND_TRIP, FOOTER))
        sha = _sha(path)
    else:
        path = _next_path(base, name, ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        sha = _sha(path)
    # surface: 6b
    said = "the record left as %s — %d line(s)" % (form, len(rows))
    desk.mint(ws, {"op": "export", "form": form, "redacted": bool(redact),
                   "lines": len(rows), "sha256": sha, "receipt": path,
                   "body": said, "origin": "machine", "scrubbed": counts})
    report = {"path": path, "lines": len(rows), "span": _span(rows),
              "sha256": sha, "counts": counts, "redacted": bool(redact),
              "terms": terms, "would": 0 if redact else would_scrub(text, terms)}
    return path, report


def redaction_summary(report):
    """what a redacted run scrubbed: (total spans, the named spans, dead terms).

    The receipt stores needle indexes, never the terms themselves, so the
    words are read back out of the caller's own list here — and a term the
    list carried that matched nothing is counted, because a terms file nobody
    is hitting is worth knowing about.
    """
    counts, terms = report["counts"], report["terms"]
    named = []
    if counts["home_path"]:
        named.append("home paths %d" % counts["home_path"])
    for key in sorted(counts["terms"]):
        i = int(key[1:]) - 1
        word = terms[i] if terms and i < len(terms) else key
        named.append("%s %d" % (word, counts["terms"][key]))
    total = counts["home_path"] + sum(counts["terms"].values())
    dead = 0 if terms is None else len(
        [i for i in range(1, len(terms) + 1) if "t%d" % i not in counts["terms"]])
    return total, named, dead


def _leaving_dir(ws, base, name, text, rows):
    """the directory a workshop leaves in: the readable file, the record
    byte-for-byte, and the map that opens old receipts at new addresses."""
    d = _next_path(base, name + "-portable", "")
    os.makedirs(d)
    with open(os.path.join(d, name + ".md"), "w", encoding="utf-8") as f:
        f.write(text)
    src = journal.path(ws)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(d, "journal.jsonl"))
    with open(os.path.join(d, "path-map.json"), "w", encoding="utf-8") as f:
        json.dump([[os.path.abspath(ws), "."]], f)
    return d
