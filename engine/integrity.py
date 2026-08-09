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

DIRS = ("engine", "vessel", "law", "docs", "soul")
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


def _release_key():
    """The signing key the notes must carry: the env's word, else the
    README's. Two copies that must agree is the anti-tamper story."""
    key = os.environ.get(PUBKEY_ENV, "").strip()
    if key:
        return key
    import re
    readme = os.path.join(root(), "README.md")
    if os.path.exists(readme):
        m = re.search(r"\b(RWS[A-Za-z0-9+/=]{20,})", open(readme, encoding="utf-8").read())
        if m:
            return m.group(1)
    return None


def _changelog_section(version):
    """(tagline, body) for this version's CHANGELOG entry, or (None, None).
    The heading shape is `## <version> — <tagline> (<date>)`."""
    p = os.path.join(root(), "CHANGELOG.md")
    if not os.path.exists(p):
        return None, None
    tagline, body, inside = None, [], False
    for line in open(p, encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            if inside:
                break
            head = line[3:]
            if head.startswith(version + " ") and "—" in head:
                tagline = head.split("—", 1)[1].rsplit("(", 1)[0].strip()
                inside = True
            continue
        if inside:
            body.append(line)
    return tagline, "\n".join(body).strip() if body else None


def release_notes(version):
    """Write this release's notes where nothing seals them: the CHANGELOG
    section plus the key line, so the README's cross-check ('the same key is
    printed in every release's notes') is true by construction. Returns
    (path, tagline) or (None, why)."""
    tagline, body = _changelog_section(version)
    if not tagline or not body:
        return None, "CHANGELOG.md has no section for %s" % version
    key = _release_key()
    if not key:
        return None, "no signing key found — set %s or keep it in README.md" % PUBKEY_ENV
    import tempfile
    p = os.path.join(tempfile.gettempdir(), "sandbox-release-notes-v%s.md" % version)
    with open(p, "w", encoding="utf-8") as f:
        f.write("Sandbox OS %s — %s\n\n%s\n\nrelease public key: %s\n"
                % (version, tagline, body, key))
    return p, tagline


def release_check():
    """The release drill's wall: refuses until everything a release needs
    actually holds. Born from a recurrence — two releases pushed with the
    fresh signature uncommitted, caught only by a stranger-path verify.
    This verb never tags, never pushes and never publishes; those are the
    owner's hands. It just refuses to let the ceremony start out of order.
    """
    import sys
    r = root()
    lines, ok = [], True

    suite = subprocess.run([sys.executable, "-m", "unittest", "discover",
                            "-s", "engine/tests", "-t", "."],
                           cwd=r, capture_output=True, text=True, timeout=600)
    good = suite.returncode == 0
    ok = ok and good
    tail = (suite.stderr or "").strip().splitlines()
    lines.append("%s the suite (%s)" % ("ok  " if good else "FAIL",
                                        tail[-1] if tail else ""))

    v_ok, v_msg = verify()
    ok = ok and v_ok
    lines.append("%s verify: %s" % ("ok  " if v_ok else "FAIL", v_msg.splitlines()[0]))

    mp, sig = manifest_path(), manifest_path() + ".minisig"
    if not os.path.exists(sig):
        ok = False
        lines.append("FAIL no signature — sign the manifest: minisign -Sm manifest.json"
                     " — then COMMIT the signature before tagging")
    elif os.path.getmtime(sig) < os.path.getmtime(mp):
        ok = False
        lines.append("FAIL the signature is OLDER than the manifest — re-sign before anything ships")
    else:
        lines.append("ok   the signature is fresher than the manifest")

    st = subprocess.run(["git", "-C", r, "status", "--porcelain"],
                        capture_output=True, text=True)
    clean = st.returncode == 0 and not st.stdout.strip()
    ok = ok and clean
    lines.append("%s the tree is committed%s" % ("ok  " if clean else "FAIL",
                 "" if clean else " — uncommitted: " + st.stdout.strip().replace("\n", ", ")[:120]))

    with open(os.path.join(r, "VERSION"), encoding="utf-8") as f:
        v = f.read().strip()
    notes_path, tagline = release_notes(v)  # tagline is the refusal's why when None
    notes_ok = notes_path is not None
    ok = ok and notes_ok
    lines.append("%s the notes carry the key%s" % ("ok  " if notes_ok else "FAIL",
                 "" if notes_ok else " — " + tagline))

    if ok:
        lines.append("the ceremony is five moves — this wall verified 1 and 2; 3 to 5 are your hands:")
        lines.append("  1. sign      minisign -Sm manifest.json            (done — fresher than the manifest)")
        lines.append("  2. commit    the signature is IN the committed tree (done — the tree is clean)")
        lines.append("  3. tag       git tag -a v%s -m \"%s\"" % (v, tagline))
        lines.append("  4. push      git push origin main --tags")
        lines.append("  5. publish   gh release create v%s --title \"Sandbox OS %s — %s\" --notes-file %s"
                     % (v, v, tagline, notes_path))
        lines.append("re-sign for any reason after this wall, and moves 2-5 start over —")
        lines.append("a tag must never point at a tree whose signature came later.")
        lines.append("a tag without its published notes leaves the key's cross-check unbacked —")
        lines.append("the ceremony ends at the Releases page, not at the push.")
        if shutil.which("gh") is None:
            lines.append("(gh is not installed here — publish from any machine that has it)")
    else:
        lines.append("the release refuses — fix the FAIL lines first.")
    return ok, "\n".join(lines)


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
