# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""note / drafts / approve / recall — the pen and the keystroke.

Every note stages, whoever typed it (R3). `approve` prints the pile, prints
the fingerprint of exactly that block, reads one real key, and lands the
lines it showed — carrying the fingerprint onto each of them. Canon is the
projection each landing refreshes: one page per project, regenerated from
the record, never edited by hand. Recall searches the landed record; `--why`
walks a fact's lineage back through the staging note and the session that
proposed it.
"""
import os
import sys

from . import desk, gate, journal, project, registry


def note(ws, body, cls="note", target_project=None, stratum=None,
         supersedes=None):
    """stage one note. Origin is decided by the hand, not claimed: a real tty
    is the owner, anything else is the machine. What lands it is the key, and
    the two are separate facts.

    A ruling is the same pen with a stratum on it. Taste is the only stratum
    this verb reaches: law binds until the owner amends it, and an amendment
    is its own sitting, never a flag on a note (law 14).
    """
    origin = "human" if sys.stdin.isatty() and not gate.synthetic() else "machine"
    record = {"body": body, "cls": cls, "origin": origin}
    if target_project:
        record["project"] = target_project
    if stratum:
        record["stratum"] = stratum
        record["cls"] = "ruling"
    if supersedes:
        record["supersedes"] = supersedes
    return desk.submit(ws, record)


def strike(ws, target_id, why):
    """stage the second thought about a landed line.

    The line itself is never touched: what stages here is a new event that
    names it, and every projection reads the pair. It goes through the same
    pen as everything else, so what strikes a fact on the record is the
    owner's key and nothing quieter.
    """
    events, _ = journal.read(ws)
    target = next((e for e in events if e.get("id") == target_id), None)
    if target is None:
        return None, ("nothing on the record carries that id — "
                      "find it with: sandbox recall \"words\"")
    disp, msg = desk.submit(ws, {"op": "invalidate", "of": target_id,
                                 "body": why, "origin": "human"
                                 if sys.stdin.isatty() and not gate.synthetic()
                                 else "machine",
                                 "project": target.get("project")})
    if disp != "staged":
        return None, msg
    return target, msg


def approve(ws, target_project=None, out=print):
    """the pile, its fingerprint, one real key, and the landing.

    Returns the exit code the verb hands back: 1 when nothing at a terminal
    can answer, or when staging moved under the person while they read; 0
    otherwise, because choosing to land nothing is not a failure.
    """
    if not gate.at_a_terminal():
        out(gate.NOT_A_TTY % "approve")
        return 1
    pile, _scars = desk.drafts(ws)
    waiting = len(pile)
    if target_project:
        pile = [d for d in pile if d.get("project") == target_project]
    if not pile:
        # surface: 7
        out("i found nothing waiting — no notes need your approval.")
        return 0
    count, digest = gate.show([desk.row(d) for d in pile], out)
    shown = pile[:count]
    gate.ask(count, out)
    consent = gate.mint_consent(shown=digest)
    if consent is None:
        # surface: 2
        out("cancelled — nothing landed")
        return 0
    # surface: 27
    n, msg = desk.land_all(ws, consent, shown=shown)
    if n is None:
        out(msg)
        return 1
    for p in {d.get("project") for d in shown}:
        refresh_canon(ws, p)
    left, _ = desk.drafts(ws)
    line = "landed %d (shown %s)" % (n, digest[:8])
    arrived = len(left) - (waiting - n)
    if arrived > 0:
        line += " · %d arrived while you read — still waiting" % arrived
    out(line)
    return 0


def refresh_canon(ws, name=None):
    """regenerate a project's CANON.md (or the workshop's) from the record.

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
        lines = ["# canon — %s" % title, "", project.CANON_HEADER, ""]
        count = 0
        for r in world["ruling"]:
            if keep(r) and not r.get("invalidated_by"):
                lines.append("- [%s] ruling: %s" % (r.get("stratum", "taste"), r.get("body", "")))
                count += 1
        for x in world["note"]:
            # a struck line stays on the record and leaves this page: canon is
            # what stands, and `sandbox recall` is where the second thought
            # and the line it struck are both readable.
            if keep(x) and not x.get("invalidated_by"):
                lines.append("- [%s] [%s] %s" % (x.get("ink", "claimed"),
                                                 x.get("origin", "machine"),
                                                 x.get("body", "")))
                count += 1
        lines += ["", "_%d landed facts — computed, not stored._" % count]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


