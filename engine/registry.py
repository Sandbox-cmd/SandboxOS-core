# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the registry: the typed read over the record — never a second store.

The workshop's world, named: what kinds of things exist (a project, a build,
an app, a note, a ruling, a check, a session, an event) and how they link.
Everything here is a PROJECTION of the journal plus on-disk cards; delete
every projection and this module rebuilds them from truth. The schema stays
deliberately small — name, description, a few typed fields — because a wrong
model is more dangerous than no model, and small models stay right.

Facts carry their epistemic status openly (law 1): origin says whose hand,
ink says what the claim may say about itself. Rulings carry their stratum
(law 14): law binds until amended; taste is dated and the newest word wins.
"""
import hashlib
import json
import os
import time

# --- the schema ---------------------------------------------------------
# One entry per entity type: description + the fields a projection fills.
# Fields marked fact-shaped carry {value, origin, ink, landed_by, landed_at,
# receipt} rather than a bare value.
#
# the descriptions below are read by a builder and by test_registry; nothing
# renders them, so they answer to no surfaces row.
# surface: none
TYPES = {
    "project": {
        "description": "one piece of work with a goal, a contract file, and a projected canon",
        "fields": ("name", "goal", "state", "root"),
    },
    "build": {
        "description": "a saved reusable build on the shelf: card + one payload + sha256",
        "fields": ("name", "pressed_from", "sha256", "origin"),
    },
    "app": {
        "description": "an installed add-on: manifest + exact placement record",
        "fields": ("name", "source", "version", "min_core"),
    },
    "note": {
        "description": "a staged or landed fact",
        "fields": ("body", "cls", "origin", "ink"),
    },
    "ruling": {
        "description": "a landed decision; binds a project or the workshop",
        "fields": ("body", "stratum", "supersedes"),  # stratum: law | taste
    },
    "check": {
        "description": "one runnable line a ship rests on",
        "fields": ("line", "project", "ratified_hash"),
    },
    "session": {
        "description": "one working session; lineage queries terminate on it by name",
        "fields": ("id", "opened", "closed", "project", "key", "agents"),
    },
    "event": {
        "description": "one journal line — the substrate every other type projects from",
        "fields": ("id", "op", "ts"),
    },
}

# Typed links, both directions named: (from, link, to, reverse).
LINKS = (
    ("ruling", "binds", "project", "bound_by"),
    ("ruling", "supersedes", "ruling", "superseded_by"),
    ("build", "pressed_from", "project", "pressed"),
    ("build", "used_on", "project", "used"),
    ("app", "installed_in", "workshop", "installed"),
    ("check", "belongs_to", "project", "checks"),
    ("note", "lands_on", "project", "notes"),
    ("event", "about", "any", "events"),
    ("session", "worked", "project", "sessions"),
)

STRATA = ("law", "taste")
ORIGINS = ("human", "machine", "external")
INKS = ("checked", "receipted", "claimed")


def fact(value, origin, ink, landed_by=None, landed_at=None, receipt=None):
    """the fact shape: a value that carries its own epistemic status."""
    if origin not in ORIGINS:
        raise ValueError("fact: origin must be one of %s" % (ORIGINS,))
    if ink not in INKS:
        raise ValueError("fact: the mark must be one of %s" % (INKS,))
    return {"value": value, "origin": origin, "ink": ink,
            "landed_by": landed_by, "landed_at": landed_at, "receipt": receipt}


# --- the projection -----------------------------------------------------

def project(ws):
    """project the registry's world from the journal and the cards on disk.

    Returns {type: [instances]}. Writes nothing, caches nothing — run it
    twice and the answers are equal, which the suite proves. The journal is
    the spine: a card no event names, and an event whose card is gone, both
    show here wearing `carded`, because a disagreement is a thing to report
    and never a thing to hide.

    Two rungs are raised here rather than stored. A green `check` names the
    lines it proves and those lines read `checked` with the stored ink kept
    beside them; an `invalidate` strikes its target. Neither rewrites a
    landed line — law 1 and law 2 mean the read carries the second thought.
    """
    from . import journal
    events, scars = journal.read(ws)
    world = {t: [] for t in TYPES}
    world["_scars"] = list(scars)
    open_sessions = {}
    proved, struck = {}, {}
    checked_at = {}
    for e in events:
        world["event"].append({"id": e.get("id"), "op": e.get("op"), "ts": e.get("ts")})
        op = e.get("op")
        if op == "session":
            _fold_session(world, open_sessions, e)
        elif op == "check":
            name = e.get("project")
            checked_at[name] = e
            for nid in e.get("proves") or ():
                proved[nid] = e.get("id")
        elif op == "invalidate":
            if e.get("of"):
                struck[e["of"]] = {"by": e.get("id"), "why": e.get("body"),
                                   "ts": e.get("ts")}
        elif op == "assert":
            cls = e.get("cls", "note")
            if cls == "ruling":
                world["ruling"].append({
                    "body": e.get("body"),
                    "stratum": e.get("stratum", "taste"),
                    "supersedes": e.get("supersedes"),
                    "binds": e.get("project", "workshop"),
                    "ts": e.get("ts"), "id": e.get("id")})
            else:
                world["note"].append({
                    "body": e.get("body"), "cls": cls,
                    "origin": e.get("origin", "machine"),
                    "ink": e.get("ink", "claimed"),
                    "ink_landed": e.get("ink", "claimed"),
                    "hand": e.get("hand"),
                    "lands_on": e.get("project", "workshop"),
                    "id": e.get("id")})

    for x in world["note"]:
        if x["id"] in proved:
            x["ink"] = "checked"
            x["proved_by"] = proved[x["id"]]
        mark = struck.get(x["id"])
        if mark:
            x["invalidated_by"] = mark["by"]
            x["invalidated_why"] = mark["why"]
    for r in world["ruling"]:
        mark = struck.get(r["id"])
        if mark:
            r["invalidated_by"] = mark["by"]
            r["invalidated_why"] = mark["why"]

    _fold_projects(ws, world, events)
    _fold_builds(ws, world, events)
    _fold_apps(ws, world)
    _fold_checks(ws, world, events, checked_at)
    return world


def _fold_session(world, open_sessions, e):
    """one sitting, keyed by the host's own session id.

    A close finds its open by `key` and by nothing else: an open minted
    without one could never be closed, which is why every session event the
    engine mints carries it. The seventh body's rows carry neither `key` nor
    `phase` — they stay exactly as they are, named as sittings nobody can
    close, rather than guessed into shape.
    """
    sid, phase, k = e.get("id"), e.get("phase"), e.get("key")
    if phase == "open":
        rec = {"id": sid, "opened": e.get("ts"), "closed": None,
               "project": e.get("project"), "key": k, "agents": None}
        world["session"].append(rec)
        if k:
            open_sessions[k] = rec
    elif phase == "close" and k in open_sessions:
        rec = open_sessions.pop(k)
        rec["closed"] = e.get("ts")
        if e.get("agents"):
            rec["agents"] = e["agents"]


def _fold_projects(ws, world, events):
    """`cls: project-state` events joined to the contract on disk."""
    from . import project as prj
    seen = {}
    for e in events:
        if e.get("op") == "assert" and e.get("cls") == "project-state" and e.get("project"):
            row = seen.setdefault(e["project"], {"name": e["project"], "goal": "",
                                                 "state": None, "root": None,
                                                 "carded": False, "evented": True})
            row["last_said"] = e.get("body")
    for c in prj.list_all(ws):
        row = seen.setdefault(c["dir"], {"name": c["dir"], "goal": "", "state": None,
                                         "root": None, "carded": False, "evented": False})
        row.update({"goal": c.get("goal", ""), "state": c.get("state"),
                    "root": prj.root_of(ws, c["dir"]), "carded": True})
    world["project"] = [seen[n] for n in sorted(seen)]


def _fold_builds(ws, world, events):
    """`cls: build-kept` events joined to the shelf's own cards."""
    from . import shelf
    seen = {}
    for e in events:
        if e.get("op") == "assert" and e.get("cls") == "build-kept":
            said = e.get("build") or (
                e.get("body") or "").split(":", 1)[-1].strip().split(" ")[0]
            if said:
                seen.setdefault(said, {"name": said, "pressed_from": None,
                                       "sha256": None, "origin": e.get("origin"),
                                       "carded": False, "evented": True})
    for c in shelf.list_all(ws):
        row = seen.setdefault(c["name"], {"name": c["name"], "pressed_from": None,
                                          "sha256": None, "origin": None,
                                          "carded": False, "evented": False})
        row.update({"pressed_from": c.get("from"), "sha256": c.get("sha256"),
                    "origin": c.get("origin"), "carded": True})
    world["build"] = [seen[n] for n in sorted(seen)]


