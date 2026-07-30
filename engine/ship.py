# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Ship: celebration only on a real check.

The checks in PROJECT.md run where the work lives; their raw text is hashed,
and that hash is what the owner ratifies — change a check and the k is asked
again. A ship against already-ratified, green checks may mint headless and
says `triggered: session` on its face. Two fences hold: red checks refuse,
and unconfirmed provisional acts refuse (challenge #4 — provisional content
never rides into a ratified ship).
"""
import hashlib
import json
import os
import subprocess

from . import gate, journal, project, provisional

TIMEOUT = 120


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


def ratify(ws, name, consent):
    """The owner's key on this exact checks text. Headless ratifies nothing."""
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        return False, "ratifying checks needs your %r at a real terminal" % gate.COMMIT_KEY
    c = project.parse_contract(project.contract_path(ws, name))
    if c is None:
        return False, "no project named %s" % name
    if not c["checks"]:
        return False, "no checks to ratify — a ship with nothing under it is a costume"
    r = _ratified(ws)
    r[name] = checks_hash(c["checks"])
    with open(_ratified_path(ws), "w", encoding="utf-8") as f:
        json.dump(r, f)
    event = {"op": "ratify", "project": name, "origin": "human",
             "body": "checks ratified (%d line(s))" % len(c["checks"]),
             "hash": r[name]}
    if consent.get("synthetic"):
        event["hand"] = "synthetic"
    journal.append(ws, event)
    return True, "ratified — your name is on these checks"


def run_checks(ws, name):
    """Run every check where the work lives. Returns (all_green, results)."""
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


def ship(ws, name, consent=None):
    """The loop's last leg. Fences first, checks second, honesty always."""
    c = project.parse_contract(project.contract_path(ws, name))
    if c is None:
        return False, "no project named %s" % name
    if not c["checks"]:
        return False, "nothing to ship on — PROJECT.md has no checks"

    waiting = provisional.pending(ws, name)
    if waiting:
        return False, ("%d provisional act(s) on %s await your confirm — "
                       "a ship never rides over unconfirmed work. sandbox resume first"
                       % (len(waiting), name))

    h = checks_hash(c["checks"])
    ratified = _ratified(ws).get(name)
    if ratified != h:
        ok, msg = ratify(ws, name, consent)
        if not ok:
            return False, ("these checks are new or changed since your last k — " + msg)

    green, results = run_checks(ws, name)
    if not green:
        red = [(line, out) for line, out, rc in results if rc != 0]
        return False, "the checks are red — no ship:\n" + "\n".join(
            "  FAIL %s\n    %s" % (line, out or "(no output)") for line, out in red)

    event = {"op": "ship", "project": name, "origin": "machine",
             "triggered": "session" if not consent else "owner",
             "body": "shipped against %d green check(s)" % len(results),
             "hash": h}
    e = journal.append(ws, event)
    return True, "shipped — %d check(s) green, on the record (journal:%s)" % (len(results), e["id"])
