# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The shelf: saved builds — real files, real provenance, no store.

`save` presses a build: a card (BUILD.md) plus exactly one payload (a file
or a directory), hashed. `use` copies the payload onto a project and writes
one line in the card's used-ledger. A card with more or fewer than one
payload is torn, and use refuses it. Origin says whose hand pressed it and
never launders: owner-kept (a real terminal), session-kept (the machine),
external (fetched from someone else's shelf).
"""
import hashlib
import os
import shutil
import sys

from . import gate, journal

DIRNAME = "shelf"


def _dir(ws, name=None):
    base = os.path.join(ws, DIRNAME)
    return os.path.join(base, name) if name else base


def payload_hash(path):
    """One file → its sha256. A directory → sha256 over sorted (rel, sha) pairs."""
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
    """Press a build onto the shelf."""
    src = os.path.abspath(os.path.expanduser(src))
    if not os.path.exists(src):
        return False, "nothing at %s to save" % src
    name = name or os.path.basename(src.rstrip(os.sep))
    d = _dir(ws, name)
    if os.path.exists(d):
        return False, "a build named %s is already on the shelf" % name
    os.makedirs(d)
    dest = os.path.join(d, os.path.basename(src.rstrip(os.sep)))
    if os.path.isdir(src):
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    else:
        shutil.copy2(src, dest)
    if origin is None:
        origin = "owner-kept" if (sys.stdin.isatty() and not gate.synthetic()) else "session-kept"
    sha = payload_hash(dest)
    with open(os.path.join(d, "BUILD.md"), "w", encoding="utf-8") as f:
        f.write("# %s\nkept: %s\nfrom: %s\nsha256: %s\norigin: %s\n" %
                (name, journal.now(), src, sha, origin))
        if note:
            f.write("note: %s\n" % note)
        f.write("\n## used\n")
    journal.append(ws, {"op": "assert", "cls": "build-kept", "origin": "machine",
                        "triggered": "session", "body": "kept: %s" % name,
                        "ink": "receipted", "receipt": os.path.join(d, "BUILD.md")})
    return True, "kept: %s (%s) — reuse it with: sandbox use %s" % (name, origin, name)


def card(ws, name):
    p = os.path.join(_dir(ws, name), "BUILD.md")
    if not os.path.exists(p):
        return None
    out = {"name": name}
    for line in open(p, encoding="utf-8"):
        for field in ("kept", "from", "sha256", "origin", "note"):
            if line.startswith(field + ":"):
                out[field] = line.split(":", 1)[1].strip()
    return out


def _payload_of(ws, name):
    d = _dir(ws, name)
    entries = [e for e in os.listdir(d) if e != "BUILD.md" and not e.startswith(".")]
    return entries


def list_all(ws):
    base = _dir(ws)
    if not os.path.isdir(base):
        return []
    return [card(ws, n) for n in sorted(os.listdir(base))
            if card(ws, n) is not None]


def use(ws, name, project_name, project_root):
    """Copy the payload onto a project; the card remembers where it went."""
    c = card(ws, name)
    if c is None:
        return False, "no build named %s on the shelf" % name
    entries = _payload_of(ws, name)
    if len(entries) != 1:
        return False, ("the card for %s is torn — expected exactly one payload, found %d"
                       % (name, len(entries)))
    src = os.path.join(_dir(ws, name), entries[0])
    if payload_hash(src) != c.get("sha256"):
        return False, ("the payload for %s no longer matches its card — refusing "
                       "to spread a build that drifted" % name)
    dest = os.path.join(project_root, entries[0])
    if os.path.exists(dest):
        return False, "%s already exists on %s — nothing overwritten" % (entries[0], project_name)
    if os.path.isdir(src):
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    with open(os.path.join(_dir(ws, name), "BUILD.md"), "a", encoding="utf-8") as f:
        f.write("used on %s %s\n" % (project_name, journal.now()))
    return True, "loaded %s onto %s" % (name, project_name)