def _fold_apps(ws, world):
    """the placement books under `.sandbox/apps/` — one per installed app."""
    from . import apps
    world["app"] = [{"name": a.get("name"), "source": a.get("source"),
                     "version": a.get("version"), "min_core": a.get("min_core"),
                     "placed": len(a.get("placed") or ())}
                    for a in apps.list_installed(ws)]


def _fold_checks(ws, world, events, checked_at):
    """the `## checks` lines a ship rests on, joined to what ran on them."""
    from . import project as prj
    # ratified is the owner's key on an exact text, so only a `ratify` fills
    # it; a check run proves the lines are green and ratifies nothing.
    ratified = {}
    for e in events:
        if e.get("op") == "ratify" and e.get("project"):
            ratified[e["project"]] = e.get("hash")
    names = set(ratified) | set(checked_at)
    out = []
    for c in prj.list_all(ws):
        names.discard(c["dir"])
        run = checked_at.get(c["dir"])
        for line in c.get("checks") or ():
            out.append({"line": line, "project": c["dir"],
                        "ratified_hash": ratified.get(c["dir"]),
                        "green": run.get("green") if run else None,
                        "last_run": run.get("ts") if run else None})
    for name in sorted(names):
        run = checked_at.get(name)
        out.append({"line": None, "project": name,
                    "ratified_hash": ratified.get(name),
                    "green": run.get("green") if run else None,
                    "last_run": run.get("ts") if run else None})
    world["check"] = out


