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

from . import desk, journal, placement


SHIM_DIR_ENV = "SANDBOX_SHIM_DIR"


def _version_path(ws):
    return os.path.join(ws, journal.STATE_DIR, "core-version.json")


def shim_dir():
    """where the `sandbox` shim goes. The env var is for tests and probe
    workshops; every other machine gets ~/.local/bin."""
    return os.path.expanduser(os.environ.get(SHIM_DIR_ENV) or "~/.local/bin")


def write_shim():
    """the one shim, pointed at this copy. Returns (path, dir, on the PATH?).

    `setup`'s whole body — the file, its mode, and whether the shell would
    find it. It lives here, beside the migration that rewrites the same file,
    and the verb does the printing.
    """
    from .cli import ROOT
    d = shim_dir()
    os.makedirs(d, exist_ok=True)
    shim = os.path.join(d, "sandbox")
    with open(shim, "w", encoding="utf-8") as f:
        f.write('#!/bin/sh\nexec "%s" "$@"\n' % os.path.join(ROOT, "sandbox"))
    os.chmod(shim, 0o755)
    return shim, d, d in os.environ.get("PATH", "")


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
    """none when current; otherwise one plain sentence."""
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
def _migration_one_home(ws):
    """9.0: the tool lives in one home. The shim follows this copy; the
    placed files re-baseline against what ships here. The old trees are
    left where they are — deleting them is the owner's hand."""
    from .cli import ROOT
    shim = os.path.join(shim_dir(), "sandbox")
    moved = "shim untouched (none found)"
    if os.path.exists(shim):
        try:
            with open(shim, encoding="utf-8") as f:
                body = f.read()
            if os.path.join(ROOT, "sandbox") not in body:
                with open(shim, "w", encoding="utf-8") as f:
                    f.write('#!/bin/sh\nexec "%s" "$@"\n' % os.path.join(ROOT, "sandbox"))
                os.chmod(shim, 0o755)
                moved = "shim now runs this copy"
            else:
                moved = "shim already runs this copy"
        except OSError as e:
            moved = "shim left alone (%s)" % e
    return moved


def _retired_placements(ws):
    """what 8.x placed into the workshop and 9.0 loads from the plugin.

    The guard beside the record, the six briefs, and the style: every one of
    them now ships inside `vessel/plugin/` and is read from there, so the copy
    in the workshop is a second version of a file with one home.
    """
    from . import journal as j
    out = [os.path.join(ws, j.STATE_DIR, "vessel", "guard.py"),
           os.path.join(ws, ".claude", "output-styles", "across-the-desk.md")]
    adir = os.path.join(ws, ".claude", "agents")
    if os.path.isdir(adir):
        out += [os.path.join(adir, n) for n in sorted(os.listdir(adir))
                if n.endswith(".md")]
    return out


def _migration_two_plugin(ws):
    """9.0: the vessel is one plugin. Everything the workshop was given a copy
    of is loaded from the plugin now, so the copies go — the pristine ones.

    An edited copy stays where it is and is named: a file the owner changed is
    the owner's, and this migration removes nothing it did not place. Nothing
    under `~/.claude` is touched at all — that directory is his.
    """
    from . import onboard, placement
    lines = []
    b = placement.book(ws)
    for dest in _retired_placements(ws):
        if not os.path.exists(dest):
            continue
        rec = b.get(dest)
        name = os.path.basename(dest)
        if rec and placement.file_sha(dest) == rec.get("sha"):
            os.remove(dest)
            del b[dest]
            lines.append("removed %s — the plugin serves it now" % name)
        else:
            lines.append("kept %s — you changed it, so it stays" % name)
    placement.write_book(ws, b)

    pointer = os.path.join(ws, journal.STATE_DIR, "vessel", "engine-root")
    if os.path.exists(pointer):
        os.remove(pointer)
        lines.append("removed engine-root — the plugin says where the tree is")
    vdir = os.path.dirname(pointer)
    if os.path.isdir(vdir) and not os.listdir(vdir):
        os.rmdir(vdir)

    if not lines:
        lines.append("nothing 8.x placed is left in this workshop")

    if onboard.wired(ws):
        lines.append("settings already carry the plugin's entry")
    else:
        _ok, wiring = onboard.emit_settings(ws)
        lines.extend(wiring)
    for name in onboard.shadowed_skills():
        lines.append("%s under ~/.claude/skills shadows the plugin's — "
                     "retire it when you like: rm -r ~/.claude/skills/%s"
                     % (name, name))
    return lines


# surface: 7
MIGRATIONS = [
    (1, "one home — the shim follows this copy", _migration_one_home),
    (2, "one plugin — the placed copies retire", _migration_two_plugin),
]


def migrate(ws):
    """apply every pending migration, recording the high-water after each —
    a failure mid-list leaves an honest 'half-migrated' doctor can name.

    A migration that did several things hands back a line per thing; one that
    did a single thing hands back a sentence and reads on one row.
    """
    r = recorded(ws)
    lines = []
    for number, description, fn in MIGRATIONS:
        if number <= r.get("migration", 0):
            continue
        msg = fn(ws)
        record_version(ws, migration=number)
        if isinstance(msg, (list, tuple)):
            lines.append("migration %d: %s" % (number, description))
            lines.extend("  " + str(m) for m in msg)
        else:
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
    """a receipt path, through the map. Unmapped paths pass unchanged."""
    p = os.path.join(ws, journal.STATE_DIR, "path-map.json")
    if not path or not os.path.exists(p):
        return path
    with open(p, encoding="utf-8") as f:
        for old, new in json.load(f):
            if path.startswith(old):
                return new + path[len(old):]
    return path


def void_ratifications(ws, why="paths changed"):
    """out loud, in one place — never a wall of surprise ship refusals."""
    from . import ship
    p = os.path.join(ws, journal.STATE_DIR, "ratified.json")
    if not os.path.exists(p):
        return "no ratifications to void"
    with open(p, encoding="utf-8") as f:
        names = sorted(json.load(f))
    os.remove(p)
    desk.mint(ws, {"cls": "note", "origin": "machine", "triggered": "session",
                   "body": "ratifications voided (%s): %s" % (why, ", ".join(names)),
                   "receipt": "journal:void"})
    return ("%d project(s)' checks await your k again — %s: %s"
            % (len(names), why, ", ".join(names)))


# --- the verb -----------------------------------------------------------

def run(ws):
    """move both surfaces: the clone (if it has a remote and the owner's
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
