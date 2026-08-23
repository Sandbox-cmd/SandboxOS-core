# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""share / fetch — builds travel between workshops, honestly.

Share stages a build for the shelf repo: the export never carries git
history, every home path in it is rewritten to `~` rather than refused (a
path is a shape and the shape has a spelling that belongs to nobody), and
what stripping cannot fix — the owner's private terms, a deny-listed file —
still refuses, per file, with the reason. The push is the owner's hand,
always. Fetch pulls from a shelf-shaped source: bytes are hash-verified
against the card BEFORE the keystroke, the signature is checked when the
card carries one, the source is labeled in one line a person decides on,
and what lands is marked origin: external so provenance never launders.

The signing key is a SECOND key (R15): a leaked shelf key must never speak
for the core's manifest, so the env that names the core's own key is refused
here by name.
"""
import os
import shutil
import subprocess

from . import clean, desk, gate, shelf

SECKEY_ENV = "SANDBOX_SHELF_SECKEY"
PUBKEY_ENV = "SANDBOX_SHELF_PUBKEY"
SIG_SUFFIX = ".minisig"

# minisign's own default secret key — the one the core's manifest is signed
# with. The shelf never borrows it (R15).
CORE_KEY = os.path.join("~", ".minisign", "minisign.key")


def _same_path(a, b):
    return os.path.abspath(os.path.expanduser(a)) == os.path.abspath(os.path.expanduser(b))


def _read_key(value):
    """a minisign public key, from the key itself or from the file holding it."""
    value = (value or "").strip()
    if not value:
        return None
    p = os.path.expanduser(value)
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()
                     and not l.startswith("untrusted comment")]
        return lines[-1] if lines else None
    return value


def _pubkey_for(seckey):
    """the public half of the shelf's key: named by the env, or sitting beside
    the secret one. It rides in the card, so a friend can check the signature
    holds even before they have decided whose key it is."""
    named = _read_key(os.environ.get(PUBKEY_ENV, ""))
    if named:
        return named
    sec = os.path.expanduser(seckey)
    for cand in (sec + ".pub", os.path.splitext(sec)[0] + ".pub",
                 os.path.join(os.path.dirname(sec), "minisign.pub")):
        if os.path.exists(cand):
            got = _read_key(cand)
            if got:
                return got
    return None


def _add_field(card_path, name, value):
    """one field into a card's head, above its used-ledger."""
    with open(card_path, encoding="utf-8") as f:
        text = f.read()
    head, sep, tail = text.partition("\n## used")
    lines = head.rstrip("\n").splitlines()
    lines = [l for l in lines if not l.startswith(name + ":")]
    lines.append("%s: %s" % (name, value))
    with open(card_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n" + sep + tail)


def _card_field(card_path, name):
    with open(card_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith(name + ":"):
                return line.split(":", 1)[1].strip()
    return None


def strip_tree(root):
    """rewrite every home path in an exported tree. Returns (count, [files]).

    Only text answers; a file that will not read as text is left alone and is
    already named `unscannable` by the scan the caller reads.
    """
    total, touched = 0, []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in clean.SKIP_DIRS]
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                continue
            fixed, n = clean.strip_home(text)
            if n:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(fixed)
                total += n
                touched.append(os.path.relpath(path, root))
    return total, touched


def sign_card(card_path):
    """sign one staged card with the shelf's own key. Returns (ok, line)."""
    sec = os.environ.get(SECKEY_ENV, "").strip()
    # surface: 3a
    if not sec:
        return False, ("no shelf key is set — point %s at its own key, or "
                       "share unsigned" % SECKEY_ENV)
    if _same_path(sec, CORE_KEY):
        return False, ("%s signs this core — the shelf takes a second key, "
                       "so a leak stops there" % SECKEY_ENV)
    if shutil.which("minisign") is None:
        return False, ("minisign is not installed here — install it, or share "
                       "this build unsigned")
    pub = _pubkey_for(sec)
    if not pub:
        return False, ("i could not read that key's public half — set %s to "
                       "its .pub file" % PUBKEY_ENV)
    # the key rides in the card, so the card is stamped before it is signed.
    _add_field(card_path, "signed-by", pub)
    r = subprocess.run(["minisign", "-Sm", card_path, "-s", os.path.expanduser(sec)],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        return False, ("minisign would not sign the card — check the key, or "
                       "share this build unsigned")
    # surface: 7
    return True, ("signed: minisign, key %s… — the friend needs that key to "
                  "check it" % pub[:12])


def share(ws, build_name, staging_root, sign=False):
    """strip, stage, and refuse only what stripping cannot fix. (ok, message)."""
    c = shelf.card(ws, build_name)
    # surface: 3a
    if c is None:
        return False, "no build named %s on the shelf" % build_name
    src_dir = os.path.join(ws, shelf.DIRNAME, build_name)
    dest = os.path.join(staging_root, "builds", build_name)
    if os.path.exists(dest) and os.listdir(dest):
        # surface: 3a
        return False, ("something is already staged at that path — move it, "
                       "and share again onto empty ground")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    clean.fresh_export(src_dir, dest)
    stripped, touched = strip_tree(dest)
    card_path = os.path.join(dest, "BUILD.md")
    if os.path.exists(card_path):
        _add_field(card_path, "from-workshop", shelf.workshop_id(ws))
    report = clean.scan(dest)
    if report["hits"] or report["denied"]:
        shutil.rmtree(dest, ignore_errors=True)
        # surface: 3a
        lines = ["the scrub refused — person data would ship:"]
        for rel, needle in report["hits"]:
            lines.append("  %s (%s)" % (rel, needle))
        for rel in report["denied"]:
            lines.append("  %s (deny-listed — never ships)" % rel)
        return False, "\n".join(lines)

    # surface: 7
    lines = ["staged for the shelf: %s" % clean.strip_home(dest)[0]]
    if stripped:
        lines.append("stripped %d home path(s) from %d file(s): %s"
                     % (stripped, len(touched), ", ".join(touched)))
    if not report["terms_loaded"]:
        lines.append("note: no private-terms file — only the floor scrub ran; "
                     "set %s to scan for your own terms" % clean.TERMS_ENV)
    if report["unscannable"]:
        lines.append("unscannable files (your eyes owe them a look before you push):")
        for rel in report["unscannable"]:
            lines.append("  " + rel)
    if sign:
        ok, line = sign_card(card_path)
        if not ok:
            shutil.rmtree(dest, ignore_errors=True)
            return False, line
        lines.append(line)
    lines.append("the push is your hand — nothing left this machine.")
    shelf.write_marketplace(ws)
    desk.mint(ws, {"cls": "build-shared", "origin": "machine", "build": build_name,
                   "triggered": "session", "body": "shared: %s" % build_name,
                   "receipt": card_path})
    return True, "\n".join(lines)


def list_source(source):
    """cards available in a shelf-shaped source directory."""
    base = os.path.join(source, "builds")
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "BUILD.md")
        if os.path.exists(p):
            out.append(name)
    return out


def trust_line(card_path, expect_key=None):
    """the one line a person decides on. Returns (ok, line).

    A hash proves the card matches its own bytes; only a key proves a hand,
    and only a key the reader already held proves whose. Each of those three
    states gets its own sentence, and none of them borrows another's.
    """
    expect = (expect_key or os.environ.get(PUBKEY_ENV, "")).strip()
    sig = card_path + SIG_SUFFIX
    key = _card_field(card_path, "signed-by")
    # surface: 26
    if not os.path.exists(sig) or not key:
        return True, ("source: UNVERIFIED — no signature on this card. you are "
                      "trusting the shelf you fetched from, not a key. it still "
                      "lands on your k.")
    if expect:
        want = _read_key(expect) or expect
        if key != want and not key.startswith(want):
            return False, ("the signature does not match the key you expected "
                           "— nothing fetched")
    if shutil.which("minisign") is None:
        return False, ("this card is signed and minisign is not installed here, "
                       "so nothing can check it — install it first")
    r = subprocess.run(["minisign", "-Vm", card_path, "-P", key, "-q"],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        return False, ("the signature does not hold — nothing fetched. ask them "
                       "to re-share, or fetch it unsigned knowing what that means.")
    if expect:
        return True, ("source: signed by %s… — matches the key you expected"
                      % key[:12])
    return True, ("source: signed by %s… — no key expected, so i checked only "
                  "that the signature holds" % key[:12])


def fetch(ws, source, name, consent, expect_key=None):
    """pull one build. Hash, then signature, then the face, then the key."""
    src_dir = os.path.join(source, "builds", name)
    card_path = os.path.join(src_dir, "BUILD.md")
    # surface: 3a
    if not os.path.exists(card_path):
        return False, "no build named %s at %s" % (name, source)
    payload_dir, pinned, why = shelf.verify_entry(source, name)
    if not pinned:
        return False, why
    ok, trust = trust_line(card_path, expect_key)
    if not ok:
        return False, trust
    # surface: 3b
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        return False, ("%s\nhash checks out. fetching needs your %r at a real "
                       "terminal." % (trust, gate.COMMIT_KEY))
    dest = os.path.join(ws, shelf.DIRNAME, name)
    # surface: 3a
    if os.path.exists(dest):
        return False, "a build named %s is already on your shelf" % name
    shutil.copytree(src_dir, dest)
    # The card's origin becomes external here — provenance never launders.
    cpath = os.path.join(dest, "BUILD.md")
    with open(cpath, encoding="utf-8") as f:
        text = f.read()
    if "origin:" in text:
        text = "\n".join(("origin: external" if l.startswith("origin:") else l)
                         for l in text.splitlines()) + "\n"
    else:
        text += "origin: external\n"
    with open(cpath, "w", encoding="utf-8") as f:
        f.write(text)
    _add_field(cpath, "fetched-from", clean.strip_home(source)[0])
    shelf.write_marketplace(ws)
    event = {"cls": "build-kept", "origin": "external", "build": name,
             "body": "fetched: %s (%s)" % (name, "signed" if "signed by" in trust
                                           else "no signature"),
             "receipt": cpath}
    desk.mint(ws, event, consent)
    # surface: 2
    return True, "%s\nfetched %s — on your shelf, origin: external" % (trust, name)
