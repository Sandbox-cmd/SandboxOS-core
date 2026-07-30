# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The face's first tokens — restrained on purpose. (taste stratum, dated
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
    """The one emphasis: what needs the owner. Plain when piped."""
    return ACCENT + text + RESET if _on() else text


def mark(ok):
    """The two-state mark doctor and checks speak."""
    return " ok " if ok else accent("LOOK")
