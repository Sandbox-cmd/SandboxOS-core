# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""make --open / --close: the honest bookkeeping around building.

Open snapshots the project's file listing (name + content hash) so close can
COMPUTE what changed — the diff is code's word, never the builder's. Close
mints the make event with the computed diff as its receipt and stages the
builder's summary behind the owner's key: what happened is fact (event),
what it meant is a claim (staged note).
"""
import hashlib
import json
import os

from . import desk, journal, project

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
        return False, "no project named %s" % name
    p = _open_path(ws, name)
    if os.path.exists(p):
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
    return True, "session open on %s — %s" % (name, intent)


def close_session(ws, name, summary=""):
    p = _open_path(ws, name)
    if not os.path.exists(p):
        return False, "no make session open on %s" % name
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
        "diff": diff})
    os.remove(p)
    n = len(added) + len(removed) + len(changed)
    if summary:
        desk.submit(ws, {"body": "make: %s: %s" % (name, summary),
                         "cls": "make-summary", "origin": "machine",
                         "project": name, "receipt": "journal:%s" % event["id"]})
    lines = ["confirmed — %d file(s) changed on %s" % (n, name)]
    for rel in (added + changed + removed)[:20]:
        lines.append("  " + rel)
    if summary:
        lines.append("1 summary staged, waiting on your keypress. approve it:  sandbox approve")
    return True, "\n".join(lines)
