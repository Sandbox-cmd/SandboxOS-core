# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""note / drafts / approve / recall — the pen and the keystroke.

A note from the machine stages; a note typed by the owner at a real terminal
lands through the gate. Canon is the projection each landing refreshes: one
page per project, regenerated from the record, never edited by hand. Recall
searches the landed record; `--why` walks a fact's lineage back through the
staging note and the session that proposed it.
"""
import os
import sys

from . import desk, gate, journal, project, registry


def note(ws, body, cls="note", target_project=None, stratum=None):
    """Stage or land one note. Origin is decided by the hand, not claimed:
    a real tty is the owner; anything else is the machine."""
    origin = "human" if sys.stdin.isatty() and not gate.synthetic() else "machine"
    if gate.synthetic() and os.environ.get("SANDBOX_TEST_HUMAN"):
        origin = "human"
    record = {"body": body, "cls": cls, "origin": origin}
    if target_project:
        record["project"] = target_project
    if stratum:
        record["stratum"] = stratum
        record["cls"] = "ruling"
    consent = None
    if origin == "human":
        consent = gate.mint_consent(is_real_tty=True, keychar=gate.COMMIT_KEY)
    disp, msg = desk.submit(ws, record, consent)
    if disp == "landed":
        refresh_canon(ws, target_project)
    return disp, msg


def approve(ws, is_real_tty=None, keychar=None):
    """The keystroke lands the pile and refreshes every touched canon."""
    consent = gate.mint_consent(is_real_tty=is_real_tty, keychar=keychar)
    if consent is None:
        return 0, "landing needs your %r at a real terminal" % gate.COMMIT_KEY
    pile, _ = desk.drafts(ws)
    touched = {d.get("project") for d in pile}
    n, msg = desk.land_all(ws, consent)
    for p in touched:
        refresh_canon(ws, p)
    return n, msg


def refresh_canon(ws, name=None):
    """Regenerate a project's CANON.md (or the workshop's) from the record.

    Canon is disposable by design — delete it and this rebuilds it from
    truth. Every line wears its ink and origin.
    """
    world = registry.project(ws)
    targets = [name] if name else [None]
    for t in targets:
        if t is None:
            path = os.path.join(ws, "CANON.md")
            title = "the workshop"
            keep = lambda x: x.get("lands_on") in (None, "workshop") or x.get("binds") == "workshop"
        else:
            pdir = project.dirpath(ws, t)
            if not os.path.isdir(pdir):
                continue
            path = os.path.join(pdir, "CANON.md")
            title = t
            keep = lambda x: x.get("lands_on") == t or x.get("binds") == t
        lines = ["# canon — %s" % title, "",
                 "*projected from the record; do not edit by hand.*", ""]
        count = 0
        for r in world["ruling"]:
            if keep(r):
                lines.append("- [%s] ruling: %s" % (r.get("stratum", "taste"), r.get("body", "")))
                count += 1
        for x in world["note"]:
            if keep(x):
                lines.append("- [%s] [%s] %s" % (x.get("ink", "claimed"),
                                                 x.get("origin", "machine"),
                                                 x.get("body", "")))
                count += 1
        lines += ["", "_%d landed facts — computed, not stored._" % count]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def recall(ws, query, target_project=None):
    """Search the landed record. Returns matching lines, ink worn openly."""
    world = registry.project(ws)
    q = query.lower()
    hits = []
    for r in world["ruling"]:
        if q in (r.get("body") or "").lower():
            if target_project and r.get("binds") != target_project:
                continue
            hits.append("[%s] ruling: %s" % (r.get("stratum"), r["body"]))
    for x in world["note"]:
        if q in (x.get("body") or "").lower():
            if target_project and x.get("lands_on") != target_project:
                continue
            hits.append("[%s] [%s] %s" % (x.get("ink"), x.get("origin"), x["body"]))
    return hits


def why(ws, query):
    """The lineage walk: for the newest fact matching the query, show the
    chain the record already holds — the landed event, what it superseded,
    and the session open around its landing."""
    events, _ = journal.read(ws)
    q = query.lower()
    hit = None
    for e in events:
        if e.get("op") == "assert" and q in (e.get("body") or "").lower():
            hit = e  # newest wins — keep walking
    if hit is None:
        return ["nothing landed matches %r" % query]
    out = ["the fact: [%s] [%s] %s" % (hit.get("ink", "claimed"),
                                       hit.get("origin", "machine"), hit.get("body")),
           "landed: %s  (journal:%s)" % (hit.get("ts"), hit.get("id"))]
    if hit.get("receipt"):
        out.append("receipt: %s" % hit["receipt"])
    if hit.get("supersedes"):
        old = next((e for e in events if e.get("id") == hit["supersedes"]), None)
        if old:
            out.append("supersedes: %s (%s)" % (old.get("body"), old.get("ts")))
    sessions = [e for e in events
                if e.get("op") == "session" and e.get("ts", "") <= hit.get("ts", "")]
    if sessions:
        out.append("during session: %s" % sessions[-1].get("id"))
    return out