MEMORY_LINES = 200
MEMORY_NOTES = 20


def memory(ws, name=None):
    """write the workshop's MEMORY.md from the record. Returns (path, lines).

    The host writes its own memory files while a session runs; this workshop
    routes that impulse to the record instead, and hands the host back a page
    the engine wrote. So the arrow only ever points one way: code projects
    this file from landed events, a session reads it, and a session that
    tries to write it meets the guard. What goes on it is what a person would
    want on arriving cold — what stands right now, and the last few things
    that landed — capped, because a page nobody finishes is a page nobody
    reads.
    """
    world = registry.project(ws)
    standing = rulings(ws, target_project=name)
    landed = [x for x in world["note"]
              if (name is None or x.get("lands_on") == name)
              and not x.get("invalidated_by")]
    landed = landed[-MEMORY_NOTES:]
    lines = ["# memory — the record, projected", ""]
    # surface: 8
    lines.append("*written by `sandbox canon --memory` from the landed record. "
                 "a session reads this page; the next run overwrites whatever "
                 "a session wrote on it.*")
    lines.append("")
    lines.append("as of %s · %d standing ruling(s) · %d landed line(s)"
                 % (journal.now()[:10], len(standing), len(landed)))
    lines.append("")
    lines.append("## what stands")
    lines.append("")
    lines += ["- " + r for r in standing] or ["- nothing stands here yet."]
    lines += ["", "## the last %d landed" % MEMORY_NOTES, ""]
    lines += ["- [%s] [%s] %s" % (_mark(x), x.get("origin", "machine"),
                                  x.get("body", "")) for x in landed] \
        or ["- nothing has landed here yet."]
    if len(lines) > MEMORY_LINES:
        lines = lines[:MEMORY_LINES - 1]
        # surface: 8
        lines.append("*cut at %d lines — the whole record opens with "
                     "`sandbox recall`.*" % MEMORY_LINES)
    d = os.path.join(ws, ".claude")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "MEMORY.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path, len(lines)


def _mark(x):
    """what a line wears in front: the rung it earned, or that it was struck."""
    return "struck" if x.get("invalidated_by") else x.get("ink")


def recall(ws, query, target_project=None):
    """search the landed record. Returns matching lines, ink worn openly."""
    world = registry.project(ws)
    q = query.lower()
    hits = []
    for r in world["ruling"]:
        if q in (r.get("body") or "").lower():
            if target_project and r.get("binds") != target_project:
                continue
            mark = "struck" if r.get("invalidated_by") else r.get("stratum")
            hits.append("[%s] ruling: %s" % (mark, r["body"]))
    for x in world["note"]:
        if q in (x.get("body") or "").lower():
            if target_project and x.get("lands_on") != target_project:
                continue
            hits.append("[%s] [%s] %s" % (_mark(x), x.get("origin"), x["body"]))
    return hits


def rulings(ws, target_project=None):
    """law 14's read: the rulings that stand right now, newest first.

    A superseded one is off this list and still on the record; a struck one
    is off it too. Both stay readable through `sandbox recall`.
    """
    world = registry.project(ws)
    standing = registry.newest_word(world, on=target_project)
    standing = sorted(standing, key=lambda r: r.get("ts") or "", reverse=True)
    return ["[%s] ruling: %s" % (r.get("stratum", "taste"), r.get("body"))
            for r in standing]


