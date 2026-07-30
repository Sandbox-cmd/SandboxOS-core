# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The record itself. Append-only JSONL; durable history no one rewrites.

A landed event is never rewritten (law 1). A torn final line (a crash
mid-append) is skipped and scarred, never fatal, and never poisons the next
append: every append starts on a fresh line. Adopted from the seventh body
with its scars intact.
"""
import json
import os
import time

STATE_DIR = ".sandbox"


def path(ws):
    return os.path.join(ws, STATE_DIR, "journal.jsonl")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ensure_genesis(ws):
    """Write the genesis line only when no journal exists. Never truncates.

    Re-running init over a living workshop must leave the record untouched —
    a past body wiped it here; every body since refuses to.
    """
    p = path(ws)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return False
    line = {"op": "genesis", "who": "desk", "ts": now(),
            "note": "the record opens empty — honest about being new"}
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return True


def append(ws, event):
    """Append one event. Stamps ts and an id if absent. Flushes before returning.

    Every event carries an id so any later record can name it as a receipt
    (`journal:<id>`) — ink depends on events being addressable.
    """
    if not isinstance(event, dict) or not event.get("op"):
        raise ValueError("journal.append: event needs an 'op'")
    event = dict(event)
    event.setdefault("ts", now())
    if not event.get("id"):
        import hashlib
        basis = "%s|%s|%s" % (event["op"], event["ts"],
                              json.dumps(event, sort_keys=True, ensure_ascii=False))
        event["id"] = "eid-" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:10]
    p = path(ws)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        # A prior torn line must not merge with this one.
        f.seek(0, os.SEEK_END)
        if f.tell() > 0:
            with open(p, "rb") as rf:
                rf.seek(-1, os.SEEK_END)
                if rf.read(1) != b"\n":
                    f.write("\n")
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return event


def read(ws):
    """Read every event. Returns (events, scars).

    A line that does not parse is skipped and reported as a scar — a read
    must never crash on a torn write, and must never hide that it saw one.
    Bytes, not text: a tear inside a multibyte character raises at the
    iterator under encoding="utf-8", above any try, and that once killed
    every reader. Non-ascii text is first-class here; its tears must scar
    like any other.
    """
    p = path(ws)
    events, scars = [], []
    if not os.path.exists(p):
        return events, scars
    with open(p, "rb") as f:
        for n, raw in enumerate(f, 1):
            try:
                line = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                scars.append("line %d is torn mid-character — skipped, kept on disk" % n)
                continue
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                scars.append("line %d unreadable (torn write?) — skipped, kept on disk" % n)
                continue
            if isinstance(e, dict) and e.get("op"):
                events.append(e)
            else:
                scars.append("line %d is not an event — skipped" % n)
    return events, scars
