# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Placement provenance: what the system put in the workshop, and its hash.

The Hermes pattern with its edges closed: on every sync, a placed file whose
local hash still equals the recorded one is refreshed silently; a diverged
file is left alone and NAMED (never silently, never forever-quiet — doctor
repeats the law-bearing ones); a recorded file absent from the new payload
is removed if pristine, left-and-named if diverged; a divergence that
happens to equal the NEW shipped content re-baselines silently. place.json
is a projection — every move also mints a `place` event, so the record can
rebuild it.
"""
import hashlib
import json
import os
import shutil

from . import journal

BOOK = "place.json"


def _book_path(ws):
    return os.path.join(ws, journal.STATE_DIR, BOOK)


def _sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def book(ws):
    p = _book_path(ws)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _write_book(ws, b):
    os.makedirs(os.path.dirname(_book_path(ws)), exist_ok=True)
    with open(_book_path(ws), "w", encoding="utf-8") as f:
        json.dump(b, f, indent=1)


def _event(ws, action, dest, sha=None):
    journal.append(ws, {"op": "place", "action": action, "path": dest,
                        "sha": sha, "origin": "machine", "triggered": "session"})


def sync(ws, payload):
    """payload: {dest_abs_path: src_abs_path}. Returns report lines.

    law_bearing paths (hooks, the guard) get repeated divergence warnings
    via doctor reading the book's `diverged` marks.
    """
    b = book(ws)
    report = []
    for dest, src in payload.items():
        new_sha = _sha_file(src)
        rec = b.get(dest)
        if not os.path.exists(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            b[dest] = {"sha": new_sha}
            _event(ws, "placed", dest, new_sha)
            report.append("placed: %s" % dest)
            continue
        cur_sha = _sha_file(dest)
        if rec is None:
            # Never recorded → never touched. The user's file wins, said plainly.
            report.append("kept (yours, never placed by me): %s" % dest)
            continue
        if cur_sha == rec["sha"]:
            if cur_sha != new_sha:
                shutil.copy2(src, dest)
                b[dest] = {"sha": new_sha}
                _event(ws, "refreshed", dest, new_sha)
                report.append("refreshed: %s" % dest)
            continue
        if cur_sha == new_sha:
            b[dest] = {"sha": new_sha}
            _event(ws, "re-baselined", dest, new_sha)
            report.append("re-baselined (your edit matches the new version): %s" % dest)
            continue
        b[dest] = dict(rec, diverged=True)
        report.append("left alone (you changed it — updates skip it until you reset): %s" % dest)

    # Deletion: recorded files no longer in the payload.
    for dest in [d for d in list(b) if d not in payload]:
        if not os.path.exists(dest):
            del b[dest]
            continue
        cur_sha = _sha_file(dest)
        if cur_sha == b[dest]["sha"]:
            os.remove(dest)
            del b[dest]
            _event(ws, "removed", dest)
            report.append("removed (no longer shipped): %s" % dest)
        else:
            b[dest] = dict(b[dest], orphaned=True, diverged=True)
            report.append("left alone (no longer shipped, but you changed it): %s" % dest)
    _write_book(ws, b)
    return report


def diverged(ws):
    """The files updates are skipping — doctor names these at every run."""
    return [d for d, rec in book(ws).items() if rec.get("diverged")]


def reset(ws, dest, src):
    """Back to pristine, on the owner's word: re-copy and re-baseline."""
    shutil.copy2(src, dest)
    b = book(ws)
    b[dest] = {"sha": _sha_file(dest)}
    _write_book(ws, b)
    _event(ws, "reset", dest, b[dest]["sha"])
    return "reset to pristine: %s" % dest
