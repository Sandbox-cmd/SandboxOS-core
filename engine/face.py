# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the face's first tokens — restrained on purpose. (taste stratum, dated
2026-07-30: the full design pass happens with the owner's taste rulings in
the room; until then the CLI wears work clothes with one earned accent.)

Rules held here: color only at a real terminal, never under NO_COLOR, and
one accent — the line that needs the owner's eyes. Everything else stays
plain text that pipes and logs cleanly.
"""
import os
import sys

ACCENT = "\033[1m"   # bold, nothing louder — earned, single, checkable
RESET = "\033[0m"


def _on():
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def accent(text):
    """the one emphasis: what needs the owner. Plain when piped."""
    return ACCENT + text + RESET if _on() else text


# the three verdicts doctor speaks. a proved fence is `ok`, a fence that
# needs the owner is the one accented word, and a fence nobody could read is
# a gap in what doctor can see rather than a fault in the workshop.
OK, LOOK, GAP = "ok", "look", "?"


def mark(verdict):
    """the mark doctor and checks speak: three verdicts, booleans still read.

    True and False are the two states every older caller hands in; the three
    words are what the report itself carries, so a receipt nobody could read
    stops being printed as a failure.
    """
    if verdict is True or verdict == OK:
        return " ok "
    if verdict is False or verdict == LOOK:
        return accent("LOOK")
    return " ?  "
