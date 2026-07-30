# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The provisional lane (amana's second speed): correct now, confirm later.

A reversible act inside ruled boundaries executes at once — but before it
touches anything, the pre-act content is snapshotted and hashed. At the next
arrival the owner confirms (it becomes a landed event) or reverts. An act
whose file has since moved on is never auto-reverted over later work: it is
presented as "needs your hand." Nothing here enters trusted memory before
the keystroke; ship refuses while any act on its project is unconfirmed.
"""
import hashlib
import json
import os
import time

from . import gate, journal

LANE = "provisional.jsonl"
SNAPS = "snapshots"


def _lane(ws):
    return os.path.join(ws, journal.STATE_DIR, LANE)


def _snapdir(ws):
    return os.path.join(ws, journal.STATE_DIR, SNAPS)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _read_lane(ws):
    p = _lane(ws)
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _write_lane(ws, entries):
    with open(_lane(ws), "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def act(ws, path, new_content, why, project=None):
    """Execute a reversible act now. Snapshot first, write second.

    Returns the lane entry. The act is marked provisional until the owner's
    keystroke at resume; its revert path is the snapshot, and its honesty is
    the pair of hashes.
    """
    os.makedirs(_snapdir(ws), exist_ok=True)
    existed = os.path.exists(path)
    before = open(path, "rb").read() if existed else b""
    aid = "prv-" + _sha(("%s|%s|%s" % (path, why, time.time())).encode())[:10]
    snap = os.path.join(_snapdir(ws), aid)
    with open(snap, "wb") as f:
        f.write(before)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    entry = {
        "id": aid, "path": os.path.abspath(path), "why": why,
        "project": project, "ts": journal.now(),
        "existed_before": existed,
        "before_sha": _sha(before),
        "after_sha": _sha(new_content.encode("utf-8")),
        "snapshot": snap,
    }
    entries = _read_lane(ws)
    entries.append(entry)
    os.makedirs(os.path.dirname(_lane(ws)), exist_ok=True)
    _write_lane(ws, entries)
    return entry


def pending(ws, project=None):
    """Unconfirmed acts — the count status and boot must name plainly."""
    acts = _read_lane(ws)
    if project is not None:
        acts = [a for a in acts if a.get("project") == project]
    return acts


def oldest_age_days(ws):
    acts = _read_lane(ws)
    if not acts:
        return 0
    oldest = min(a["ts"] for a in acts)
    then = time.mktime(time.strptime(oldest, "%Y-%m-%dT%H:%M:%SZ"))
    return max(0, int((time.time() - then) // 86400))


def status_of(ws, entry):
    """clean (revertible or confirmable as-taken) | moved-on (needs your hand)."""
    path = entry["path"]
    current = open(path, "rb").read() if os.path.exists(path) else b""
    return "clean" if _sha(current) == entry["after_sha"] else "moved-on"


def confirm(ws, aid, consent):
    """The keystroke lands the act as a journal event. Headless lands nothing."""
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        return False, "confirming needs your %r at a real terminal" % gate.COMMIT_KEY
    entries = _read_lane(ws)
    keep, hit = [], None
    for e in entries:
        if e["id"] == aid:
            hit = e
        else:
            keep.append(e)
    if hit is None:
        return False, "no provisional act named %s" % aid
    event = {"op": "assert", "cls": "provisional-confirmed", "body": hit["why"],
             "project": hit.get("project"), "origin": "human",
             "receipt": hit["snapshot"], "ink": "receipted"}
    if consent.get("synthetic"):
        event["hand"] = "synthetic"
    journal.append(ws, event)
    _write_lane(ws, keep)
    os.remove(hit["snapshot"])
    return True, "confirmed — landed with your key"


def revert(ws, aid):
    """Restore the snapshot — but only over a file that hasn't moved on.

    A moved-on file is never auto-reverted; the answer is 'needs your hand',
    with both hashes shown so the owner can see exactly what drifted.
    """
    entries = _read_lane(ws)
    hit = next((e for e in entries if e["id"] == aid), None)
    if hit is None:
        return False, "no provisional act named %s" % aid
    if status_of(ws, hit) != "clean":
        return False, ("needs your hand — %s changed after this act "
                       "(after-sha %s, now different); nothing auto-reverted"
                       % (hit["path"], hit["after_sha"][:12]))
    with open(hit["snapshot"], "rb") as f:
        before = f.read()
    if hit["existed_before"]:
        with open(hit["path"], "wb") as f:
            f.write(before)
    else:
        os.remove(hit["path"])
    _write_lane(ws, [e for e in entries if e["id"] != aid])
    os.remove(hit["snapshot"])
    return True, "reverted — the file is as it was before the act"
