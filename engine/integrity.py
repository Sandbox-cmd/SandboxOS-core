# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""seal and verify this copy of the core. Tamper-evident, not tamper-proof —
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
import re
import shutil
import subprocess

DIRS = ("engine", "vessel", "law", "docs", "soul")
FILES = ("sandbox", "boot.py", "README.md", "LICENSE", "VERSION", "CHANGELOG.md")
SKIP_DIRS = {"__pycache__"}
PUBKEY_ENV = "SANDBOX_MINISIGN_PUBKEY"


def root():
    """where this copy lives. One home (ruled 2026-07-23, 2026-08-22): the
    guard, the shim and every receipt path resolve against this, never
    against a pointer file written at init."""
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
    """the signing key the notes must carry: the env's word, else the
    README's. Two copies that must agree is the anti-tamper story."""
    key = os.environ.get(PUBKEY_ENV, "").strip()
    if key:
        return key
    import re
    readme = os.path.join(root(), "README.md")
    if os.path.exists(readme):
        with open(readme, encoding="utf-8") as f:
            m = re.search(r"\b(RWS[A-Za-z0-9+/=]{20,})", f.read())
        if m:
            return m.group(1)
    return None


RELEASE_TRAILER = re.compile(r"^Release-Of:\s*v\d+\.\d+\.\d+\s*$", re.M)


