# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Verbs as declared action types (law 11 made structural).

Every verb is one function plus one DECLARATION: what it reads, the only
scopes it may write, which gate speed it needs, and the event it emits.
Declarations bind ENGINE CODE and are lint-enforced; the model's own session
writes are bound by the guard's standing fences instead — two regimes,
neither claiming the other's coverage (spec §2).

The same table serves every surface: the CLI dispatches through it, and the
agent tool-surface is generated from it — no surface re-implements a verb.
"""
import os

# The record's op set. Eight inherited, one born with the seam.
OPS = ("genesis", "session", "assert", "invalidate", "make",
       "ratify", "ship", "halt", "place")

GATES = ("none", "provisional", "keystroke", "tty-keystroke")

# Write scopes are symbolic here and resolved against a live workshop by the
# code that enforces them. "state" is the record's own directory — only the
# desk-family verbs may name it.
SCOPES = ("state", "project", "workshop", "core", "shelf", "apps", "settings")


def declaration(reads=(), writes=(), gate="none", emits=None):
    assert gate in GATES, gate
    assert emits is None or emits in OPS, emits
    for w in writes:
        assert w in SCOPES, w
    return {"reads": tuple(reads), "writes": tuple(writes),
            "gate": gate, "emits": emits}


# --- helpers ------------------------------------------------------------

def _flag(argv, name):
    """Pop --name VALUE from argv. Returns (value, rest)."""
    argv = list(argv)
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1] if i + 1 < len(argv) else None
        return val, argv[:i] + argv[i + 2:]
    return None, argv


def _target(ws, argv):
    """The project a bare verb lands on: --project NAME, else the single
    on-project, else None (workshop-level)."""
    from . import project
    name, rest = _flag(argv, "--project")
    if name:
        return name, rest
    on = project.on_list(ws)
    return (on[0] if len(on) == 1 else None), rest


def _tty():
    import sys
    return sys.stdin.isatty()


# --- the verbs. Each band adds its rows here, never elsewhere. -----------

def _version(ws, argv):
    from .cli import version_line
    print(version_line())
    return 0


def _help(ws, argv):
    from .cli import version_line
    print(version_line())
    print("a maker's operating system for your own machine.")
    print()
    print("verbs so far: " + " ".join(sorted(TABLE)))
    print("this copy is early — verbs land band by band, each with its check.")
    return 0


def _project(ws, argv):
    from . import project
    if not argv:
        for p in project.list_all(ws):
            print("%-20s %-8s %s" % (p["dir"], p["state"], p["goal"]))
        return 0
    sub, rest = argv[0], argv[1:]
    if sub == "new" and rest:
        ok, msg = project.new(ws, rest[0], " ".join(rest[1:]))
    elif sub in ("on", "off") and rest:
        ok, msg = project.switch(ws, rest[0], sub == "on")
    elif sub == "done" and rest:
        ok, msg = project.done(ws, rest[0])
    else:
        print("project new NAME [goal] · on NAME · off NAME · done NAME")
        return 2
    print(msg)
    return 0 if ok else 1


def _note(ws, argv):
    from . import notes
    target, rest = _target(ws, argv)
    if "--workshop" in rest:
        rest.remove("--workshop")
        target = None
    if not rest:
        print("note needs words: sandbox note \"what you found\"")
        return 2
    disp, msg = notes.note(ws, " ".join(rest), target_project=target)
    print(msg)
    return 0


def _drafts(ws, argv):
    from . import desk
    pile, scars = desk.drafts(ws)
    if not pile and not scars:
        print("i found nothing waiting — no notes need your approval.")
        return 0
    for d in pile:
        print("waiting: [%s] %s" % (d.get("cls", "note"), (d.get("body") or "")[:90]))
    for s in scars:
        print(s)
    print("approve them at a real terminal:  sandbox approve")
    return 0


def _approve(ws, argv):
    from . import notes
    n, msg = notes.approve(ws, is_real_tty=_tty(), keychar="k" if _tty() else None)
    print(msg)
    return 0


def _recall(ws, argv):
    from . import notes
    target, rest = _target(ws, argv)
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
    from . import make as mk
    target, rest = _target(ws, argv)
    if target is None:
        print("make needs a project: --project NAME (or switch one on)")
        return 2
    intent, rest = _flag(rest, "--open")
    if intent is not None:
        ok, msg = mk.open_session(ws, target, intent)
    elif "--close" in rest:
        rest.remove("--close")
        summary, rest = _flag(rest, "--summary")
        ok, msg = mk.close_session(ws, target, summary or "")
    else:
        print("make --open \"intent\" · make --close [--summary \"...\"]")
        return 2
    print(msg)
    return 0 if ok else 1


def _ship(ws, argv):
    from . import gate, ship as sh
    target, rest = _target(ws, argv)
    name = rest[0] if rest else target
    if name is None:
        print("ship needs a project: sandbox ship NAME")
        return 2
    consent = gate.mint_consent(is_real_tty=_tty(), keychar="k" if _tty() else None)
    ok, msg = sh.ship(ws, name, consent)
    print(msg)
    return 0 if ok else 1


def _status(ws, argv):
    from . import status as st
    print(st.status(ws))
    return 0


def _resume(ws, argv):
    from . import status as st
    text, _n = st.resume(ws, is_real_tty=_tty(), keychar="k" if _tty() else None)
    print(text)
    return 0


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
    from . import shelf
    cards = shelf.list_all(ws)
    if not cards:
        print("the shelf is empty — press one with: sandbox save PATH")
        return 0
    for c in cards:
        print("%-20s %-12s %s" % (c["name"], c.get("origin", ""), c.get("note", "")))
    return 0


def _use(ws, argv):
    from . import project, shelf
    target, rest = _target(ws, argv)
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
    if not rest or not staging:
        print("share needs a build and a staging dir: sandbox share NAME --to DIR")
        return 2
    ok, msg = sh.share(ws, rest[0], staging)
    print(msg)
    return 0 if ok else 1


def _fetch(ws, argv):
    from . import gate, share as sh
    source, rest = _flag(argv, "--from")
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
    consent = gate.mint_consent(is_real_tty=_tty(), keychar="k" if _tty() else None)
    ok, msg = sh.fetch(ws, source, rest[0], consent)
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
        consent = gate.mint_consent(is_real_tty=_tty(), keychar="k" if _tty() else None)
        ok, msg = apps.install(ws, rest[0], consent)
    elif sub == "remove" and rest:
        ok, msg = apps.remove(ws, rest[0])
    else:
        print("app install DIR · app remove NAME · app (list)")
        return 2
    print(msg)
    return 0 if ok else 1


def _reset(ws, argv):
    from . import onboard, placement
    if not argv:
        print("reset needs a placed file: sandbox reset PATH")
        return 2
    dest = os.path.abspath(os.path.expanduser(argv[0]))
    b = placement.book(ws)
    if dest not in b:
        print("that file was never placed by the system — nothing to reset to.")
        return 1
    src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "vessel", "claude-code")
    src = os.path.join(src_dir, os.path.basename(dest))
    if not os.path.exists(src):
        print("no pristine copy of %s in this core." % os.path.basename(dest))
        return 1
    print(placement.reset(ws, dest, src))
    return 0


def _page(ws, argv):
    from . import page
    out = page.render(ws)
    print("rendered: %s — open it in any browser; it asks the network for nothing." % out)
    return 0


def _update(ws, argv):
    from . import update
    ok, text = update.run(ws)
    print(text)
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
    "use": _use,
    "share": _share,
    "fetch": _fetch,
    "app": _app,
    "reset": _reset,
    "page": _page,
    "update": _update,
    "verify": _verify,
    "seal": _seal,
    "version": _version,
    "help": _help,
    "project": _project,
    "note": _note,
    "drafts": _drafts,
    "approve": _approve,
    "recall": _recall,
    "make": _make,
    "ship": _ship,
    "status": _status,
    "resume": _resume,
    "play": _play,
    "doctor": _doctor,
}

DECLARATIONS = {
    "init": declaration(reads=("core",), writes=("workshop", "state", "settings"),
                        emits="place"),
    "save": declaration(reads=("project", "workshop"), writes=("shelf",), emits="assert"),
    "builds": declaration(reads=("shelf",)),
    "use": declaration(reads=("shelf",), writes=("project", "shelf")),
    "share": declaration(reads=("shelf",), writes=("workshop",)),
    "fetch": declaration(reads=("workshop",), writes=("shelf",), gate="keystroke",
                         emits="assert"),
    "app": declaration(reads=("workshop", "apps"), writes=("apps", "workshop"),
                       gate="keystroke", emits="place"),
    "reset": declaration(reads=("core",), writes=("workshop", "state"), emits="place"),
    "page": declaration(reads=("workshop", "project"), writes=("workshop",)),
    "update": declaration(reads=("core", "workshop"), writes=("workshop", "state", "settings"),
                          emits="place"),
    "verify": declaration(reads=("core",)),
    "seal": declaration(reads=("core",), writes=("core",)),
    "version": declaration(reads=("VERSION",)),
    "help": declaration(),
    "project": declaration(reads=("project",), writes=("project", "workshop"), emits="assert"),
    "note": declaration(reads=("project",), writes=("workshop",), gate="keystroke", emits="assert"),
    "drafts": declaration(reads=("workshop",)),
    "approve": declaration(reads=("workshop",), writes=("workshop", "project"),
                           gate="tty-keystroke", emits="assert"),
    "recall": declaration(reads=("workshop", "project")),
    "make": declaration(reads=("project",), writes=("workshop",), emits="make"),
    "ship": declaration(reads=("project",), writes=("workshop",), gate="keystroke", emits="ship"),
    "status": declaration(reads=("workshop", "project")),
    "resume": declaration(reads=("workshop",), writes=("workshop", "project"),
                          gate="tty-keystroke", emits="assert"),
    "play": declaration(writes=("workshop",)),
    "doctor": declaration(reads=("workshop", "project")),
}


def dispatch(ws, verb, argv):
    """The one door's hand-off. Unknown verbs refuse plainly."""
    fn = TABLE.get(verb)
    if fn is None:
        print("no verb named %r yet — this copy is early. try: sandbox help" % verb)
        return 2
    return fn(ws, argv)
