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

GATE_WORDS = {
    "none": "runs freely",
    "provisional": "acts now, your next arrival confirms",
    "keystroke": "needs your k",
    "tty-keystroke": "needs your k at a real terminal",
}


def render_verbs():
    lines = ["| verb | gate | writes |", "|---|---|---|"]
    for name in sorted(verbs.TABLE):
        d = verbs.DECLARATIONS[name]
        writes = ", ".join(d["writes"]) if d["writes"] else "nothing"
        lines.append("| `%s` | %s | %s |" % (name, GATE_WORDS[d["gate"]], writes))
    return "\n".join(lines)


def manual_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "docs", "MANUAL.md")


def write():
    p = manual_path()
    text = open(p, encoding="utf-8").read()
    if BEGIN not in text or END not in text:
        raise SystemExit("MANUAL.md has no generated block markers")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = head + BEGIN + "\n" + render_verbs() + "\n" + END + tail
    open(p, "w", encoding="utf-8").write(new)
    return p


def current_block():
    text = open(manual_path(), encoding="utf-8").read()
    if BEGIN not in text:
        return None
    return text.split(BEGIN, 1)[1].split(END, 1)[0].strip()


if __name__ == "__main__":
    if "--write" in sys.argv:
        print("wrote: %s" % write())
    else:
        print(render_verbs())
