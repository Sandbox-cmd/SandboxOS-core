# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The registry: the typed read over the record — never a second store.

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

# --- the schema ---------------------------------------------------------
# One entry per entity type: description + the fields a projection fills.
# Fields marked fact-shaped carry {value, origin, ink, landed_by, landed_at,
# receipt} rather than a bare value.

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
        "fields": ("id", "opened", "closed", "project"),
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
    """The fact shape: a value that carries its own epistemic status."""
    if origin not in ORIGINS:
        raise ValueError("fact: origin must be one of %s" % (ORIGINS,))
    if ink not in INKS:
        raise ValueError("fact: ink must be one of %s" % (INKS,))
    return {"value": value, "origin": origin, "ink": ink,
            "landed_by": landed_by, "landed_at": landed_at, "receipt": receipt}


# --- the projection -----------------------------------------------------

def project(ws):
    """Project the registry's world from the journal alone.

    Returns {type: [instances]}. Writes nothing, caches nothing — run it
    twice and the answers are equal, which the suite proves. On-disk cards
    (project contracts, build cards, app manifests) join this projection as
    their organs land in later bands; the journal is always the spine.
    """
    from . import journal
    events, scars = journal.read(ws)
    world = {t: [] for t in TYPES}
    world["_scars"] = list(scars)
    open_sessions = {}
    for e in events:
        world["event"].append({"id": e.get("id"), "op": e.get("op"), "ts": e.get("ts")})
        op = e.get("op")
        if op == "session":
            sid = e.get("id")
            if e.get("phase") == "open":
                open_sessions[e.get("key", sid)] = {
                    "id": sid, "opened": e.get("ts"), "closed": None,
                    "project": e.get("project")}
                world["session"].append(open_sessions[e.get("key", sid)])
            elif e.get("phase") == "close" and e.get("key") in open_sessions:
                open_sessions[e["key"]]["closed"] = e.get("ts")
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
                    "lands_on": e.get("project", "workshop"),
                    "id": e.get("id")})
    return world


def newest_word(world, on=None):
    """Law 14's read: the rulings that currently stand.

    A ruling that another ruling names in `supersedes` is superseded — shown
    in chronology, never deleted. Filter by `on` (a project name or
    'workshop') if given.
    """
    rulings = world["ruling"]
    superseded = {r["supersedes"] for r in rulings if r.get("supersedes")}
    standing = [r for r in rulings if r["id"] not in superseded]
    if on is not None:
        standing = [r for r in standing if r.get("binds") == on]
    return standing
