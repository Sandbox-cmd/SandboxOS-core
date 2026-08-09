# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""status / resume / play / doctor — the workshop meeting its owner.

status is a pure render: nothing writes. resume is the arrivals beat: what
happened since you left, the pile behind your key, and the provisional acts
waiting for their confirm — one keystroke covers the batch; anything that
moved on is named "needs your hand," never auto-resolved. play opens the
free room: nothing in it touches the record, by construction. doctor names
what it finds, one line each, and fails honestly.
"""
import os
import sys

from . import desk, gate, journal, notes, project, provisional

PLAYGROUND = "playground"


def status(ws):
    lines = []
    projects = project.list_all(ws)
    on = project.on_list(ws)
    active = [p for p in projects if p["state"] == "active"]
    lines.append("%d project(s), %d active · on: %s" %
                 (len(projects), len(active), ", ".join(on) if on else "nothing"))
    for p in projects:
        mark = "*" if p["dir"] in on else " "
        lines.append(" %s %-20s %-8s %s" % (mark, p["dir"], p["state"], p["goal"]))
    pile, scars = desk.drafts(ws)
    if pile:
        lines.append("%d draft(s) waiting on your key — sandbox approve" % len(pile))
    waiting = provisional.pending(ws)
    if waiting:
        lines.append("%d provisional act(s) await your confirm, oldest %d day(s) — sandbox resume"
                     % (len(waiting), provisional.oldest_age_days(ws)))
    if scars:
        lines.append("%d unreadable staging line(s) — doctor has details" % len(scars))
    if not pile and not waiting:
        lines.append("nothing needs you.")
    return "\n".join(lines)


def resume(ws, is_real_tty=None, keychar=None):
    """Arrivals: the digest, then the one keystroke that lands the pile and
    confirms every clean provisional act. Headless shows and touches nothing."""
    out = []
    events, _ = journal.read(ws)
    recent = [e for e in events[-10:] if e.get("op") in ("ship", "make", "assert")]
    if recent:
        out.append("since you left:")
        for e in recent[-5:]:
            out.append("  %s %s" % (e.get("op"), (e.get("body") or "")[:70]))
    pile, _ = desk.drafts(ws)
    waiting = provisional.pending(ws)
    clean = [a for a in waiting if provisional.status_of(ws, a) == "clean"]
    moved = [a for a in waiting if provisional.status_of(ws, a) != "clean"]
    if not pile and not waiting:
        out.append("nothing waits. the page is quiet.")
        return "\n".join(out), 0

    out.append("%d draft(s) and %d provisional act(s) wait on one k." % (len(pile), len(clean)))
    for a in moved:
        out.append("  needs your hand: %s (%s) — the file moved on; revert or confirm it yourself"
                   % (a["why"], os.path.basename(a["path"])))

    consent = gate.mint_consent(is_real_tty=is_real_tty, keychar=keychar)
    if consent is None:
        out.append("approve at a real terminal: sandbox resume, then k")
        return "\n".join(out), 0
    n, msg = notes.approve(ws, is_real_tty=is_real_tty, keychar=keychar)
    confirmed = 0
    for a in clean:
        ok, _ = provisional.confirm(ws, a["id"], consent)
        confirmed += 1 if ok else 0
    out.append("landed %d draft(s), confirmed %d provisional act(s)." % (n, confirmed))
    return "\n".join(out), n + confirmed


def play(ws):
    """The free room. Uncounted and uncitable by construction: nothing under
    playground/ is read by canon, recall, or the record."""
    d = os.path.join(ws, PLAYGROUND)
    os.makedirs(d, exist_ok=True)
    charter = os.path.join(d, "CHARTER.md")
    if not os.path.exists(charter):
        with open(charter, "w", encoding="utf-8") as f:
            f.write("# the playground\n\nungated, uncounted, uncitable. "
                    "trying is free in here; nothing in this room ships by accident.\n")
    return "the playground is open: %s — nothing in there touches the record." % d


def doctor(ws):
    """Health, one honest line each. Returns (all_ok, lines)."""
    checks = []

    v = sys.version_info
    checks.append(("python >= 3.9", v >= (3, 9), "%d.%d" % (v[0], v[1])))

    import shutil
    checks.append(("git", shutil.which("git") is not None,
                   "" if shutil.which("git") else "not found — projects stand without history"))

    if os.path.exists(journal.path(ws)):
        events, scars = journal.read(ws)
        checks.append(("the record reads", True, "%d event(s)" % len(events)))
        checks.append(("no torn lines", not scars,
                       "; ".join(scars) if scars else ""))
    else:
        checks.append(("the record", False, "no workshop here yet — sandbox init"))

    bad = []
    for p in project.list_all(ws):
        if p["state"] not in ("active", "parked", "done"):
            bad.append("%s: state %r" % (p["dir"], p["state"]))
    checks.append(("project contracts parse", not bad, "; ".join(bad)))

    stale = provisional.oldest_age_days(ws)
    checks.append(("provisional lane fresh", stale <= 7,
                   "oldest act is %d day(s) old — resume and rule on it" % stale if stale > 7 else ""))

    from . import update
    s = update.skew(ws)
    checks.append(("core and workshop agree", s is None, s or ""))

    from . import placement
    div = placement.diverged(ws)
    checks.append(("placed files current", not div,
                   "updates are skipping your edited copies: %s — sandbox reset PATH re-baselines"
                   % ", ".join(os.path.basename(d) for d in div) if div else ""))

    from . import onboard
    drift = placement.unrecorded_drift(ws, onboard.shipped_payload(ws))
    checks.append(("kept files match what ships", not drift,
                   "never-recorded copies differ from this core: %s — restore on your word: sandbox reset NAME"
                   % ", ".join(os.path.basename(d) for d in drift) if drift else ""))

    from . import face
    lines = []
    for label, ok, note_ in checks:
        lines.append(" %-4s %-26s %s" % (face.mark(ok).strip(), label, note_))
    return all(ok for _, ok, _ in checks), lines
