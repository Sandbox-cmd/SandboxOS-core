# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The gate on becoming (amana). Consent is a keystroke, never a field.

What changes the body's own shape — identity, rules, schema, the memory
canon — promotes only on the owner's key at a real terminal. Everything else
passes without ceremony: the gate stays rare so it survives being real.
Adopted from the seventh body with the forged-pty scar carried.
"""
import os
import sys

COMMIT_KEY = "k"

# The harness's own name for itself.
SYNTHETIC_ENV = "SANDBOX_SYNTHETIC_TTY"


def synthetic():
    """True when a test harness allocated this terminal.

    A terminal is a file descriptor, not a person. A forged pty once landed
    a fact reading `[human | stated]` that no human ever saw. This is NOT a
    defence — an adversary simply would not set the variable. It exists so a
    green suite can never be mistaken for a person's approval, and so an
    audit can tell the two apart after the fact.
    """
    return bool(os.environ.get(SYNTHETIC_ENV))


# A proposal carrying its own consent is a tamper signal, refused outright.
CONSENT_FIELDS = ("consent", "approved", "confirmed", "committed", "granted",
                  "owner_ok", "hand")

# Blast class reads ONLY the code-stamped write target — never free text.
GATED = ("identity", "rules", "schema", "memory-canon")


def blast_class(proposal):
    target = (proposal.get("target") or "").split(":", 1)[0].strip().lower()
    return target if target in GATED else None


def mint_consent(is_real_tty=None, keychar=None):
    """The one seam between a human hand and a promotion. Headless mints nothing."""
    tty = sys.stdin.isatty() if is_real_tty is None else is_real_tty
    if not tty:
        return None
    if keychar != COMMIT_KEY:
        return None
    c = {"source": "tty", "key": keychar}
    if synthetic():
        c["synthetic"] = True
    return c


def decide(proposal, consent=None):
    """REFUSE | PASS | PROMOTE. Every landed write goes through here."""
    for f in CONSENT_FIELDS:
        if f in proposal:
            return "REFUSE", "proposal carries its own consent ('%s') — refused as tampering" % f
    cls = blast_class(proposal)
    if cls is None:
        return "PASS", "this class of change needs no approval — the gate stays rare"
    if not consent or consent.get("source") != "tty" or consent.get("key") != COMMIT_KEY:
        return "REFUSE", "'%s' changes the tool's own shape — it needs your %r at a real terminal" % (cls, COMMIT_KEY)
    return "PROMOTE", "owner keypress at a real terminal — '%s' may land" % cls
