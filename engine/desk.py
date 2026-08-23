# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the desk: the one landing strip for anything anyone asserts.

Everything stages (R3). Origin still says who typed it — a person or the
machine — and the key that lands it is a separate fact, read at approval
over a pile the person was shown. Two refusals happen here before anything
touches the record: a proposal carrying its own consent (tampering), and a
claim arriving with its ink already on (nothing marks itself checked —
law 1). Ink is computed at landing from what can actually be opened.

The landing carries `shown`: the sha256 of the block the person read, so a
year later the record says what else rode that one keypress. The scar it
answers is 07-28 — thirty-four lines landed on a key pressed over ten — and
its rule is here in `land_all`: a shown line lands while it still matches
the line on disk, and one that moved fails the whole pile closed.
"""
import hashlib
import json
import os

from . import gate, journal


def staging_path(ws):
    return os.path.join(ws, journal.STATE_DIR, "staging.jsonl")


def compute_ink(record):
    """ink at landing, from evidence — never from the writer's say-so.

    A receipt that exists and opens → receipted. No receipt → claimed.
    (`checked` is the third rung and it is not written here or anywhere:
    a green `sandbox check` mints an event naming what it proves, and the
    projection raises those lines when it reads them. A landed line is never
    rewritten, so this function says only what it can prove at landing.)
    """
    receipt = record.get("receipt")
    if receipt and os.path.exists(receipt):
        return "receipted"
    if receipt and str(receipt).startswith("journal:"):
        return "receipted"
    return "claimed"


def mint(ws, record, consent=None):
    """the code-minted path: a receipt an organ writes, never a claim.

    `save`, `use`, `share`, `fetch`, a project's own lifecycle — none of them
    asks the owner for a key, because none of them asserts anything: each
    reports a thing it just did and hands over the file that proves it. What
    they may not do is name their own rung or their own hand, so they come
    through here: one function computes the rung for the whole engine, and
    the hand is read off the consent that was minted at a terminal.
    """
    if "ink" in record:
        raise ValueError("mint: the rung is computed here, never handed in")
    for f in gate.CONSENT_FIELDS:
        if f in record:
            raise ValueError("mint: a record never carries its own consent")
    event = dict(record)
    event.setdefault("op", "assert")
    event["ink"] = compute_ink(record)
    if consent and consent.get("synthetic"):
        event["hand"] = "synthetic"
    return journal.append(ws, event)


def submit(ws, record):
    """submit one assertion. Returns (disposition, message).

    dispositions: staged | refused. Nothing lands from here: what lands is
    the pile a person was shown, on the key they pressed over it.
    """
    if not isinstance(record, dict) or not record.get("body"):
        return "refused", "a note needs words of its own"
    if "ink" in record:
        return "refused", "a claim never marks itself — the mark is computed at landing"
    for f in gate.CONSENT_FIELDS:
        if f in record:
            return "refused", "record carries its own consent ('%s') — refused as tampering" % f

    staged = dict(record)
    staged["origin"] = record.get("origin", "machine")
    # when the draft was written, kept so the landed line can say how long it
    # waited — the first link `recall --why` walks (record.md behavior 7).
    staged["staged_at"] = journal.now()
    with open(staging_path(ws), "a", encoding="utf-8") as f:
        f.write(json.dumps(staged, ensure_ascii=False) + "\n")
    return "staged", "waiting for your approval — approve it: sandbox approve"


def draft_hash(record):
    """the fingerprint of a draft's exact words, carried onto the line it
    becomes. It is what makes the walk from a landed fact back to the note
    that proposed it a match rather than a guess — the staging line is gone
    the moment the key lands it, and this survives it."""
    return hashlib.sha256((record.get("body") or "").encode("utf-8")).hexdigest()


def row(record):
    """one waiting line, as a person reads it before the key."""
    return "[%s] %s" % (record.get("cls", "note"), record.get("body") or "")


def drafts(ws):
    """read what waits. A torn staging line is reported, never fatal."""
    p = staging_path(ws)
    out, scars = [], []
    if not os.path.exists(p):
        return out, scars
    with open(p, "rb") as f:
        for n, raw in enumerate(f, 1):
            try:
                line = raw.decode("utf-8").strip()
                if line:
                    out.append(json.loads(line))
            except (UnicodeDecodeError, ValueError):
                scars.append("staging line %d unreadable — skipped, kept on disk" % n)
    return out, scars


def drop(ws, n):
    """retract the Nth waiting draft (as `drafts` numbers them) — the exit
    for an accidental staging. The dropped body is said in full, so the
    retraction happens in the open; torn lines stay on disk untouched."""
    p = staging_path(ws)
    raws = []
    if os.path.exists(p):
        with open(p, "rb") as f:
            raws = [r for r in f.readlines() if r.strip()]
    parseable = []
    for i, raw in enumerate(raws):
        try:
            record = json.loads(raw.decode("utf-8"))
            parseable.append((i, record))
        except (UnicodeDecodeError, ValueError):
            continue
    if not 1 <= n <= len(parseable):
        return False, "nothing at %d — %d draft(s) wait. see them: sandbox drafts" % (n, len(parseable))
    idx, record = parseable[n - 1]
    del raws[idx]
    if raws:
        with open(p, "wb") as f:
            f.writelines(raws)
    else:
        os.remove(p)
    return True, "dropped, in the open: [%s] %s" % (record.get("cls", "note"),
                                                    record.get("body") or "")


def land_all(ws, consent, shown=None):
    """the owner's keystroke lands what it was shown. Headless lands nothing.

    `shown` is the exact records that were printed before the key: each one
    lands only while the line on disk still matches it, a line that arrived
    while the person was reading stays where it is, and a shown line that
    moved fails the whole pile closed. None lands the pile as it stands.
    """
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        return 0, "landing needs your %r at a real terminal" % gate.COMMIT_KEY
    p = staging_path(ws)
    raws = []
    if os.path.exists(p):
        with open(p, "rb") as f:
            raws = [r for r in f.readlines() if r.strip()]
    parsed = {}
    for i, raw in enumerate(raws):
        try:
            parsed[i] = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            continue
    if shown is None:
        take = sorted(parsed)
    else:
        take = []
        for record in shown:
            hit = next((i for i in sorted(parsed)
                        if i not in take and parsed[i] == record), None)
            if hit is None:
                # surface: 3b
                return None, ("staging moved under you — nothing landed. "
                              "see it again: sandbox drafts")
            take.append(hit)
    landed = 0
    for i in sorted(take):
        event = dict(parsed[i])
        # a draft says its own op only when it is one of the record's other
        # kinds (an invalidate stages like everything else, R3); the pen's
        # default stays `assert`.
        event["op"] = parsed[i].get("op", "assert")
        event["ink"] = compute_ink(parsed[i])
        event["from_draft"] = draft_hash(parsed[i])
        if consent.get("shown"):
            event["shown"] = consent["shown"]
        if consent.get("synthetic"):
            event["hand"] = "synthetic"
        journal.append(ws, event)
        landed += 1
    left = [raw for i, raw in enumerate(raws) if i not in set(take)]
    if left:
        with open(p, "wb") as f:
            f.writelines(left)
    elif os.path.exists(p):
        os.remove(p)
    # surface: 2
    msg = "landed %d" % landed
    torn = len(raws) - len(parsed)
    if torn:
        msg += " · %d unreadable line(s) kept on disk" % torn
    return landed, msg
