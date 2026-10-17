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
import re
import shutil
import signal
import subprocess
import time

from . import gate, journal, project, provisional

TIMEOUT = 120

# a slow honest check names its own limit at the end of its line, as a shell
# comment (`node --test slow.mjs # timeout 300s`): the shell ignores it, and
# because it sits in the line it sits in the fingerprint the key reads.
LINE_TIMEOUT = re.compile(r"\s#\s*timeout\s+([0-9]{1,5})s?\s*$")
MAX_TIMEOUT = 3600

# a line that looks like it names a limit and does not parse is red, so a
# limit the key read is never silently a different one.
LOOKS_LIKE_A_LIMIT = re.compile(r"\s#\s*timeout\b", re.IGNORECASE)
# surface: 3a
UNREAD_LIMIT = "a line's time limit needs this shape, 1 to 3600: # timeout 300s"

# how the stop reads the process table; without it the stop still reaches
# the line's own group.
PS = ["ps", "-A", "-o", "pid=,ppid=,pgid=,stat="]

# seconds a stopped line's processes get to end on SIGTERM before what is
# still standing is killed outright.
KILL_GRACE = 5

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


def line_timeout(line):
    """the seconds a check line may run: its own `# timeout Ns`, or the default."""
    m = LINE_TIMEOUT.search(line)
    return int(m.group(1)) if m else TIMEOUT


def limit_reads(line):
    """whether a line's limit reads. a line that looks like it names one reads
    only in the right shape with a number from 1 to MAX_TIMEOUT."""
    if not LOOKS_LIKE_A_LIMIT.search(line):
        return True
    m = LINE_TIMEOUT.search(line)
    return bool(m) and 1 <= int(m.group(1)) <= MAX_TIMEOUT


def _processes():
    """every live process as {pid: (ppid, pgid)}, read off `ps`; empty when
    `ps` will not run, and the stop then reaches the line's own group."""
    try:
        r = subprocess.run(PS, capture_output=True, text=True)
    except OSError:
        return {}
    table = {}
    for row in r.stdout.splitlines():
        parts = row.split()
        if len(parts) == 4 and not parts[3].startswith("Z"):
            table[int(parts[0])] = (int(parts[1]), int(parts[2]))
    return table


def _descendants(pid):
    """every process below `pid`, as {pid: pgid}. A child that started its own
    session (node's `detached: true`, a daemon) leaves the line's group but
    keeps its parent link while its parent lives, so the walk still finds it."""
    table = _processes()
    below, todo = {}, [pid]
    while todo:
        parent = todo.pop()
        for child, (ppid, pgid) in table.items():
            if ppid == parent and child not in below:
                below[child] = pgid
                todo.append(child)
    return below


def _still_standing(found):
    """the ones in `found` that live on in the group they were found in, so a
    pid the system hands out again is never signalled."""
    table = _processes()
    return {pid: pgid for pid, pgid in found.items()
            if pid in table and table[pid][1] == pgid}


def _answering(groups):
    """the groups that still have a member, whether or not the walk found it:
    a process whose launcher exited keeps the group and loses its parent."""
    alive = set()
    for g in groups:
        try:
            os.killpg(g, 0)
            alive.add(g)
        except (ProcessLookupError, PermissionError):
            pass
    return alive


def _signal(groups, pids, sig):
    for kill, target in [(os.killpg, g) for g in groups] + [(os.kill, p) for p in pids]:
        try:
            kill(target, sig)
        except (ProcessLookupError, PermissionError):
            pass


class _SignalsWait:
    """while a line is being stopped, ctrl-c and the stop signals wait their
    turn, so a second press cannot cut the stop short before SIGKILL. The
    first one that arrived is raised again once the stop is done, through
    the handler that was in place. An ignored signal stays ignored, and one
    whose handler was set outside python is left as it is."""
    SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)

    def __enter__(self):
        self.saved, self.arrived = {}, []
        for sig in self.SIGNALS:
            try:
                if signal.getsignal(sig) in (signal.SIG_IGN, None):
                    continue
                self.saved[sig] = signal.signal(
                    sig, lambda n, frame: self.arrived.append(n))
            except ValueError:
                break
        return self

    def __exit__(self, *exc):
        for sig, handler in self.saved.items():
            signal.signal(sig, handler)
        if self.arrived:
            signal.raise_signal(self.arrived[0])
        return False


def _stop(p):
    """stop a check line and everything it started: SIGTERM to the line's
    group, every group a descendant moved into and each descendant, then
    SIGKILL to every one of them still standing after KILL_GRACE.

    killing only the shell once left a dev server running on its port, and
    every later run of that check hung. The walk is taken before the first
    signal, because a child whose parent dies loses its link to the line.
    """
    with _SignalsWait():
        own = os.getpgrp()
        found = _descendants(p.pid)
        groups = ({p.pid} | set(found.values())) - {own}
        _signal(groups, found, signal.SIGTERM)
        deadline = time.monotonic() + KILL_GRACE
        while time.monotonic() < deadline:
            if (p.poll() is not None and not _still_standing(found)
                    and not _answering(groups)):
                return
            time.sleep(0.05)
        standing = _still_standing(found)
        _signal(_answering(groups) | (set(standing.values()) - {own}),
                standing, signal.SIGKILL)
        try:
            p.wait(timeout=KILL_GRACE)
        except subprocess.TimeoutExpired:
            pass


def _run_line(line, root, limit):
    """run one check line in its own session. Returns (output, code), or
    (None, 124) when it ran out of time. When the tool stops a line (its
    limit, ctrl-c, a stop signal to sandbox) it stops what the line started."""
    with subprocess.Popen(line, shell=True, cwd=root, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True,
                          start_new_session=True) as p:
        try:
            out, err = p.communicate(timeout=limit)
            return out + err, p.returncode
        except subprocess.TimeoutExpired:
            _stop(p)
        except BaseException:
            _stop(p)
            raise
    return None, 124


class _StopSignalsRaise:
    """while the checks run, SIGTERM and SIGHUP (a closed terminal) raise
    SystemExit, so the running line is stopped on the way out; the handlers
    in place before are put back after. Ctrl-C raises KeyboardInterrupt
    already. An ignored signal stays ignored (`nohup sandbox check`). Off the
    main thread nothing changes, because python allows handlers only there."""
    SIGNALS = (signal.SIGTERM, signal.SIGHUP)

    def __enter__(self):
        self.saved = {}
        for sig in self.SIGNALS:
            try:
                if signal.getsignal(sig) in (signal.SIG_IGN, None):
                    continue
                self.saved[sig] = signal.signal(sig, self._raise)
            except ValueError:
                break
        return self

    def __exit__(self, *exc):
        for sig, handler in self.saved.items():
            signal.signal(sig, handler)
        return False

    @staticmethod
    def _raise(signum, frame):
        raise SystemExit(128 + signum)


def run_checks(ws, name):
    """run every check where the work lives. Returns (all_green, results)."""
    c = project.parse_contract(project.contract_path(ws, name))
    if c is None:
        return False, [("", "no project named %s" % name, 1)]
    root = project.root_of(ws, name)
    results = []
    with _StopSignalsRaise():
        for line in c["checks"]:
            if not limit_reads(line):
                results.append((line, UNREAD_LIMIT, 2))
                continue
            limit = line_timeout(line)
            output, code = _run_line(line, root, limit)
            if output is None:
                results.append((line, "timed out after %ds" % limit, 124))
            else:
                results.append((line, output.strip()[-500:], code))
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