# --- the index: a projection with a speed decision inside it ---------------
#
# Two thresholds, both printed by doctor, so the day one is crossed is a day
# a person can see rather than guess at. Under them the counts are computed
# in memory and thrown away; over them the same counts are kept on disk with
# a hash of the journal prefix they were folded from, so a history that moved
# is caught rather than believed. The journal itself never shrinks and is
# never compacted: the index is the only thing here that is ever discarded.
INDEX_AT_EVENTS = 50000
INDEX_AT_MS = 250
INDEX_FILE = "index.json"


def index_path(ws):
    from . import journal
    return os.path.join(ws, journal.STATE_DIR, INDEX_FILE)


def index(ws, write=True):
    """the bounded read: counts, and the journal prefix they cover.

    Rebuildable from the record alone — delete the file and the next call
    answers the same thing. `covers` is the lines, bytes and sha256 of the
    prefix that was folded, so a prefix that stops matching says history
    moved and the kept copy is thrown away rather than trusted.

    `write=False` is the looking caller's door: doctor prints these counts on
    every run and must leave the workshop byte-for-byte as it found it, so it
    asks for the fold without the keeping (law 12).
    """
    from . import journal
    start = time.time()
    p = journal.path(ws)
    raw = b""
    if os.path.exists(p):
        with open(p, "rb") as f:
            raw = f.read()
    events, scars = journal.read(ws)
    by_op, by_ink, hand = {}, {}, 0
    for e in events:
        op = e.get("op") or "?"
        by_op[op] = by_op.get(op, 0) + 1
        if e.get("ink"):
            by_ink[e["ink"]] = by_ink.get(e["ink"], 0) + 1
        if e.get("hand"):
            hand += 1
    built_ms = int(round((time.time() - start) * 1000))
    out = {"events": len(events), "by_op": by_op, "by_ink": by_ink,
           "hand": hand, "scars": len(scars),
           "covers": {"lines": raw.count(b"\n"), "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest()},
           "built_ms": built_ms}
    if write and (len(events) >= INDEX_AT_EVENTS or built_ms >= INDEX_AT_MS):
        os.makedirs(os.path.dirname(index_path(ws)), exist_ok=True)
        with open(index_path(ws), "w", encoding="utf-8") as f:
            json.dump(out, f)
    return out


def newest_word(world, on=None):
    """law 14's read: the rulings that currently stand.

    A ruling that another ruling names in `supersedes` is superseded — shown
    in chronology, never deleted. Filter by `on` (a project name or
    'workshop') if given.
    """
    rulings = world["ruling"]
    superseded = {r["supersedes"] for r in rulings if r.get("supersedes")}
    standing = [r for r in rulings
                if r["id"] not in superseded and not r.get("invalidated_by")]
    if on is not None:
        standing = [r for r in standing if r.get("binds") == on]
    return standing


# --- rebuilding a projection from the record ------------------------------

PROJECTIONS = ("place", "shelf", "canon", "index")


def rebuild(ws, name):
    """rewrite one projection from the journal and the cards. (ok, lines).

    Every name here is derived, never authored: delete the file and this
    puts it back. What it will never do is invent an event to match a file
    it found — a disk that knows something the record does not is named and
    left alone, because a projection may be rebuilt and the record may not.
    """
    if name not in PROJECTIONS:
        # surface: 3a
        return False, ["no projection named %s — try: %s"
                       % (name, ", ".join(PROJECTIONS))]
    return globals()["_rebuild_" + name](ws)


def _rebuild_place(ws):
    """place.json, folded from the `place` events that made every move."""
    from . import journal, placement
    from . import status
    events, _ = journal.read(ws)
    book, n = {}, 0
    for e in events:
        if e.get("op") != "place" or not e.get("path"):
            continue
        if e.get("action") not in status.PLACE_ACTIONS:
            continue
        n += 1
        if e.get("action") == "removed":
            book.pop(e["path"], None)
        else:
            book[e["path"]] = {"sha": e.get("sha")}
    placement.write_book(ws, book)
    # surface: 7
    return True, ["rewrote the placement book: %d file(s) from %d event(s)"
                  % (len(book), n)]


def _rebuild_shelf(ws):
    """each card's used-ledger, folded from the `build-used` events.

    The payload and the press are the disk's own; what the record owns here
    is where a build went afterwards, so that is what is rewritten.
    """
    from . import journal, shelf
    events, _ = journal.read(ws)
    used, kept = {}, set()
    for e in events:
        if e.get("op") != "assert":
            continue
        if e.get("cls") == "build-kept" and e.get("build"):
            kept.add(e["build"])
        if e.get("cls") == "build-used" and e.get("build"):
            used.setdefault(e["build"], []).append(
                "used on %s %s" % (e.get("project") or "a project",
                                   (e.get("ts") or "")[:10]))
    lines, touched = [], 0
    for card in shelf.list_all(ws):
        if shelf.write_used(ws, card["name"], used.get(card["name"], [])):
            touched += 1
        if card["name"] not in kept:
            # surface: 7
            lines.append("kept on disk and unknown to the record: %s"
                         % card["name"])
    # surface: 7
    lines.insert(0, "rewrote %d used-ledger(s) from %d event(s)"
                 % (touched, sum(len(v) for v in used.values())))
    return True, lines


def _rebuild_canon(ws):
    """every CANON.md page, the workshop's and each project's."""
    from . import notes, project as prj
    notes.refresh_canon(ws)
    n = 1
    for c in prj.list_all(ws):
        notes.refresh_canon(ws, c["dir"])
        n += 1
    # surface: 7
    return True, ["rewrote %d canon page(s) from the record" % n]


def _rebuild_index(ws):
    """the kept counts, folded again and written whatever the threshold says."""
    out = index(ws, write=False)
    os.makedirs(os.path.dirname(index_path(ws)), exist_ok=True)
    with open(index_path(ws), "w", encoding="utf-8") as f:
        json.dump(out, f)
    # surface: 7
    return True, ["rewrote the index: %d event(s), folded in %d ms"
                  % (out["events"], out["built_ms"])]
