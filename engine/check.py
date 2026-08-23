# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""check: run what the project rests on, and let the record say so.

The same lines a ship runs, run without the ship: no ratification, no
celebration, no key. What a green run leaves behind is one event naming the
lines it proved, and from then on those lines read `checked` wherever the
record is read — raised at the projection, never written onto a landed line
(law 1, law 2). That is the whole of the third rung: it is reached by a run
and by nothing a writer can say about itself.

The runner is `ship.run_checks` — imported, not copied, so a check and a
ship can never disagree about what the project's own lines do.
"""
from . import journal, project, ship


def proves(ws, name, events=None):
    """the lines a green run would raise.

    Every claim landed on this project since the last green run — or, when
    there has never been one, since the project's first make opened, because
    that is the moment the work under these checks began. A line older than
    the window was proved by an earlier run or by nothing; either way this
    run did not prove it.

    A claim is what a run can raise: a line that rests on nothing yet. A
    receipt already rests on a file that opens, and a ruling is a decision
    rather than a thing a command can be right or wrong about — neither is
    this verb's business.
    """
    if events is None:
        events, _ = journal.read(ws)
    start = 0
    for i, e in enumerate(events):
        if e.get("op") == "check" and e.get("project") == name and e.get("green"):
            start = i + 1
    if start == 0:
        for i, e in enumerate(events):
            if (e.get("op") == "make" and e.get("phase") == "open"
                    and e.get("project") == name):
                start = i
                break
    return [e["id"] for e in events[start:]
            if e.get("op") == "assert" and e.get("project") == name
            and e.get("cls", "note") != "ruling"
            and e.get("ink") == "claimed" and e.get("id")]


def rows(results):
    """one line per check, the way a person reads a run: the mark, then the
    command exactly as it is written in the contract."""
    out = []
    for line, said, rc in results:
        out.append("%s %s" % ("ok  " if rc == 0 else "FAIL", line))
        if rc != 0:
            out.append("     %s" % (said or "(no output)"))
    return out


def run_checks(ws, name):
    """the runner, reachable from this side too: one implementation, three
    callers — this verb, the close, and the ship."""
    return ship.run_checks(ws, name)


def mint(ws, name, checks, green_count):
    """the event a green run leaves: the hash it ran, and what it raises.

    A ship mints one of these as well, so a celebration and a bare run leave
    the record in the same shape and the projection has one rule to read.
    Returns (event, the ids it raised).
    """
    events, _ = journal.read(ws)
    raised = proves(ws, name, events)
    e = journal.append(ws, {
        "op": "check", "project": name, "origin": "machine",
        "triggered": "session", "body": "%d check(s) green" % green_count,
        "hash": ship.checks_hash(checks),
        "green": green_count, "proves": raised})
    return e, raised


def run(ws, name):
    """run a project's checks. Returns (green, message).

    Nothing ships here and nothing is ratified: the owner's key belongs to
    `ship`, and this verb exists so a person can find out where they stand
    without spending it.
    """
    c = project.parse_contract(project.contract_path(ws, name))
    if c is None:
        return False, "no project named %s" % name
    if not c["checks"]:
        # surface: 3a
        return False, ("nothing under ## checks in PROJECT.md — "
                       "put one command per line there")
    green, results = ship.run_checks(ws, name)
    lines = rows(results)
    if not green:
        red = len([1 for _, _, rc in results if rc != 0])
        # surface: 30
        lines.append("%d red on %s — fix them, then: sandbox check %s"
                     % (red, name, name))
        return False, "\n".join(lines)
    e, raised = mint(ws, name, c["checks"], len(results))
    # surface: 2
    lines.append("%d check(s) green on %s — %d claim(s) now read [checked] "
                 "(journal:%s)" % (len(results), name, len(raised), e["id"]))
    return True, "\n".join(lines)