def commit_message(said):
    """the message the wall reads: the file `said` names, or `said` itself.

    git hands its hook a path; a person testing the same verb hands it the
    words. One reader takes both, so the hook and the hand meet the same
    trailer check.
    """
    try:
        with open(said, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return said


def is_release_commit(msg):
    """true when this commit message carries the release trailer.

    one reader, and the shipped hook shells this verb rather than carrying a
    second copy of the shape: two patterns that must agree is how the hook
    became noise the last time (scars 3).
    """
    return bool(RELEASE_TRAILER.search(msg or ""))


def _last_tag(r):
    """the newest tag reachable from main, or None on a tree with no tag."""
    out = subprocess.run(["git", "-C", r, "describe", "--tags", "--abbrev=0", "main"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def work_commits(r, tag):
    """[(sha, subject)] for every commit on main since `tag` that no release
    made — the evidence the main row names."""
    rng = ("%s..main" % tag) if tag else "main"
    out = subprocess.run(["git", "-C", r, "log", "--reverse",
                          "--format=%H%x1f%s%x1f%B%x1e", rng],
                         capture_output=True, text=True)
    if out.returncode != 0:
        return []
    found = []
    for chunk in out.stdout.split("\x1e"):
        if not chunk.strip():
            continue
        parts = chunk.strip("\n").split("\x1f")
        sha, subject = parts[0], parts[1] if len(parts) > 1 else ""
        msg = parts[2] if len(parts) > 2 else ""
        if not is_release_commit(msg):
            found.append((sha, subject))
    return found


def signature_holds(path=None, key=None):
    """true when the signature verifies over the file's CURRENT bytes, false
    when it does not, None when nothing here can tell.

    git writes checkout-order mtimes, so comparing the two timestamps was a
    coin flip on any fresh clone. content answers the question the clock only
    seemed to.
    """
    path = path or manifest_path()
    key = key or _release_key()
    if key is None or shutil.which("minisign") is None:
        return None
    r = subprocess.run(["minisign", "-Vm", path, "-P", key],
                       capture_output=True, text=True)
    return r.returncode == 0


def hook_source():
    """the commit-msg hook this core ships, sealed with the rest of the tree."""
    return os.path.join(root(), "vessel", "git", "commit-msg")


def place_hook(tree=None):
    """copy the shipped hook into this tree's own hooks, on the owner's word.

    it is a flag on the verb and never a step of it: a file that appears in
    someone's `.git` without them asking is the kind of surprise this system
    is against.
    """
    src = hook_source()
    if not os.path.exists(src):
        # surface: 3a
        return False, "this core ships no git hook to place"
    hooks = os.path.join(tree or root(), ".git", "hooks")
    if not os.path.isdir(hooks):
        # surface: 3a
        return False, "no .git/hooks here — run this from the tree you develop in"
    dest = os.path.join(hooks, "commit-msg")
    shutil.copyfile(src, dest)
    os.chmod(dest, 0o755)
    # surface: 2
    return True, ("i placed the commit-msg hook at %s — it asks this verb "
                  "before any commit on main" % dest)


def _changelog_section(version):
    """(tagline, body) for this version's CHANGELOG entry, or (None, None).
    The heading shape is `## <version> — <tagline> (<date>)`."""
    p = os.path.join(root(), "CHANGELOG.md")
    if not os.path.exists(p):
        return None, None
    tagline, body, inside = None, [], False
    with open(p, encoding="utf-8") as f:
        section = f.read().splitlines()
    for line in section:
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
    """write this release's notes where nothing seals them: the CHANGELOG
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


def main_row(r):
    """the row that keeps main verifiable: every commit since the last tag is
    one a release made, or the release stops and names the first that is not.

    a hook can be skipped, so the same fact is re-derived here from the log —
    law 10's split, where the hook is the fast answer and this is the one that
    holds.
    """
    tag = _last_tag(r)
    if tag is None:
        # surface: 13
        return True, "ok   no tag yet — every commit on main is this release's first"
    work = work_commits(r, tag)
    if not work:
        # surface: 13
        return True, "ok   main holds only release commits since %s" % tag
    # surface: 13
    return False, ("FAIL main holds %d work commit(s) since %s — the first is %s %s\n"
                   "     work belongs on a branch: git switch -c <name>, then start again"
                   % (len(work), tag, work[0][0][:7], work[0][1]))


def signature_row(mp=None):
    """the row that reads the signature against the manifest's CURRENT bytes.

    it replaces a comparison of the two mtimes, which git writes in checkout
    order: on a fresh clone that test answered by luck.
    """
    mp = mp or manifest_path()
    if not os.path.exists(mp + ".minisig"):
        # surface: 13
        return False, ("FAIL no signature — sign the manifest: minisign -Sm manifest.json"
                       " — then commit the signature before tagging")
    held = signature_holds(mp)
    if held is None:
        # surface: 13
        return False, ("FAIL the signature stays unread here — install minisign, or put "
                       "the key in %s or README.md" % PUBKEY_ENV)
    if not held:
        # surface: 13
        return False, ("FAIL the signature does not hold over this manifest — re-sign: "
                       "minisign -Sm manifest.json, then commit it")
    with open(mp, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    # surface: 13
    return True, ("ok   the signature holds over these exact manifest bytes (sha256 %s…)"
                  % digest[:8])


def ceremony(version, tagline, notes_path, gh=True):
    """the five moves, and which two this verb already ran.

    It is a block of instructions to the owner's hands, so it says "i" only
    where it made a move itself — and moves 3 to 5 are the owner's, which is
    why they carry no claim at all. Its own function so the block can be read
    and pinned without a release drill running first.
    """
    # surface: 13
    lines = [
        "the release is clear on my side — moves 1 and 2 held; 3 to 5 are yours:",
        "  1. sign      minisign -Sm manifest.json     done: it holds over these bytes",
        "  2. commit    the signature is in the tree   done: the tree is clean",
        "               that commit's message carries the trailer:  Release-Of: v%s" % version,
        "  3. tag       git tag -a v%s -m \"%s\"" % (version, tagline),
        "  4. push      git push origin main --tags",
        "  5. publish   gh release create v%s --title \"Sandbox OS %s — %s\" --notes-file %s"
        % (version, version, tagline, notes_path),
        "re-sign after this point and moves 2 to 5 start over: a tag points at one",
        "tree, and its signature has to be older than the tag. publish is the last",
        "move because the key's cross-check lives on the Releases page, not in the push.",
    ]
    if not gh:
        lines.append("(gh is not installed here — publish from any machine that has it)")
    return lines


def release_check():
    """the release drill's wall: refuses until everything a release needs
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

    good, row = main_row(r)
    ok = ok and good
    lines.append(row)

    good, row = signature_row()
    ok = ok and good
    lines.append(row)

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
        lines.extend(ceremony(v, tagline, notes_path,
                              gh=shutil.which("gh") is not None))
    else:
        # surface: 13
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
