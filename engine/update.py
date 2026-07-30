# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""update — the system moves; your things don't.

The workshop records which core version last touched it and the highest
migration applied (code-written, beside the record). Boot and doctor name
skew plainly instead of letting a new engine meet an old workshop in
silence. Migrations are numbered, idempotent, owner-run; the journal's
stored field names never change and the record is never rewritten. The
seventh-body seams live here too: a path-map that lets old receipts open at
their new addresses, and the ratification voiding that is said OUT LOUD
instead of surprising every ship.
"""
import json
import os
import subprocess

from . import journal, placement


def _version_path(ws):
    return os.path.join(ws, journal.STATE_DIR, "core-version.json")


def core_version():
    from .cli import ROOT
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


def recorded(ws):
    p = _version_path(ws)
    if not os.path.exists(p):
        return {"version": None, "migration": 0}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def record_version(ws, migration=None):
    r = recorded(ws)
    r["version"] = core_version()
    if migration is not None:
        r["migration"] = migration
    os.makedirs(os.path.dirname(_version_path(ws)), exist_ok=True)
    with open(_version_path(ws), "w", encoding="utf-8") as f:
        json.dump(r, f)
    return r


def skew(ws):
    """None when current; otherwise one plain sentence."""
    r = recorded(ws)
    cur = core_version()
    if r["version"] is None:
        return "this workshop has never met this core — run: sandbox update"
    if r["version"] != cur:
        return ("the core is %s but this workshop last saw %s — run: sandbox update"
                % (cur, r["version"]))
    pending = [m for m in MIGRATIONS if m[0] > r.get("migration", 0)]
    if pending:
        return "%d migration(s) pending — run: sandbox update" % len(pending)
    return None


# --- migrations ---------------------------------------------------------
# (number, description, fn(ws) -> str). Numbered, idempotent, appended only.
MIGRATIONS = []


def migrate(ws):
    """Apply every pending migration, recording the high-water after each —
    a failure mid-list leaves an honest 'half-migrated' doctor can name."""
    r = recorded(ws)
    lines = []
    for number, description, fn in MIGRATIONS:
        if number <= r.get("migration", 0):
            continue
        msg = fn(ws)
        record_version(ws, migration=number)
        lines.append("migration %d: %s — %s" % (number, description, msg))
    if not lines:
        lines.append("no migrations pending")
    return lines


# --- the seventh-body seams (challenge #1, #2) --------------------------

def set_path_map(ws, pairs):
    """[(old_prefix, new_prefix)...] — receipts recorded under old roots
    open at their new addresses. The journal itself is never rewritten."""
    p = os.path.join(ws, journal.STATE_DIR, "path-map.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(list(pairs), f)


def resolve(ws, path):
    """A receipt path, through the map. Unmapped paths pass unchanged."""
    p = os.path.join(ws, journal.STATE_DIR, "path-map.json")
    if not path or not os.path.exists(p):
        return path
    with open(p, encoding="utf-8") as f:
        for old, new in json.load(f):
            if path.startswith(old):
                return new + path[len(old):]
    return path


def void_ratifications(ws, why="paths changed"):
    """Out loud, in one place — never a wall of surprise ship refusals."""
    from . import ship
    p = os.path.join(ws, journal.STATE_DIR, "ratified.json")
    if not os.path.exists(p):
        return "no ratifications to void"
    with open(p, encoding="utf-8") as f:
        names = sorted(json.load(f))
    os.remove(p)
    journal.append(ws, {"op": "assert", "cls": "note", "origin": "machine",
                        "triggered": "session",
                        "body": "ratifications voided (%s): %s" % (why, ", ".join(names)),
                        "ink": "receipted", "receipt": "journal:void"})
    return ("%d project(s)' checks await your k again — %s: %s"
            % (len(names), why, ", ".join(names)))


# --- the verb -----------------------------------------------------------

def run(ws):
    """Move both surfaces: the clone (if it has a remote and the owner's
    pull), then the workshop (re-sync + migrations + version record)."""
    from . import onboard
    from .cli import ROOT
    lines = []
    r = subprocess.run(["git", "-C", ROOT, "remote"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        lines.append("a remote exists — fetch and pull are your hands, then re-run this. "
                     "nothing was pulled for you.")
    else:
        lines.append("no remote on this clone — new versions arrive when you add one "
                     "and pull, or replace the clone; your workshop is untouched either way.")
    ok, text = onboard.run(ws)
    lines.append(text)
    lines.extend(migrate(ws))
    record_version(ws)
    lines.append("workshop now current with core %s" % core_version())
    return ok, "\n".join(lines)
