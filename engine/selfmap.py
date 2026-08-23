# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""selfmap — the docs' generated blocks, projected from the source.

A hand-carried table rots; this one is rendered from the verb table itself.
`python3 -m engine.selfmap --write` refreshes the block in docs/MANUAL.md;
the doc lint fails the suite when the block and the source drift.
"""
import os
import sys

from . import verbs

BEGIN = "<!-- verbs:begin (generated — run: python3 -m engine.selfmap --write) -->"
END = "<!-- verbs:end -->"

# What each gate speed costs the person, said in their words — not the
# engine's. "runs freely" sounded like a liberty; it is the absence of a gate.
GATE_WORDS = {
    "none": "no key needed",
    "provisional": "acts now; your next sandbox resume confirms it",
    "keystroke": "needs your k",
    "tty-keystroke": "needs your k at a real terminal",
}

# The write scopes are the engine's own vocabulary; these are the same
# places named to someone who has never opened verbs.py. One map, so help
# and the MANUAL cannot disagree about what a verb touches.
SCOPE_WORDS = {
    "state": "the record",
    "workshop": "the workshop",
    "project": "the project",
    "shelf": "the shelf",
    "core": "this core",
    "apps": "apps",
    "settings": "settings",
}


def scope_words(writes):
    """a verb's write scopes, in a person's words. Nothing is a real answer."""
    if not writes:
        return "nothing"
    return ", ".join(SCOPE_WORDS[w] for w in writes)


def flag_words(name):
    """a verb's flags as a person would type them, or "none"."""
    spec = verbs.FLAGS.get(name, {})
    if not spec:
        return "none"
    return ", ".join(k + (" " + v if v else "") for k, v in spec.items())


def render_verbs():
    lines = ["| verb | what it does | gate | writes |", "|---|---|---|---|"]
    for name in sorted(verbs.TABLE):
        d = verbs.DECLARATIONS[name]
        lines.append("| `%s` | %s | %s | %s |"
                     % (name, d["blurb"], GATE_WORDS[d["gate"]], scope_words(d["writes"])))
    return "\n".join(lines)


def render_verb_help(name):
    """`sandbox VERB --help`: what it does, what it costs, what it writes,
    what it takes — then where the long page is. Generated, so it cannot
    drift from the verb it describes."""
    d = verbs.DECLARATIONS[name]
    return "\n".join([
        d["blurb"],
        "gate: %s" % GATE_WORDS[d["gate"]],
        "writes: %s" % scope_words(d["writes"]),
        "flags: %s" % flag_words(name),
        "the page: docs/MANUAL.md",
    ])


def manual_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "docs", "MANUAL.md")


def write():
    p = manual_path()
    with open(p, encoding="utf-8") as f:
        text = f.read()
    if BEGIN not in text or END not in text:
        raise SystemExit("MANUAL.md has no generated block markers")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = head + BEGIN + "\n" + render_verbs() + "\n" + END + tail
    with open(p, "w", encoding="utf-8") as f:
        f.write(new)
    return p


def current_block():
    with open(manual_path(), encoding="utf-8") as f:
        text = f.read()
    if BEGIN not in text:
        return None
    return text.split(BEGIN, 1)[1].split(END, 1)[0].strip()


if __name__ == "__main__":
    if "--write" in sys.argv:
        print("wrote: %s" % write())
    else:
        print(render_verbs())
