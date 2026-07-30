# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Seal and verify this copy of the core. Tamper-evident, not tamper-proof —
and it says so.

The manifest hashes the shipped tree. `verify` proves the copy CHANGED,
never WHO changed it. With SANDBOX_MINISIGN_PUBKEY set it turns strict: a
missing minisign, a missing signature, or a bad signature REFUSES before
any hashing — no default key, no fallback, no signature theater. It seals
the core, never the workshop.
"""
import hashlib
import json
import os
import shutil
import subprocess

DIRS = ("engine", "vessel", "law", "docs")
FILES = ("sandbox", "boot.py", "README.md", "LICENSE", "VERSION", "CHANGELOG.md")
SKIP_DIRS = {"__pycache__"}
PUBKEY_ENV = "SANDBOX_MINISIGN_PUBKEY"


def root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def manifest_path():
    return os.path.join(root(), "manifest.json")


def _walk():
    r = root()
    for d in DIRS:
        base = os.path.join(r, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
            for n in filenames:
                if n.endswith(".minisig"):
                    continue
                yield os.path.relpath(os.path.join(dirpath, n), r)
    for f in FILES:
        if os.path.exists(os.path.join(r, f)):
            yield f


def _sha(rel):
    with open(os.path.join(root(), rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def seal():
    files = {rel: _sha(rel) for rel in _walk()}
    from time import gmtime, strftime
    with open(manifest_path(), "w", encoding="utf-8") as f:
        json.dump({"generated": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
                   "files": files}, f, indent=1, sort_keys=True)
    lines = ["sealed: %d file(s)" % len(files)]
    if os.environ.get(PUBKEY_ENV):
        lines.append("strict verify is on — a fresh seal needs a fresh signature: "
                     "minisign -Sm manifest.json")
    return True, "\n".join(lines)


def verify():
    mp = manifest_path()
    if not os.path.exists(mp):
        return False, "no manifest — nothing to verify against. seal first."
    pub = os.environ.get(PUBKEY_ENV, "").strip()
    if pub:
        if shutil.which("minisign") is None:
            return False, "strict verify: minisign is not installed — refusing"
        sig = mp + ".minisig"
        if not os.path.exists(sig):
            return False, "strict verify: manifest.json.minisig is missing — refusing"
        r = subprocess.run(["minisign", "-Vm", mp, "-P", pub],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return False, "strict verify: the signature does not hold — refusing"
    with open(mp, encoding="utf-8") as f:
        recorded = json.load(f)["files"]
    current = {rel: _sha(rel) for rel in _walk()}
    changed = sorted(r for r in recorded if r in current and current[r] != recorded[r])
    missing = sorted(r for r in recorded if r not in current)
    new = sorted(r for r in current if r not in recorded)
    if not changed and not missing and not new:
        note = "" if pub else " (tamper-evident, not tamper-proof)"
        return True, "clean — this copy matches its manifest%s" % note
    lines = []
    for r_ in changed:
        lines.append("changed: %s" % r_)
    for r_ in missing:
        lines.append("missing: %s" % r_)
    for r_ in new:
        lines.append("new: %s" % r_)
    return False, "\n".join(lines)
