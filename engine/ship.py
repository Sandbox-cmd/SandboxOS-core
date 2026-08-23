# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""ship: celebration only on a real check, and only on checks you were shown.

The checks in PROJECT.md run where the work lives. Their lines are printed
and fingerprinted on every run (R17), and that text is what the owner's key
lands on: change a check and the k is read again, leave it alone and the
ship needs no ceremony at all (R10). Two fences hold before any of it: a
project with nothing under `## checks` ships nothing, and unconfirmed
provisional acts hold the ship back until they are ruled on.

A green ship mints the same `check` event a bare `sandbox check` mints, so
the proof a celebration rests on raises the same lines the quiet run does.
"""
import hashlib
import json
import os
import shutil
import subprocess

from . import gate, journal, project, provisional

TIMEOUT = 120

# the longest a line can be and still read as a command rather than a
# sentence — the shape `stray_check` uses to name a check parked under the
# wrong heading, where the contract reader never sees it.
MAX_CHECK_WORDS = 12


def _ratified_path(ws):
    return os.path.join(ws, journal.STATE_DIR, "ratified.json")


def checks_hash(checks):
    return hashlib.sha256("\n".join(checks).encode("utf-8")).hexdigest()


def _ratified(ws):
    p = _ratified_path(ws)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def looks_runnable(line):
    """whether a line reads as a command this machine could run.

    The test is the machine's own: the first word resolves to something on
    the path, or it is a path itself. Prose that happens to open with a
    command name is caught by the two shapes prose has and a check does not —
    a closing period, and length.
    """
    line = line.strip()
    if not line or line[0] in "#|-*>":
        return False
    if line.endswith((".", "!", "?", ":")):
        return False
    words = line.split()
    if len(words) > MAX_CHECK_WORDS:
        return False
    first = words[0]
    if first.startswith(("./", "/", "../")):
        return True
    return shutil.which(first) is not None


def stray_check(path):
    """a runnable line sitting under some other heading, or None."""
    if not os.path.exists(path):
        return None
    section = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("## "):
                section = line[3:].strip().lower()
            elif section and section != "checks" and looks_runnable(line):
                return section, line.strip()
    return None


def ratify(ws, name, consent, digest=""):
    """the owner's key on this exact checks text. Headless ratifies nothing."""
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        # surface: 3b
        return False, ("ratifying checks needs your %r at a real terminal — "
                       "run: sandbox ship %s" % (gate.COMMIT_KEY, name))
    c = project.parse_contract(project.contract_path(ws, name))
    if c is None:
        # surface: 3a
        return False, "no project named %s" % name
    if not c["checks"]:
        # the same sentence `ship` refuses with below, because it is the same
        # refusal — `ship` reaches this guard only after its own, so a second
        # wording here was a twin nobody could ever read (9.0.1).
        # surface: 3a
        return False, ("a ship with no checks is a costume — add a line "
                       "under PROJECT.md's ## checks")
    r = _ratified(ws)
    r[name] = checks_hash(c["checks"])
    with open(_ratified_path(ws), "w", encoding="utf-8") as f:
        json.dump(r, f)
    event = {"op": "ratify", "project": name, "origin": "human",
             "body": "checks ratified (%d line(s))" % len(c["checks"]),
             "hash": r[name]}
    if consent.get("shown"):
        event["shown"] = consent["shown"]
    if consent.get("synthetic"):
        event["hand"] = "synthetic"
    journal.append(ws, event)
    # surface: 28
    return True, "ratified — your k is on these exact checks (%s)" % digest[:8]


def run_checks(ws, name):
    """run every check where the work lives. Returns (all_green, results)."""
    c = project.parse_contract(project.contract_path(ws, name))
    if c is None:
        return False, [("", "no project named %s" % name, 1)]
    root = project.root_of(ws, name)
    results = []
    for line in c["checks"]:
        try:
            r = subprocess.run(line, shell=True, cwd=root, capture_output=True,
                               text=True, timeout=TIMEOUT)
            results.append((line, (r.stdout + r.stderr).strip()[-500:], r.returncode))
        except subprocess.TimeoutExpired:
            results.append((line, "timed out after %ds" % TIMEOUT, 124))
    return all(rc == 0 for _, _, rc in results), results


def closes_since_ship(ws):
    """per project, the closes that landed after its last ship.

    The count the nags are made of: a close is a piece of work wrapped, and
    a ship is the last one put on the record. Projects with none are left
    out, so a caller renders a row only where there is something to do.
    """
    events, _ = journal.read(ws)
    counts = {}
    for e in events:
        name = e.get("project")
        if not name:
            continue
        if e.get("op") == "ship":
            counts[name] = 0
        elif e.get("op") == "make" and e.get("phase") == "close":
            counts[name] = counts.get(name, 0) + 1
    return [(name, n) for name, n in sorted(counts.items()) if n]


def ship(ws, name, out=print):
    """the loop's last leg: what it will run, then the key, then the run.

    The lines and their fingerprint print on every run (R17) and the key is
    read only when that text moved since the last ratification (R10) — so a
    person always sees the exact checks their name is on, and pays for the
    ceremony once.
    """
    c = project.parse_contract(project.contract_path(ws, name))
    if c is None:
        # surface: 3a
        return False, "no project named %s" % name
    if not c["checks"]:
        stray = stray_check(project.contract_path(ws, name))
        if stray:
            # surface: 3a
            return False, ("a line under ## %s looks like a check — move it "
                           "under ## checks" % stray[0])
        # surface: 3a
        return False, ("a ship with no checks is a costume — add a line "
                       "under PROJECT.md's ## checks")

    count, digest = gate.show(c["checks"], out)

    waiting = provisional.pending(ws, name)
    if waiting:
        # surface: 3b
        return False, ("%d provisional act(s) on %s await your confirm — "
                       "a ship never rides over unconfirmed work. sandbox resume first"
                       % (len(waiting), name))

    h = checks_hash(c["checks"])
    by_hand = _ratified(ws).get(name) != h
    if by_hand:
        if not gate.at_a_terminal():
            # surface: 3b
            return False, "ratifying checks needs your 'k' at a real terminal — run: sandbox ship %s" % name
        gate.ask(count, out)
        consent = gate.mint_consent(shown=digest)
        if consent is None:
            # surface: 2
            return False, "cancelled — nothing shipped"
        ok, msg = ratify(ws, name, consent, digest)
        if not ok:
            return False, msg
        out(msg)

    green, results = run_checks(ws, name)
    if not green:
        red = [(line, said) for line, said, rc in results if rc != 0]
        # surface: 30
        return False, ("\n".join("FAIL %s\n     %s" % (line, said or "(no output)")
                                 for line, said in red)
                       + "\nthe checks are red — no ship")

    from . import check
    check.mint(ws, name, c["checks"], len(results))
    event = {"op": "ship", "project": name, "origin": "machine",
             "triggered": "owner" if by_hand else "session",
             "body": "shipped against %d green check(s)" % len(results),
             "hash": h}
    e = journal.append(ws, event)
    # surface: 2
    return True, "shipped — %d check(s) green, on the record (journal:%s)" % (len(results), e["id"])
