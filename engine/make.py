# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""make: a piece of building wrapped so the diff is the receipt.

`make --open "intent"` snapshots the project's file listing; `make --close`
walks it again and lands what actually changed, so the count is computed
from the files rather than taken from anyone's account of the work. The
close re-runs the project's own checks first: green ends by naming the ship,
red refuses and the make stays open (R11). The summary stages behind the
owner's key — what happened is a fact the record keeps, what it meant is a
claim that waits for a keypress.

The building itself happens in the session the owner already sits in. This
module runs no builder and writes no file into the project.
"""
import hashlib
import json
import os

from . import check, desk, journal, project

SKIP = {".git", "__pycache__", ".DS_Store", ".make"}


def _listing(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in filenames:
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            try:
                with open(p, "rb") as f:
                    out[rel] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                continue
    return out


def _open_path(ws, name):
    return os.path.join(ws, journal.STATE_DIR, "make-open-%s.json" % name)


def open_session(ws, name, intent):
    if not os.path.exists(project.contract_path(ws, name)):
        # surface: 3a
        return False, "no project named %s" % name
    p = _open_path(ws, name)
    if os.path.exists(p):
        # surface: 3a
        return False, "a make session is already open on %s — close it first" % name
    root = project.root_of(ws, name)
    snap = {"intent": intent, "root": root, "listing": _listing(root),
            "opened": journal.now()}
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(snap, f)
    journal.append(ws, {"op": "make", "phase": "open", "project": name,
                        "body": intent, "origin": "machine",
                        "triggered": "session"})
    # surface: 2
    return True, "session open on %s — %s" % (name, intent)


def close_session(ws, name, summary=""):
    """the close: the checks first, then the diff, then the staged summary.

    The order is the 08-01 scar's rule — a close that claims a piece of work
    re-runs what the work rests on before it says a word about it.
    """
    p = _open_path(ws, name)
    if not os.path.exists(p):
        # surface: 3a
        return False, "no make session open on %s" % name
    c = project.parse_contract(project.contract_path(ws, name))
    checks = c["checks"] if c else []
    if checks:
        green, results = check.run_checks(ws, name)
        if not green:
            red = [line for line, _said, rc in results if rc != 0]
            # surface: 30
            return False, ("%d red — no close: FAIL %s. fix them, then: "
                           "sandbox make --close %s" % (len(red), red[0], name))
    with open(p, encoding="utf-8") as f:
        snap = json.load(f)
    now_listing = _listing(snap["root"])
    before = snap["listing"]
    added = sorted(set(now_listing) - set(before))
    removed = sorted(set(before) - set(now_listing))
    changed = sorted(k for k in now_listing if k in before and now_listing[k] != before[k])
    diff = {"added": added, "removed": removed, "changed": changed}
    event = journal.append(ws, {
        "op": "make", "phase": "close", "project": name,
        "body": snap["intent"], "origin": "machine", "triggered": "session",
        "diff": diff, "checks": "green" if checks else "none"})
    os.remove(p)
    n = len(added) + len(removed) + len(changed)
    if summary:
        desk.submit(ws, {"body": "make: %s: %s" % (name, summary),
                         "cls": "make-summary", "origin": "machine",
                         "project": name, "receipt": "journal:%s" % event["id"]})
    # "confirmed" is earned by a real diff; an empty one says "attempted" —
    # the word must not grade itself generously in exactly the place this
    # system claims it does not.
    # surface: 2
    if n:
        lines = ["confirmed — %d file(s) changed on %s" % (n, name)]
    else:
        lines = ["attempted — nothing changed on %s (the diff is empty, and says so)" % name]
    for rel in (added + changed + removed)[:20]:
        lines.append("  " + rel)
    if summary:
        lines.append("1 summary staged, waiting on your keypress. approve it:  sandbox approve")
    if checks:
        lines.append("checks green — ship it: sandbox ship %s" % name)
    else:
        lines.append("nothing under ## checks — a ship with nothing under it "
                     "is a costume; add one line there")
    return True, "\n".join(lines)
