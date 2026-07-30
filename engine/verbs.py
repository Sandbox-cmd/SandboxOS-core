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


# --- the verbs of band A. Each band adds its rows here, never elsewhere. ---

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


TABLE = {
    "version": _version,
    "help": _help,
}

DECLARATIONS = {
    "version": declaration(reads=("VERSION",)),
    "help": declaration(),
}


def dispatch(ws, verb, argv):
    """The one door's hand-off. Unknown verbs refuse plainly."""
    fn = TABLE.get(verb)
    if fn is None:
        print("no verb named %r yet — this copy is early. try: sandbox help" % verb)
        return 2
    return fn(ws, argv)
