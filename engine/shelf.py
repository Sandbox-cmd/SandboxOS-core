# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the shelf: saved builds — real files, real provenance, no store.

`save` presses a build: a card (BUILD.md) plus exactly one payload (a file
or a directory), hashed. `use` copies the payload onto a project and writes
one line in the card's used-ledger. A card with more or fewer than one
payload is torn, and use refuses it. Origin says whose hand pressed it and
never launders: session-kept (the machine), external (fetched from someone
else's shelf), and owner-kept — which waits for S1, because only a key on a
build earns it and no terminal check ever proved a hand.

Both moves leave a trace: a press and a use each land one event whose
receipt is the card, so the record and the shelf can be asked the same
question and be made to agree.
"""
import hashlib
import json
import os
import shutil

from . import desk, journal

DIRNAME = "shelf"
MARKET_DIR = ".claude-plugin"
MARKET_FILE = "marketplace.json"
ID_FILE = "workshop-id"

# what a friend's confirmation looks like when the owner stages it: there is
# no network here and no reading someone else's record, so the first pull is
# witnessed by a person and the note says so in its first word (J20).
WITNESS = "pull-witnessed:"


def _dir(ws, name=None):
    base = os.path.join(ws, DIRNAME)
    return os.path.join(base, name) if name else base


def dirpath(ws, name=None):
    """the shelf's directory — the one line `sandbox shelf-dir` prints."""
    return _dir(ws, name)


def workshop_id(ws):
    """this workshop's own short name for itself, minted once and then kept.

    a card used to answer "whose workshop" with the owner's home path, which
    is the one thing a build that travels must not carry (law 13). twelve hex
    characters mean nothing off this machine and stay the same on it. it is
    written on first need — a save or a share — rather than at init, so a
    workshop that predates this line still gets one the first time it matters.
    """
    p = os.path.join(ws, journal.STATE_DIR, ID_FILE)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            got = f.read().strip()
        if got:
            return got
    got = os.urandom(6).hex()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(got + "\n")
    return got


def from_line(ws, src):
    """what a card may say about where a build came from.

    inside the workshop it is the path relative to it; outside, the file's own
    name and nothing else. an absolute path never enters the shelf, so nothing
    downstream has to strip one later (inventory finding 4, at its root).
    """
    rel = os.path.relpath(src, os.path.abspath(ws))
    if rel.split(os.sep)[0] == "..":
        return "outside the workshop (%s)" % os.path.basename(src.rstrip(os.sep))
    return rel.replace(os.sep, "/")


def payload_hash(path):
    """one file → its sha256. A directory → sha256 over sorted (rel, sha) pairs."""
    if os.path.isfile(path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    pairs = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for n in sorted(filenames):
            p = os.path.join(dirpath, n)
            with open(p, "rb") as f:
                pairs.append("%s %s" % (os.path.relpath(p, path),
                                        hashlib.sha256(f.read()).hexdigest()))
    return hashlib.sha256("\n".join(sorted(pairs)).encode()).hexdigest()


def save(ws, src, name=None, note="", origin=None):
    """press a build onto the shelf."""
    src = os.path.abspath(os.path.expanduser(src))
    if not os.path.exists(src):
        return False, "nothing at %s to save" % src
    name = name or os.path.basename(src.rstrip(os.sep))
    d = _dir(ws, name)
    if os.path.exists(d):
        # surface: 3a
        return False, "a build named %s is already on the shelf" % name
    os.makedirs(d)
    dest = os.path.join(d, os.path.basename(src.rstrip(os.sep)))
    if os.path.isdir(src):
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    else:
        shutil.copy2(src, dest)
    if origin is None:
        # `save` never reads the terminal to decide this. A file descriptor is
        # not a hand: under a pty rig `sys.stdin.isatty()` said owner-kept for
        # a build no owner touched, and at a real terminal it said it for a
        # build the session pressed. Until a key lands a build (S1), every
        # press the engine makes is session-kept and says so.
        origin = "session-kept"
    sha = payload_hash(dest)
    with open(os.path.join(d, "BUILD.md"), "w", encoding="utf-8") as f:
        f.write("# %s\nkept: %s\nfrom: %s\nsha256: %s\norigin: %s\n" %
                (name, journal.now(), from_line(ws, src), sha, origin))
        if note:
            f.write("note: %s\n" % note)
        f.write("\n## used\n%s\n" % USED_HINT)
    workshop_id(ws)
    write_marketplace(ws)
    desk.mint(ws, {"cls": "build-kept", "origin": "machine", "build": name,
                   "triggered": "session", "body": "kept: %s" % name,
                   "receipt": os.path.join(d, "BUILD.md")})
    # surface: 2
    return True, "kept: %s (%s) — reuse it with: sandbox use %s" % (name, origin, name)


def card(ws, name):
    p = os.path.join(_dir(ws, name), "BUILD.md")
    if not os.path.exists(p):
        return None
    out = {"name": name}
    with open(p, encoding="utf-8") as f:
        for line in f:
            for field in ("kept", "from-workshop", "from", "sha256", "origin",
                          "note", "signed-by", "fetched-from"):
                if line.startswith(field + ":"):
                    out[field] = line.split(":", 1)[1].strip()
    return out


CARD = "BUILD.md"

# the line an empty `## used` section carries, so it explains itself: a
# card's travel log is written by the tool and by nobody's hand, and a
# blank heading reads as a section someone forgot to fill in.
# surface: 9
USED_HINT = "(each sandbox use appends a line here)"


def _not_card(entry):
    """the card and the signature beside it are the card's own two files;
    everything else in a build directory is the payload."""
    return not entry.startswith(CARD) and not entry.startswith(".")


def _payload_of(ws, name):
    d = _dir(ws, name)
    return [e for e in os.listdir(d) if _not_card(e)]


def payload_in(build_dir):
    """the one payload beside a card, wherever the card is sitting.

    a build is a card plus exactly one payload; more or fewer is torn, and
    every reader of a build directory — the shelf's own, a staged one, a
    friend's — asks that question the same way.
    """
    if not os.path.isdir(build_dir):
        return None
    entries = [e for e in os.listdir(build_dir) if _not_card(e)]
    return os.path.join(build_dir, entries[0]) if len(entries) == 1 else None


def list_all(ws):
    base = _dir(ws)
    if not os.path.isdir(base):
        return []
    return [card(ws, n) for n in sorted(os.listdir(base))
            if card(ws, n) is not None]


def door_of(c):
    """which door a build came in by, in a person's words."""
    # surface: 1
    if (c.get("origin") or "") == "external":
        return "fetched from %s" % (c.get("fetched-from") or "someone else's shelf")
    return "kept here"


# --- the shelf as a marketplace the host already reads ---------------------

def marketplace_path(ws):
    return os.path.join(_dir(ws), MARKET_DIR, MARKET_FILE)


def offers_marketplace(ws):
    """true when this shelf is already shaped for a friend's host to add."""
    return os.path.exists(marketplace_path(ws))


def entry_for(c):
    """one card as the host reads it: a plugin-shaped entry, pinned by the
    same hash the card already carries, pointing at the build's directory."""
    # surface: 16
    return {"name": "build-%s" % c["name"],
            "source": "./%s" % c["name"],
            "description": c.get("note") or "a build kept on this shelf",
            "version": (c.get("kept") or "").split("T")[0] or "0.0.0",
            "sha256": c.get("sha256") or ""}


def marketplace(ws):
    """the whole file, regenerated from the cards — never hand-edited.

    the host does its own pinning from this; nothing here re-implements the
    reader. the owner is named by the workshop id, so a shelf a stranger adds
    says which workshop it is without saying whose.
    """
    who = workshop_id(ws)
    return {"name": "shelf-%s" % who,
            "owner": {"name": "shelf-%s" % who},
            "plugins": [entry_for(c) for c in list_all(ws)]}


def write_marketplace(ws):
    """write the marketplace file and the page beside it. returns the path."""
    base = _dir(ws)
    if not os.path.isdir(base):
        return None
    d = os.path.join(base, MARKET_DIR)
    os.makedirs(d, exist_ok=True)
    p = marketplace_path(ws)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(marketplace(ws), f, indent=1, ensure_ascii=False)
        f.write("\n")
    _write_readme(ws)
    return p


def _write_readme(ws):
    """the shelf's own short page: what the host will list, by name."""
    # surface: 17
    lines = ["# the shelf", "",
             "a friend adds this shelf with one line:", "",
             '    claude plugin marketplace add "$(sandbox shelf-dir)"', "",
             "what the host lists, once it is added:", ""]
    cards = list_all(ws)
    for c in cards:
        lines.append("- `build-%s` — %s" % (c["name"], c.get("note") or "no note yet"))
    if not cards:
        lines.append("- nothing yet; keep one with: sandbox save PATH")
    lines += ["",
              "landing one on your own shelf is still sandbox fetch — that is the "
              "door that records it.",
              "",
              "*generated by save, share and fetch — edits here are overwritten.*",
              ""]
    p = os.path.join(_dir(ws), "README.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return p


def verify_entry(source, name):
    """the pin check, for a build as for an app. returns (path, ok, line).

    one function for every door: a shelf's card, a shelf's marketplace entry,
    and an app index all pin the same hash the same way, so the reader that
    used to live beside the index is here instead of anywhere else.
    """
    build_dir = os.path.join(source, "builds", name)
    card_path = os.path.join(build_dir, "BUILD.md")
    if os.path.exists(card_path):
        want = _field(card_path, "sha256")
        payload = payload_in(build_dir)
        if payload is None:
            # surface: 3a
            return build_dir, False, ("the card at the source is torn — a build "
                                      "is one card and one payload")
        ok, line = _pinned(payload_hash(payload), want, name, source)
        return build_dir, ok, line

    market = os.path.join(source, MARKET_DIR, MARKET_FILE)
    if os.path.exists(market):
        with open(market, encoding="utf-8") as f:
            listed = json.load(f)
        for e in listed.get("plugins") or []:
            if e.get("name") != "build-%s" % name:
                continue
            rel = (e.get("source") or "./%s" % name)
            d = os.path.join(source, rel[2:] if rel.startswith("./") else rel)
            payload = payload_in(d)
            if payload is None:
                # surface: 3a
                return d, False, ("the entry names %r and the shelf does not "
                                  "carry it whole" % name)
            ok, line = _pinned(payload_hash(payload), e.get("sha256"), name, source)
            return d, ok, line

    index = os.path.join(source, "index.json")
    if os.path.exists(index):
        with open(index, encoding="utf-8") as f:
            listed = json.load(f)
        entry = (listed.get("apps") or {}).get(name)
        if entry is None:
            # surface: 3a
            return None, False, "the source at %s does not list %r" % (source, name)
        d = os.path.join(source, entry.get("path", os.path.join("apps", name)))
        if not os.path.isdir(d):
            # surface: 3a
            return None, False, ("the index lists %r and the directory beside "
                                 "it is missing" % name)
        ok, line = _pinned(payload_hash(d), entry.get("sha256"), name, source)
        return d, ok, line
    # surface: 3a
    return None, False, "nothing at %s lists %r to check" % (source, name)


def _pinned(actual, want, name, source):
    """the two answers a pin can give, said the same way for every door."""
    # surface: 26
    if actual != (want or ""):
        return False, ("the bytes at %s disagree with its own pin for %r "
                       "(%s… vs %s…) — trust neither, tell whoever keeps it"
                       % (source, name, actual[:12], (want or "")[:12]))
    return True, "pinned by the source's own index"


def _field(card_path, name):
    with open(card_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith(name + ":"):
                return line.split(":", 1)[1].strip()
    return None


def first_pull(ws):
    """what the record knows about a build landing on someone else's machine.

    it reads this workshop's own shares and the note the owner stages when a
    friend tells them. it cannot read the friend's record and does not
    pretend to: the confirmation is a human one, named as one (J20).
    """
    events, _ = journal.read(ws)
    shared, witnessed = [], []
    for e in events:
        if e.get("op") == "assert" and e.get("cls") == "build-shared":
            shared.append(e.get("build"))
        body = (e.get("body") or "").strip()
        if body.startswith(WITNESS):
            witnessed.append(body)
    return {"shared": shared, "witnessed": witnessed}


def write_used(ws, name, rows):
    """rewrite one card's used-ledger. True when the file moved.

    The header and the fields above `## used` are the press's own writing and
    are left exactly as they are: what a rebuild owns is the travel log, and
    the record is where that log comes from.
    """
    p = os.path.join(_dir(ws, name), "BUILD.md")
    if not os.path.exists(p):
        return False
    with open(p, encoding="utf-8") as f:
        head = f.read().split("\n## used", 1)[0]
    body = "".join(r.rstrip() + "\n" for r in rows) or USED_HINT + "\n"
    text = head + "\n## used\n" + body
    with open(p, encoding="utf-8") as f:
        if f.read() == text:
            return False
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def use(ws, name, project_name, project_root):
    """copy the payload onto a project; the card remembers where it went."""
    c = card(ws, name)
    if c is None:
        return False, "no build named %s on the shelf" % name
    entries = _payload_of(ws, name)
    if len(entries) != 1:
        return False, ("the card for %s is torn — expected exactly one payload, found %d"
                       % (name, len(entries)))
    src = os.path.join(_dir(ws, name), entries[0])
    if payload_hash(src) != c.get("sha256"):
        return False, ("%s no longer matches its card — i refuse to spread a "
                       "build that drifted" % name)
    dest = os.path.join(project_root, entries[0])
    if os.path.exists(dest):
        return False, "%s already exists on %s — nothing overwritten" % (entries[0], project_name)
    if os.path.isdir(src):
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    card_path = os.path.join(_dir(ws, name), "BUILD.md")
    with open(card_path, "a", encoding="utf-8") as f:
        f.write("used on %s %s\n" % (project_name, journal.now()))
    # the card remembered where a build went and the record learned nothing;
    # a build that travels is a thing that happened, so it lands as an event
    # with the card as its receipt (J19).
    desk.mint(ws, {"cls": "build-used", "origin": "machine", "build": name,
                   "triggered": "session", "project": project_name,
                   "body": "used: %s on %s" % (name, project_name),
                   "receipt": card_path})
    return True, "loaded %s onto %s" % (name, project_name)