def shown(ws, digest):
    """everything that rode one keypress — the other half of `shown:`.

    The landing writes the fingerprint of the block a person read onto every
    line it lands. This reads it back, so a fact found a year later can show
    the company it kept at the moment it landed.
    """
    world = registry.project(ws)
    events, _ = journal.read(ws)
    ids = {e.get("id") for e in events
           if (e.get("shown") or "").startswith(digest)}
    if not ids:
        return []
    out = []
    for r in world["ruling"]:
        if r["id"] in ids:
            out.append("[%s] ruling: %s" % (r.get("stratum", "taste"), r.get("body")))
    for x in world["note"]:
        if x["id"] in ids:
            out.append("[%s] [%s] %s" % (_mark(x), x.get("origin"), x.get("body")))
    return out


def _session_around(world, ts):
    """the sitting that was open when a line landed — open at or before it,
    closed at or after it (or still open). The old walk named the last session
    event at or before the fact, which could be another sitting's close; a
    session that was already over is not the one a fact happened inside."""
    best = None
    for s in world["session"]:
        opened, closed = s.get("opened") or "", s.get("closed")
        if opened > ts:
            continue
        if closed and closed < ts:
            continue
        if best is None or opened > (best.get("opened") or ""):
            best = s
    return best


def why(ws, query):
    """the lineage walk: for the newest fact matching the query, every link
    the record can carry, one addressed line each.

    The chain runs fact → the note that proposed it → the sitting it landed
    inside → the block the key was pressed over, and then out to what it
    rests on: its receipt, the ruling it replaced, the check that proved it,
    the second thought that struck it. Each line carries an address, because
    the point of the walk is that a person can go and look.
    """
    events, _ = journal.read(ws)
    world = registry.project(ws)
    q = query.lower()
    hit = None
    for e in events:
        if e.get("op") == "assert" and q in (e.get("body") or "").lower():
            hit = e  # newest wins — keep walking
    if hit is None:
        return ["nothing landed matches %r" % query]
    seen = next((x for x in world["note"] if x.get("id") == hit.get("id")), None)
    mark = _mark(seen) if seen else hit.get("ink", "claimed")
    out = ["the fact: [%s] [%s]%s %s" % (mark, hit.get("origin", "machine"),
                                         " [%s]" % hit["hand"] if hit.get("hand") else "",
                                         hit.get("body"))]
    if hit.get("staged_at"):
        out.append("staged: %s  (draft %s)"
                   % (hit["staged_at"], (hit.get("from_draft") or "")[:8]))
    out.append("landed: %s  (journal:%s)" % (hit.get("ts"), hit.get("id")))
    if hit.get("receipt"):
        out.append("receipt: %s" % hit["receipt"])
    sitting = _session_around(world, hit.get("ts") or "")
    if sitting:
        shut = ("closed %s" % sitting["closed"]) if sitting.get("closed") else "still open"
        out.append("during session: %s (opened %s, %s)"
                   % (sitting.get("key") or sitting.get("id"),
                      sitting.get("opened"), shut))
    if hit.get("supersedes"):
        old = next((e for e in events if e.get("id") == hit["supersedes"]), None)
        if old:
            out.append("supersedes: %s (%s)" % (old.get("body"), old.get("ts")))
    if seen and seen.get("proved_by"):
        run = next((e for e in events if e.get("id") == seen["proved_by"]), None)
        out.append("proved by: check %s (%s green, %s)"
                   % (seen["proved_by"], (run or {}).get("green"), (run or {}).get("ts")))
    if seen and seen.get("invalidated_by"):
        out.append("struck by: %s — %s" % (seen["invalidated_by"],
                                           seen.get("invalidated_why")))
    if hit.get("shown"):
        dig = hit["shown"][:8]
        rode = len([e for e in events if e.get("shown") == hit["shown"]]) - 1
        if rode > 1:
            out.append("shown: %s with %d others — see them: sandbox recall --shown %s"
                       % (dig, rode, dig))
        elif rode == 1:
            out.append("shown: %s with 1 other — see them: sandbox recall --shown %s"
                       % (dig, dig))
        else:
            out.append("shown: %s — it rode your key alone" % dig)
    return out
