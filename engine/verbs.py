# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""verbs as declared action types (law 11 made structural).

Every verb is one function plus one DECLARATION: what it reads, the only
scopes it may write, which gate speed it needs, and the event it emits.
Declarations bind ENGINE CODE and are lint-enforced; the model's own session
writes are bound by the guard's standing fences instead — two regimes,
neither claiming the other's coverage (spec §2).

The same table serves every surface: the CLI dispatches through it, and the
agent tool-surface is generated from it — no surface re-implements a verb.
"""
import os

from . import registry

# The record's op set: eleven names, nine inherited and two born with this
# body. `check` is the only op that raises a claim's rung, and it raises it
# at the read; `export` is the second, and it stamps the receipt a person
# carries off the machine.
# `halt` is reserved and unminted — the seventh body's rows still use it, so
# the name stays and test_declarations counts it as parked.
OPS = ("genesis", "session", "assert", "invalidate", "make",
       "ratify", "ship", "halt", "place", "check", "export")

GATES = ("none", "provisional", "keystroke", "tty-keystroke")

# Write scopes are symbolic here and resolved against a live workshop by the
# code that enforces them. "state" is the record's own directory — only the
# desk-family verbs may name it.
SCOPES = ("state", "project", "workshop", "core", "shelf", "apps", "settings")


def declaration(reads=(), writes=(), gate="none", emits=None, blurb=""):
    """one verb's whole self-report. `blurb` is what it does, in words — the
    one field a person reads before they type: help renders it, the MANUAL
    renders it, `sandbox VERB --help` renders it. It is a sentence fragment,
    so it starts lowercase and ends without a period, and it fits a terminal
    row beside nothing else, so twelve words is the whole budget."""
    assert gate in GATES, gate
    assert emits is None or emits in OPS, emits
    for w in writes:
        assert w in SCOPES, w
    assert blurb, "a verb ships with a blurb or it ships nameless"
    assert blurb[0].islower(), blurb
    assert not blurb.endswith("."), blurb
    assert len(blurb.split()) <= 12, blurb
    return {"reads": tuple(reads), "writes": tuple(writes),
            "gate": gate, "emits": emits, "blurb": blurb}


# --- helpers ------------------------------------------------------------

def _flag(argv, name):
    """pop --name VALUE from argv. Returns (value, rest)."""
    argv = list(argv)
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1] if i + 1 < len(argv) else None
        return val, argv[:i] + argv[i + 2:]
    return None, argv


# Every verb's flags, at the one door — a verb that treats an unknown
# --flag as content is the bug (note --help once staged a draft whose whole
# body was the flag). Values are the placeholder the refusal shows; None
# means the flag stands alone.
FLAGS = {
    "note": {"--project": "NAME", "--workshop": None, "--ruling": None,
             "--supersedes": "eid-…"},
    "project": {"--root": "DIR", "--for": "PATH"},
    "drafts": {"--drop": "N"},
    "approve": {"--project": "NAME"},
    "recall": {"--project": "NAME", "--why": None, "--ruling": None,
               "--shown": "3f9a1c4e"},
    "make": {"--project": "NAME", "--open": '"intent"',
             "--close": None, "--summary": '"..."'},
    "ship": {"--project": "NAME"},
    "check": {"--project": "NAME"},
    "session": {"--key": "K", "--project": "NAME", "--agents": "name=N,…"},
    "use": {"--project": "NAME"},
    "save": {"--note": '"..."'},
    "share": {"--to": "DIR", "--sign": None},
    "fetch": {"--from": "DIR", "--expect-key": "K"},
    "app": {"--catalog": "DIR"},
    "import": {"--projects": "a,b,c"},
    "export": {"--redact": None, "--project": "NAME", "--since": "2026-08-01",
               "--to": "DIR", "--html": None, "--portable": None},
    # page is export --html, so it takes export's flags and never the two
    # that pick a form — it has already picked one.
    "page": {"--redact": None, "--project": "NAME", "--since": "2026-08-01",
             "--to": "DIR"},
    "release": {"--hook": None, "--is-release-commit": "FILE"},
    "status": {"--line": None},
    "canon": {"--project": "NAME", "--memory": None},
    # the projections are named once, in registry; a second hand-typed list
    # here is how the flag came to advertise a `marketplace` rebuild that
    # never existed.
    "update": {"--rebuild": "|".join(registry.PROJECTIONS)},
}


def _unknown_flags(argv, spec):
    """tokens that look like flags and are not this verb's. A known flag's
    value is skipped, so a value that happens to start with -- passes."""
    unknown, i = [], 0
    while i < len(argv):
        t = argv[i]
        if t in spec:
            i += 2 if spec[t] is not None else 1
            continue
        if t.startswith("--"):
            unknown.append(t)
        i += 1
    return unknown


def _flags_refusal(verb, flag, spec):
    if not spec:
        return "%s doesn't know %s — it takes no flags." % (verb, flag)
    shown = [k + (" " + v if v else "") for k, v in spec.items()]
    listed = shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " and " + shown[-1]
    return "%s doesn't know %s — its flags are %s." % (verb, flag, listed)


def _target(ws, argv):
    """the project a bare verb lands on. Returns (name, rest, refusal).

    --project NAME wins; else the project you are standing in; else the one
    that is on. Two on and nowhere to stand is ambiguous, and the refusal
    names the candidates rather than picking for you.
    """
    from . import project
    name, rest = _flag(argv, "--project")
    if name:
        return name, rest, None
    here = project.standing_in(ws)
    if here:
        return here, rest, None
    on = project.on_list(ws)
    if len(on) == 1:
        return on[0], rest, None
    if len(on) > 1:
        return None, rest, ("which project? you are standing in none, and %d "
                            "are on: %s — say: --project NAME"
                            % (len(on), ", ".join(sorted(on))))
    return None, rest, None


# --- the verbs. Each band adds its rows here, never elsewhere. -----------

def _version(ws, argv):
    from .cli import version_line, home_line
    print(version_line())
    print(home_line())
    return 0


def _plugin_dir(ws, argv):
    """where the plugin lives, printed — a convenience, and nothing more.

    Nothing calls it to wire anything: the marketplace this core registers is
    a `directory` source at this tree's root, and the plugin entry inside it
    is a relative path, so the host follows the tree with no command to run
    (R14's intent; its `command` wording is superseded). Reads one constant
    and writes nothing.
    """
    from . import vessel
    print(vessel.PLUGIN)
    return 0


def _help(ws, argv):
    """the index: two lines per verb — what it does, then what it costs and
    what it touches. One line could not hold both and stay inside a terminal
    row, and the row that got cut was always the one a person came for."""
    from .cli import version_line
    from .selfmap import GATE_WORDS, scope_words
    print(version_line())
    print("a maker's operating system for your own machine.")
    print()
    for name in sorted(TABLE):
        d = DECLARATIONS[name]
        print("  %-10s %s" % (name, d["blurb"]))
        print("             %s · %s" % (GATE_WORDS[d["gate"]], scope_words(d["writes"])))
    print()
    print("docs/MANUAL.md carries the full page per verb.")
    print("any verb answers --help.")
    return 0


def _project(ws, argv):
    from . import project
    if not argv:
        for p in project.list_all(ws):
            print("%-20s %-8s %s" % (p["dir"], p["state"], p["goal"]))
        return 0
    root, argv = _flag(argv, "--root")
    where, argv = _flag(argv, "--for")
    if argv[:1] == ["now"]:
        # the page a session starts from; the session-start hook asks with
        # --for, because it runs from the workshop and not where you stand.
        brief = project.now_brief(ws, name=(argv[1:] or [None])[0],
                                  path=where or os.getcwd())
        if brief:
            print(brief)
        return 0
    if not argv:
        print("project new NAME [goal] [--root DIR] · on|off NAME · "
              "done NAME · now [NAME]")
        return 2
    sub, rest = argv[0], argv[1:]
    if sub == "new" and rest:
        ok, msg = project.new(ws, rest[0], " ".join(rest[1:]), root=root)
    elif sub in ("on", "off") and rest:
        ok, msg = project.switch(ws, rest[0], sub == "on")
    elif sub == "done" and rest:
        ok, msg = project.done(ws, rest[0])
    else:
        print("project new NAME [goal] [--root DIR] · on|off NAME · "
              "done NAME · now [NAME]")
        return 2
    print(msg)
    return 0 if ok else 1


def _note(ws, argv):
    from . import notes
    # --ruling is the same pen with a stratum on it. There is no --law: an
    # amendment to what binds is its own sitting, never a flag (law 14).
    ruling = "--ruling" in argv
    argv = [a for a in argv if a != "--ruling"]
    supersedes, argv = _flag(argv, "--supersedes")
    if "--workshop" in argv:
        # said out loud, so the target rule never has to guess
        target, rest = None, _flag([a for a in argv if a != "--workshop"],
                                   "--project")[1]
    else:
        target, rest, refusal = _target(ws, argv)
        if refusal:
            print(refusal)
            return 2
    if not rest:
        print("note needs words: sandbox note \"what you found\"")
        return 2
    if supersedes and not ruling:
        print("--supersedes belongs to a ruling: add --ruling, or drop it")
        return 2
    disp, msg = notes.note(ws, " ".join(rest), target_project=target,
                           stratum="taste" if ruling else None,
                           supersedes=supersedes)
    print(msg)
    return 0


def _drafts(ws, argv):
    from . import desk
    drop, rest = _flag(argv, "--drop")
    if drop is not None:
        try:
            n = int(drop)
        except ValueError:
            print("drop needs the draft's number: sandbox drafts --drop N")
            return 2
        ok, msg = desk.drop(ws, n)
        print(msg)
        return 0 if ok else 1
    pile, scars = desk.drafts(ws)
    if not pile and not scars:
        print("i found nothing waiting — no notes need your approval.")
        return 0
    for i, d in enumerate(pile, 1):
        print("%2d. waiting: [%s] %s" % (i, d.get("cls", "note"), (d.get("body") or "")[:90]))
    for s in scars:
        print(s)
    print("approve them at a real terminal:  sandbox approve")
    return 0


def _approve(ws, argv):
    from . import notes
    name, _rest = _flag(argv, "--project")
    # The screen is the verb's: notes.approve prints the pile, its digest and
    # the prompt, then reads the key. A gate refusal is not a success — the
    # exit code is what a script reads.
    return notes.approve(ws, target_project=name)


def _recall(ws, argv):
    from . import notes
    target, rest, _refusal = _target(ws, argv)
    if "--ruling" in rest:
        rest.remove("--ruling")
        standing = notes.rulings(ws, target_project=target)
        for line in standing:
            print(line)
        if not standing:
            print("no ruling stands here yet — make one: sandbox note --ruling \"…\"")
        return 0
    digest, rest = _flag(rest, "--shown")
    if digest:
        rode = notes.shown(ws, digest)
        for line in rode:
            print(line)
        if not rode:
            print("nothing landed on that keypress — find one: sandbox recall --why")
        return 0
    if "--why" in rest:
        rest.remove("--why")
        for line in notes.why(ws, " ".join(rest)):
            print(line)
        return 0
    hits = notes.recall(ws, " ".join(rest), target_project=target)
    for h in hits:
        print(h)
    if not hits:
        print("nothing landed matches — the record is honest about that.")
    return 0


def _make(ws, argv):
    """one open form and one close form, and no third mood: the building
    itself happens in the session, and this verb keeps the books on it."""
    from . import make as mk
    rest = list(argv)
    project_flag, rest = _flag(rest, "--project")
    opening = "--open" in rest
    intent = None
    if opening:
        i = rest.index("--open")
        if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
            intent = rest[i + 1]
            del rest[i:i + 2]
        else:
            # --open followed by another flag: the intent is whatever words
            # are left once every flag is out, so no flag is ever the intent.
            del rest[i]
    closing = "--close" in rest
    rest = [a for a in rest if a != "--close"]
    summary, rest = _flag(rest, "--summary")
    if opening and intent is None:
        intent = " ".join(rest) or None
        rest = []
    if project_flag:
        rest = ["--project", project_flag] + rest
    if intent is None and not closing:
        print("a make opens with --open and closes with --close: "
              "sandbox make --open \"…\"")
        return 2
    target, rest, refusal = _target(ws, rest)
    name = rest[0] if rest else target
    if name is None:
        print(refusal or "make needs a project: --project NAME (or switch one on)")
        return 2
    if intent is not None:
        ok, msg = mk.open_session(ws, name, intent)
    else:
        ok, msg = mk.close_session(ws, name, summary or "")
    print(msg)
    return 0 if ok else 1


def _ship(ws, argv):
    """ship shows its own block and reads its own key (R10), so no bare
    prompt stands in front of it."""
    from . import ship as sh
    target, rest, refusal = _target(ws, argv)
    if refusal and not rest:
        print(refusal)
        return 2
    name = rest[0] if rest else target
    if name is None:
        print("ship needs a project: sandbox ship NAME")
        return 2
    ok, msg = sh.ship(ws, name)
    print(msg)
    return 0 if ok else 1


def _check(ws, argv):
    from . import check as ck
    target, rest, refusal = _target(ws, argv)
    if refusal and not rest:
        print(refusal)
        return 2
    name = rest[0] if rest else target
    if name is None:
        print("check needs a project: sandbox check NAME")
        return 2
    ok, msg = ck.run(ws, name)
    print(msg)
    return 0 if ok else 1


def _invalidate(ws, argv):
    from . import notes
    if len(argv) < 2:
        print("invalidate needs a line and your reason: "
              "sandbox invalidate ID \"why\"")
        return 2
    target, msg = notes.strike(ws, argv[0], " ".join(argv[1:]))
    if target is None:
        print(msg)
        return 1
    # surface: 6a
    print("staged to strike %s — the line stays on the record: %s"
          % (argv[0], (target.get("body") or "")[:70]))
    print(msg)
    return 0


def _session(ws, argv):
    from . import journal
    sub = argv[0] if argv else None
    key, rest = _flag(argv, "--key")
    name, rest = _flag(rest, "--project")
    agents, rest = _flag(rest, "--agents")
    if sub not in ("open", "close") or not key:
        print("session open --key K [--project NAME] · session close --key K")
        return 2
    e = journal.session(ws, sub, key, project=name, agents=agents)
    # surface: 2
    print("session %s on the record: %s (journal:%s)" % (sub, key, e["id"]))
    return 0


def _canon(ws, argv):
    """the projections a person can ask for by name.

    Canon is disposable by design: it is regenerated from the record at every
    landing, so this verb is the way to get it back after a hand edit. The
    memory page is the same move pointed at the host — the engine writes it
    from the record and a session only ever reads it (law 11).
    """
    from . import notes
    memory = "--memory" in argv
    argv = [a for a in argv if a != "--memory"]
    target, _rest, refusal = _target(ws, argv)
    if refusal:
        print(refusal)
        return 2
    if memory:
        path, n = notes.memory(ws, target)
        # surface: 8
        print("wrote %s — %d line(s), projected from the record" % (path, n))
        return 0
    notes.refresh_canon(ws, target)
    where = target or "the workshop"
    # surface: 8
    print("rebuilt canon for %s — projected from the record" % where)
    return 0


def _status(ws, argv):
    from . import status as st
    if "--line" in argv:
        # the host's status line calls this on a hot path: one row, nothing
        # written, and a 0 whatever it finds — a line that can fail a shell
        # is a line somebody turns off.
        print(st.line(ws))
        return 0
    print(st.status(ws))
    return 0


def _resume(ws, argv):
    from . import status as st
    return st.resume(ws)


def _play(ws, argv):
    from . import status as st
    print(st.play(ws))
    return 0


def _doctor(ws, argv):
    from . import status as st
    ok, lines = st.doctor(ws)
    for line in lines:
        print(line)
    return 0 if ok else 1


def _init(ws, argv):
    from . import onboard
    ok, text = onboard.run(ws)
    print(text)
    return 0 if ok else 1


def _save(ws, argv):
    from . import shelf
    note_, rest = _flag(argv, "--note")
    if not rest:
        print("save needs a path: sandbox save PATH [--note \"...\"]")
        return 2
    ok, msg = shelf.save(ws, rest[0], note=note_ or "")
    print(msg)
    return 0 if ok else 1


def _builds(ws, argv):
    """the shelf, read by a person: one row per build, then the door it came
    in by. A build that arrived from someone else says so on its own line —
    the browse door and the fetch door leave different marks, and a shelf
    that hid the difference would be laundering provenance (R18)."""
    from . import shelf
    cards = shelf.list_all(ws)
    if not cards:
        print("the shelf is empty — press one with: sandbox save PATH")
        return 0
    for c in cards:
        print("%-20s %-12s %s" % (c["name"], c.get("origin", ""), c.get("note", "")))
        print("%-20s %s" % ("", shelf.door_of(c)))
    pull = shelf.first_pull(ws)
    if pull["shared"] and not pull["witnessed"]:
        print("shared %d, no pull witnessed yet — stage one: "
              "sandbox note \"pull-witnessed: WHO BUILD\""
              % len(pull["shared"]))
    if shelf.offers_marketplace(ws):
        print("a friend adds this shelf with: claude plugin marketplace add "
              "\"$(sandbox shelf-dir)\"")
    return 0


def _shelf_dir(ws, argv):
    """where the shelf lives, printed. A friend hands this to the host as a
    marketplace source; it reads one path and writes nothing."""
    from . import shelf
    print(shelf.dirpath(ws))
    return 0


def _use(ws, argv):
    from . import project, shelf
    target, rest, refusal = _target(ws, argv)
    if refusal:
        print(refusal)
        return 2
    if not rest:
        print("use needs a build: sandbox use NAME")
        return 2
    if target is None:
        print("use needs a project: --project NAME (or switch one on)")
        return 2
    ok, msg = shelf.use(ws, rest[0], target, project.root_of(ws, target))
    print(msg)
    return 0 if ok else 1


def _share(ws, argv):
    from . import share as sh
    staging, rest = _flag(argv, "--to")
    sign = "--sign" in rest
    rest = [a for a in rest if a != "--sign"]
    if not rest or not staging:
        print("share needs a build and a staging dir: sandbox share NAME --to DIR")
        return 2
    ok, msg = sh.share(ws, rest[0], staging, sign=sign)
    print(msg)
    return 0 if ok else 1


def _fetch(ws, argv):
    from . import gate, share as sh
    source, rest = _flag(argv, "--from")
    expect, rest = _flag(rest, "--expect-key")
    if not source:
        print("fetch needs a source: sandbox fetch --from DIR [NAME]")
        return 2
    if not rest:
        names = sh.list_source(source)
        for n in names:
            print(n)
        if not names:
            print("nothing at that source in shelf shape.")
        return 0
    consent = gate.one_key()
    ok, msg = sh.fetch(ws, source, rest[0], consent, expect_key=expect)
    print(msg)
    return 0 if ok else 1


def _app(ws, argv):
    from . import apps, gate
    if not argv:
        installed = apps.list_installed(ws)
        for a in installed:
            print("%-20s %-10s %s" % (a["name"], a["version"], a["source"]))
        if not installed:
            print("no apps installed.")
        return 0
    sub, rest = argv[0], argv[1:]
    if sub == "install" and rest:
        cat, rest = _flag(rest, "--catalog")
        consent = gate.one_key()
        app_dir, source, why = apps.resolve_install(rest[0], cat)
        if why:
            print(why)
            return 1
        ok, msg = apps.install(ws, app_dir, consent, source=source)
    elif sub == "remove" and rest:
        ok, msg = apps.remove(ws, rest[0])
    else:
        print("app install DIR · app remove NAME · app (list)")
        return 2
    print(msg)
    return 0 if ok else 1


def _import(ws, argv):
    from . import succession
    take, rest = _flag(argv, "--projects")
    if not rest:
        print("import needs the old workshop: sandbox import PATH [--projects a,b,c]")
        return 2
    if take is None:
        offers = succession.list_old(rest[0])
        if not offers:
            print("nothing at %s looks like a workshop." % rest[0])
            return 1
        print("the old workshop offers:")
        for o in offers:
            print("  %-22s %-8s %s" % (o["name"], o["state"], o["goal"][:60]))
        print("choose with: sandbox import %s --projects name,name" % rest[0])
        return 0
    ok, text = succession.run(ws, rest[0], [t.strip() for t in take.split(",") if t.strip()])
    print(text)
    return 0 if ok else 1


def _setup(ws, argv):
    from . import update
    shim, shim_dir, on_path = update.write_shim()
    print("one shim written: %s -> this copy" % shim)
    if not on_path:
        print("add to your PATH if it is not there:  export PATH=\"%s:$PATH\"" % shim_dir)
    return 0


def _reset(ws, argv):
    from . import onboard, placement
    if not argv:
        print("reset needs a placed file: sandbox reset PATH-or-NAME")
        return 2
    payload = onboard.shipped_payload(ws)
    dest, matches = placement.resolve_placed(payload, argv[0])
    if dest is None:
        print("%s names %d placed files — say more of the path:" % (argv[0], len(matches)))
        for m in matches:
            print("  " + m)
        return 2
    if dest not in payload:
        print("that file was never placed by the system — nothing to reset to.")
        return 1
    # The pristine copy comes from the same payload init places — never from
    # a guessed path (the old basename guess could not reach agents/ or the
    # style, one directory down).
    src = payload[dest]
    if not os.path.exists(src):
        print("no pristine copy of %s in this core." % os.path.basename(dest))
        return 1
    print(placement.reset(ws, dest, src))
    return 0


def _export_report(report, out=print):
    """what the run did, then the path it wrote — the path is the last line,
    so a check can read it off the tail rather than guessing at a glob."""
    first, last = report["span"]
    # surface: 7
    out("%d line(s), %s → %s" % (report["lines"], first[:10] or "—", last[:10] or "—"))
    from . import clean, export
    if report["redacted"]:
        total, named, dead = export.redaction_summary(report)
        # surface: 7
        out("redacted %d span(s)%s" % (total, ": " + " · ".join(named) if named else ""))
        if report["terms"] is None:
            # surface: 7
            out("no terms file — the floor needles only. point %s at a list to add your own."
                % clean.TERMS_ENV)
        else:
            # surface: 7
            out("your terms file loaded — %d term(s), %d never matched"
                % (len(report["terms"]), dead))
    else:
        # surface: 7
        out("not redacted — %d span(s) would go under --redact" % report["would"])
    # the last line is the path, and it wears `~` like every other path this
    # core prints — an owner's name is not part of where a file is.
    out(clean.strip_home(report["path"])[0])


def _export(ws, argv):
    from . import export
    to, argv = _flag(argv, "--to")
    name, argv = _flag(argv, "--project")
    since, argv = _flag(argv, "--since")
    form = "md"
    if "--html" in argv:
        form, argv = "html", [a for a in argv if a != "--html"]
    if "--portable" in argv:
        if form == "html":
            # surface: 3a
            print("export writes one form at a time: --html or --portable")
            return 2
        form, argv = "portable", [a for a in argv if a != "--portable"]
    redact = "--redact" in argv
    path, report = export.write(ws, form=form, redact=redact, since=since,
                                project=name, to=to)
    if path is None:
        print(report["refused"])
        return 1
    _export_report(report)
    return 0


def _page(ws, argv):
    from . import export, journal
    # surface: 2
    print("page is export --html now — writing %s%s.html"
          % (export.STEM, journal.now()[:10]))
    return _export(ws, argv + ["--html"])


def _update(ws, argv):
    from . import registry, update
    name, argv = _flag(argv, "--rebuild")
    if name:
        ok, lines = registry.rebuild(ws, name)
        for line in lines:
            print(line)
        return 0 if ok else 2
    ok, text = update.run(ws)
    print(text)
    return 0 if ok else 1


def _release(ws, argv):
    from . import integrity
    said, argv = _flag(argv, "--is-release-commit")
    if said is not None:
        if integrity.is_release_commit(integrity.commit_message(said)):
            return 0
        # surface: 3c
        print("i turned this commit back: main takes the commits a release makes.")
        print("what would work: git switch -c NAME && git commit")
        return 1
    if "--hook" in argv:
        ok, msg = integrity.place_hook()
        print(msg)
        return 0 if ok else 1
    ok, msg = integrity.release_check()
    print(msg)
    return 0 if ok else 1


def _verify(ws, argv):
    from . import integrity
    ok, msg = integrity.verify()
    print(msg)
    return 0 if ok else 1


def _seal(ws, argv):
    from . import integrity
    ok, msg = integrity.seal()
    print(msg)
    return 0 if ok else 1


TABLE = {
    "init": _init,
    "save": _save,
    "builds": _builds,
    "shelf-dir": _shelf_dir,
    "use": _use,
    "share": _share,
    "fetch": _fetch,
    "app": _app,
    "import": _import,
    "setup": _setup,
    "reset": _reset,
    "page": _page,
    "export": _export,
    "update": _update,
    "release": _release,
    "verify": _verify,
    "seal": _seal,
    "version": _version,
    "plugin-dir": _plugin_dir,
    "help": _help,
    "project": _project,
    "note": _note,
    "drafts": _drafts,
    "approve": _approve,
    "recall": _recall,
    "make": _make,
    "ship": _ship,
    "check": _check,
    "invalidate": _invalidate,
    "session": _session,
    "status": _status,
    "canon": _canon,
    "resume": _resume,
    "play": _play,
    "doctor": _doctor,
}

DECLARATIONS = {
    "init": declaration(reads=("core",), writes=("workshop", "state", "settings"),
                        emits="place",
                        blurb="open a workshop here and place the vessel"),
    "save": declaration(reads=("project", "workshop"), writes=("shelf",), emits="assert",
                        blurb="keep a build on the shelf"),
    "builds": declaration(reads=("shelf",),
                          blurb="list what the shelf keeps"),
    "shelf-dir": declaration(reads=("shelf",),
                             blurb="print the directory a friend adds as a marketplace"),
    "use": declaration(reads=("shelf",), writes=("project", "shelf"),
                       blurb="load a shelf build onto a project"),
    "share": declaration(reads=("shelf",), writes=("workshop",),
                         blurb="stage a build for someone else to fetch"),
    "fetch": declaration(reads=("workshop",), writes=("shelf",), gate="keystroke",
                         emits="assert",
                         blurb="bring a friend's build onto your shelf"),
    "app": declaration(reads=("workshop", "apps"), writes=("apps", "workshop"),
                       gate="keystroke", emits="place",
                       blurb="install or remove an app; your k lands the install"),
    "import": declaration(reads=("workshop",), writes=("workshop", "state", "project", "shelf"),
                          emits="assert",
                          blurb="carry an old workshop in, whole"),
    "setup": declaration(reads=("core",), writes=("workshop",),
                         blurb="write the sandbox shim where your shell can find it"),
    "reset": declaration(reads=("core",), writes=("workshop", "state"), emits="place",
                         blurb="restore a placed file to what this core ships"),
    "page": declaration(reads=("workshop", "project"), writes=("workshop",),
                        emits="export",
                        blurb="write the record as one html file"),
    "export": declaration(reads=("workshop", "project"), writes=("workshop",),
                          emits="export",
                          blurb="write the record to one file you can hand over"),
    "update": declaration(reads=("core", "workshop"), writes=("workshop", "state", "settings"),
                          emits="place",
                          blurb="move the system forward; your own things stay"),
    "release": declaration(reads=("core",),
                           blurb="check what a release needs before the ceremony starts"),
    "verify": declaration(reads=("core",),
                          blurb="check this core against its manifest"),
    "seal": declaration(reads=("core",), writes=("core",),
                        blurb="write this core's manifest"),
    "version": declaration(reads=("VERSION",),
                           blurb="print this core's version and which tree runs"),
    "plugin-dir": declaration(reads=("core",),
                              blurb="print the directory the plugin loads from"),
    "help": declaration(blurb="this page: every verb, what it does, what it needs"),
    "project": declaration(reads=("project",), writes=("project", "workshop"), emits="assert",
                           blurb="make, switch, or finish a project"),
    "note": declaration(reads=("project",), writes=("workshop",), gate="keystroke", emits="assert",
                        blurb="stage one line on the record; your k lands it"),
    "drafts": declaration(reads=("workshop",), writes=("workshop",),
                          blurb="show the notes waiting for your approval; drop one by number"),
    "approve": declaration(reads=("workshop",), writes=("workshop", "project"),
                           gate="tty-keystroke", emits="assert",
                           blurb="land the drafts waiting on your k, at a real terminal"),
    "recall": declaration(reads=("workshop", "project"),
                          blurb="ask the record before deciding twice"),
    "make": declaration(reads=("project",), writes=("workshop",), emits="make",
                        blurb="open a build session, or close it on a computed diff"),
    "ship": declaration(reads=("project",), writes=("workshop",), gate="keystroke", emits="ship",
                        blurb="run the project's own checks; celebrate only on green"),
    "check": declaration(reads=("project",), writes=("workshop",), emits="check",
                         blurb="run the project's checks; a green run proves what waited on them"),
    "invalidate": declaration(reads=("workshop",), writes=("workshop",),
                              gate="keystroke", emits="invalidate",
                              blurb="strike a landed line; it stays, struck — your k lands it"),
    "session": declaration(reads=("workshop",), writes=("workshop",), emits="session",
                           blurb="open or close a working session on the record"),
    "canon": declaration(reads=("workshop", "project"),
                         writes=("workshop", "project"),
                         blurb="rebuild a project's canon page, or the memory page a session reads"),
    "status": declaration(reads=("workshop", "project"),
                          blurb="what the workshop holds and what needs you"),
    "resume": declaration(reads=("workshop",), writes=("workshop", "project"),
                          gate="tty-keystroke", emits="assert",
                          blurb="what happened since you left, plus one k for what waited"),
    "play": declaration(writes=("workshop",),
                        blurb="open the playground, where nothing counts"),
    "doctor": declaration(reads=("workshop", "project"),
                          blurb="check the workshop's health, one line each"),
}


def dispatch(ws, verb, argv):
    """the one door's hand-off. Unknown verbs and unknown flags refuse
    plainly — no verb ever swallows a --flag as content."""
    fn = TABLE.get(verb)
    if fn is None:
        print("no verb named %r yet — this copy is early. try: sandbox help" % verb)
        return 2
    # --help is the one flag every verb knows, and it is answered here, above
    # the unknown-flag refusal — so no verb body ever sees it. It is not in
    # FLAGS on purpose: that table is per-verb content, and the scar it came
    # from (note --help staging a draft whose whole body was the flag) is a
    # verb reading a flag as words.
    if "--help" in argv or "-h" in argv:
        from .selfmap import render_verb_help
        print(render_verb_help(verb))
        return 0
    spec = FLAGS.get(verb, {})
    unknown = _unknown_flags(argv, spec)
    if unknown:
        print(_flags_refusal(verb, unknown[0], spec))
        return 2
    return fn(ws, argv)
