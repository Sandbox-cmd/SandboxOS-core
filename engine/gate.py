# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the gate on becoming (amana). Consent is a keystroke, never a field.

What changes the body's own shape — identity, rules, schema, the memory
canon — promotes only on the owner's key at a real terminal. Everything else
passes without ceremony: the gate stays rare so it survives being real.
Adopted from the seventh body with the forged-pty scar carried.

The key is read here and nowhere else: one character from the terminal
itself, never a parameter a caller can hand in, and the pile it lands is
fingerprinted first so a keypress can only land what the eyes were on.
"""
import hashlib
import os
import sys

COMMIT_KEY = "k"

# The harness's own name for itself.
SYNTHETIC_ENV = "SANDBOX_SYNTHETIC_TTY"

# The test rig's door: the character a harness supplies when no terminal
# exists. It stamps every consent it mints — see mint_consent.
TEST_KEY_ENV = "SANDBOX_TEST_KEY"

# The terminal itself, whatever stdin happens to be.
TTY = "/dev/tty"

# The most rows one key ever covers. A hash over what scrolled past is a hash
# over what nobody read.
PAGE = 20

# surface: 3b
# the one refusal every gated verb prints, with the verb's own name in it.
NOT_A_TTY = "landing needs your 'k' at a real terminal — run: sandbox %s"


def synthetic():
    """true when a test harness allocated this terminal.

    A terminal is a file descriptor, not a person. A forged pty once landed
    a fact reading `[human | stated]` that no human ever saw. This is NOT a
    defence — an adversary simply would not set the variable. It exists so a
    green suite can never be mistaken for a person's approval, and so an
    audit can tell the two apart after the fact.
    """
    return bool(os.environ.get(SYNTHETIC_ENV))


def at_a_terminal():
    """whether one key can be read right now.

    Stdin must be a terminal AND /dev/tty must open, because the key is read
    from the terminal itself: whatever was piped in is never a hand. A rig's
    key counts, and is stamped for it.
    """
    if os.environ.get(TEST_KEY_ENV):
        return True
    if not sys.stdin.isatty():
        return False
    try:
        fd = os.open(TTY, os.O_RDWR)
    except OSError:
        return False
    os.close(fd)
    return True


def read_key(prompt=None):
    """one keypress from the terminal itself — no echo, no line to submit.

    Returns (char, why); char is None when nothing could answer. The
    terminal's settings are restored on every path out of the raw read.
    """
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    if not at_a_terminal():
        return None, "no terminal"
    rig = os.environ.get(TEST_KEY_ENV)
    if rig:
        return rig[:1], "rig"
    import termios
    import tty as rawtty
    try:
        fd = os.open(TTY, os.O_RDWR)
    except OSError:
        return None, "no terminal"
    try:
        try:
            saved = termios.tcgetattr(fd)
        except termios.error:
            return None, "no terminal"
        try:
            rawtty.setraw(fd)
            raw = os.read(fd, 1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)
    finally:
        os.close(fd)
    if not raw:
        return None, "no key"
    return raw.decode("utf-8", "replace"), "tty"


def shown_digest(lines):
    """the fingerprint of exactly what was printed, joined as it was printed."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def show(rows, out):
    """print the block one key is about to land, then its fingerprint.

    Returns (how many rows were shown, the full digest). A pile longer than
    the page leaves the rest for a second pass, so the hash covers what was
    read and nothing else.
    """
    block = ["%2d. %s" % (i, r) for i, r in enumerate(rows[:PAGE], 1)]
    if len(rows) > PAGE:
        block.append("%d of %d shown — land these, or narrow with: "
                     "sandbox approve --project NAME" % (PAGE, len(rows)))
    for line in block:
        out(line)
    digest = shown_digest(block)
    out("shown: %s" % digest[:8])
    return min(len(rows), PAGE), digest


def ask(n, out):
    """the prompt between the block and the key."""
    if n == 1:
        out("press k to land this one · any other key cancels")
    else:
        out("press k to land these %d · any other key cancels" % n)


# A proposal carrying its own consent is a tamper signal, refused outright.
CONSENT_FIELDS = ("consent", "approved", "confirmed", "committed", "granted",
                  "owner_ok", "hand")

# Blast class reads ONLY the code-stamped write target — never free text.
GATED = ("identity", "rules", "schema", "memory-canon")


def blast_class(proposal):
    target = (proposal.get("target") or "").split(":", 1)[0].strip().lower()
    return target if target in GATED else None


def mint_consent(shown=None):
    """the one seam between a human hand and a promotion. Headless mints nothing.

    `shown` is the digest of the block the person was looking at; it rides the
    consent onto every line it lands. A rig's key is always stamped synthetic,
    on its own, so no rig path can mint an unstamped hand.
    """
    char, _why = read_key()
    if char != COMMIT_KEY:
        return None
    c = {"source": "tty", "key": char}
    if shown:
        c["shown"] = shown
    if synthetic() or os.environ.get(TEST_KEY_ENV):
        c["synthetic"] = True
    return c


def one_key(out=print):
    """one real key for a verb that has no screen of its own yet.

    fetch and app install each land on the owner's k; until each grows the
    block it shows first, the prompt is this gate's own and the key is read
    the way approve reads it — never handed in by the caller. ship left this
    seat in 9.0: it shows its checks and reads its own key (R10).
    """
    if not at_a_terminal():
        return None
    ask(1, out)
    return mint_consent()


def decide(proposal, consent=None):
    """the three verdicts: REFUSE | PASS | PROMOTE. every landed write
    goes through here."""
    for f in CONSENT_FIELDS:
        if f in proposal:
            return "REFUSE", "proposal carries its own consent ('%s') — refused as tampering" % f
    cls = blast_class(proposal)
    if cls is None:
        return "PASS", "this class of change needs no approval — the gate stays rare"
    if not consent or consent.get("source") != "tty" or consent.get("key") != COMMIT_KEY:
        return "REFUSE", "'%s' changes the tool's own shape — it needs your %r at a real terminal" % (cls, COMMIT_KEY)
    return "PROMOTE", "owner keypress at a real terminal — '%s' may land" % cls
