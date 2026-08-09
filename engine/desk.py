# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The desk: the one landing strip for anything the machine asserts.

Routes by origin (law 11): a machine-origin assertion STAGES and waits; a
human-origin record at a real terminal goes through the gate and lands.
Two refusals happen here before anything touches the record: a proposal
carrying its own consent (tampering), and a claim arriving with its ink
already on (nothing marks itself checked — law 1). Ink is computed at
landing from what can actually be opened.
"""
import json
import os

from . import gate, journal


def staging_path(ws):
    return os.path.join(ws, journal.STATE_DIR, "staging.jsonl")


def compute_ink(record):
    """Ink at landing, from evidence — never from the writer's say-so.

    A receipt that exists and opens → receipted. No receipt → claimed.
    (`checked` — a receipt whose content re-verifies the claim — arrives
    with the check-running machinery; this function says only what it can
    honestly prove today.)
    """
    receipt = record.get("receipt")
    if receipt and os.path.exists(receipt):
        return "receipted"
    if receipt and str(receipt).startswith("journal:"):
        return "receipted"
    return "claimed"


def submit(ws, record, consent=None):
    """Submit one assertion. Returns (disposition, message).

    dispositions: staged | landed | refused
    """
    if not isinstance(record, dict) or not record.get("body"):
        return "refused", "an assertion needs a body"
    if "ink" in record:
        return "refused", "a claim never marks its own ink — computed at landing"
    for f in gate.CONSENT_FIELDS:
        if f in record:
            return "refused", "record carries its own consent ('%s') — refused as tampering" % f

    origin = record.get("origin", "machine")
    if origin != "human":
        entry = dict(record)
        entry["origin"] = origin
        with open(staging_path(ws), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return "staged", "waiting for your approval — approve it: sandbox approve"

    verdict, why = gate.decide(record, consent)
    if verdict == "REFUSE":
        return "refused", why
    event = dict(record)
    event["op"] = "assert"
    event["origin"] = "human"
    event["ink"] = compute_ink(record)
    if consent and consent.get("synthetic"):
        event["hand"] = "synthetic"
    journal.append(ws, event)
    return "landed", "landed with your key"


def drafts(ws):
    """Read what waits. A torn staging line is reported, never fatal."""
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
    """Retract the Nth waiting draft (as `drafts` numbers them) — the exit
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


def land_all(ws, consent):
    """The owner's keystroke lands the pile. Headless lands nothing.

    Each draft becomes a journal event with computed ink and its origin
    preserved; the staging file empties only after every line landed.
    """
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        return 0, "landing needs your %r at a real terminal" % gate.COMMIT_KEY
    pile, scars = drafts(ws)
    landed = 0
    for d in pile:
        event = dict(d)
        event["op"] = "assert"
        event["ink"] = compute_ink(d)
        if consent.get("synthetic"):
            event["hand"] = "synthetic"
        journal.append(ws, event)
        landed += 1
    if landed:
        os.remove(staging_path(ws))
    msg = "landed %d" % landed
    if scars:
        msg += " · %d unreadable line(s) kept on disk" % len(scars)
    return landed, msg
